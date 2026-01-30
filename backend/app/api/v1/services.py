"""Routes API pour les services externes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.core.config import get_settings
from app.services.tracker_service import TrackerService
from app.services.discogs_service import DiscogsService
from app.services.spotify_service import SpotifyService
from app.services.ai_service import AIService
from app.models import Album, Artist, Image, Metadata

router = APIRouter()

# Instance globale du tracker
_tracker_instance = None


def get_tracker():
    """Obtenir l'instance du tracker."""
    global _tracker_instance
    if _tracker_instance is None:
        settings = get_settings()
        _tracker_instance = TrackerService(settings.secrets)
    return _tracker_instance


@router.get("/tracker/status")
async def get_tracker_status():
    """Statut du tracker Last.fm."""
    tracker = get_tracker()
    return tracker.get_status()


@router.post("/tracker/start")
async def start_tracker():
    """Démarrer le tracker Last.fm."""
    tracker = get_tracker()
    await tracker.start()
    return {"status": "started"}


@router.post("/tracker/stop")
async def stop_tracker():
    """Arrêter le tracker Last.fm."""
    tracker = get_tracker()
    await tracker.stop()
    return {"status": "stopped"}


@router.post("/discogs/sync")
async def sync_discogs_collection(
    limit: int = None,
    db: Session = Depends(get_db)
):
    """Synchroniser la collection Discogs.
    
    Args:
        limit: Nombre maximum d'albums à synchroniser (optionnel, pour tests)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🔄 Début synchronisation Discogs")
    settings = get_settings()
    secrets = settings.secrets
    discogs_config = secrets.get('discogs', {})
    spotify_config = secrets.get('spotify', {})
    ai_config = secrets.get('euria', {})
    
    discogs_service = DiscogsService(
        api_key=discogs_config.get('api_key'),
        username=discogs_config.get('username')
    )
    
    # Initialiser les services Spotify et IA
    spotify_service = SpotifyService(
        client_id=spotify_config.get('client_id'),
        client_secret=spotify_config.get('client_secret')
    )
    
    ai_service = AIService(
        url=ai_config.get('url'),
        bearer=ai_config.get('bearer')
    )
    
    try:
        logger.info("📡 Récupération collection Discogs...")
        albums_data = discogs_service.get_collection(limit=limit)
        logger.info(f"✅ {len(albums_data)} albums récupérés de Discogs")
        
        synced_count = 0
        skipped_count = 0
        error_count = 0
        
        for album_data in albums_data:
            try:
                # Vérifier si l'album existe déjà
                existing = db.query(Album).filter_by(
                    discogs_id=str(album_data['release_id'])
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Créer/récupérer artistes (dédoublonner pour éviter UNIQUE constraint)
                artists = []
                seen_artist_ids = set()
                
                for artist_name in album_data['artists']:
                    if not artist_name or not artist_name.strip():
                        continue
                    
                    artist = db.query(Artist).filter_by(name=artist_name).first()
                    if not artist:
                        artist = Artist(name=artist_name)
                        db.add(artist)
                        db.flush()
                    
                    # Éviter les doublons d'artistes (certains albums Discogs ont des duplicatas)
                    if artist.id not in seen_artist_ids:
                        artists.append(artist)
                        seen_artist_ids.add(artist.id)
                
                # Si pas d'artiste, ignorer cet album
                if not artists:
                    logger.warning(f"⚠️ Album sans artiste ignoré: {album_data.get('title', 'Unknown')}")
                    error_count += 1
                    continue
                
                # Déterminer le support
                support = "Unknown"
                if album_data.get('formats'):
                    format_name = album_data['formats'][0]
                    if 'Vinyl' in format_name or 'LP' in format_name:
                        support = "Vinyle"
                    elif 'CD' in format_name:
                        support = "CD"
                    elif 'Digital' in format_name:
                        support = "Digital"
                
                # Normaliser l'année (Discogs peut retourner 0 ou None)
                year = album_data.get('year')
                if year == 0:
                    year = None
                
                # Rechercher URL Spotify
                spotify_url = None
                try:
                    artist_name = album_data['artists'][0] if album_data['artists'] else ""
                    spotify_url = await spotify_service.search_album_url(artist_name, album_data['title'])
                    if spotify_url:
                        logger.info(f"🎵 Spotify trouvé pour: {album_data['title']}")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur recherche Spotify pour {album_data['title']}: {e}")
                
                # Créer album
                album = Album(
                    title=album_data['title'],
                    year=year,
                    support=support,
                    discogs_id=str(album_data['release_id']),
                    discogs_url=album_data.get('discogs_url'),
                    spotify_url=spotify_url
                )
                album.artists = artists
                db.add(album)
                db.flush()
                
                # Ajouter image
                if album_data.get('cover_image'):
                    image = Image(
                        url=album_data['cover_image'],
                        image_type='album',
                        source='discogs',
                        album_id=album.id
                    )
                    db.add(image)
                
                # Générer description IA avec délai pour éviter rate limiting
                ai_info = None
                try:
                    import asyncio
                    # Petit délai pour éviter de saturer l'API EurIA
                    await asyncio.sleep(0.3)
                    
                    artist_name = album_data['artists'][0] if album_data['artists'] else ""
                    ai_info = await ai_service.generate_album_info(artist_name, album_data['title'])
                    if ai_info:
                        logger.info(f"🤖 Description IA générée pour: {album_data['title']}")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur génération IA pour {album_data['title']}: {e}")
                
                # Ajouter métadonnées
                metadata = Metadata(
                    album_id=album.id,
                    labels=','.join(album_data['labels']) if album_data.get('labels') else None,
                    ai_info=ai_info
                )
                db.add(metadata)
                
                synced_count += 1
                
            except Exception as e:
                logger.error(f"❌ Erreur import album {album_data.get('title', 'Unknown')}: {e}")
                error_count += 1
                db.rollback()  # Rollback pour cet album uniquement
                continue
        
        db.commit()
        logger.info(f"✅ Synchronisation terminée: {synced_count} albums ajoutés, {skipped_count} ignorés, {error_count} erreurs")
        
        return {
            "status": "success",
            "synced_albums": synced_count,
            "skipped_albums": skipped_count,
            "error_albums": error_count,
            "total_albums": len(albums_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur synchronisation Discogs: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur synchronisation: {str(e)}")


@router.post("/ai/generate-info")
async def generate_ai_info(
    album_id: int,
    db: Session = Depends(get_db)
):
    """Générer description IA pour un album."""
    album = db.query(Album).filter(Album.id == album_id).first()
    
    if not album:
        raise HTTPException(status_code=404, detail="Album non trouvé")
    
    # Récupérer le service IA
    settings = get_settings()
    secrets = settings.secrets
    euria_config = secrets.get('euria', {})
    
    ai_service = AIService(
        url=euria_config.get('url'),
        bearer=euria_config.get('bearer'),
        max_attempts=euria_config.get('max_attempts', 5)
    )
    
    # Générer l'info
    artists = [a.name for a in album.artists] if album.artists else ["Unknown"]
    artist_name = ', '.join(artists)
    
    ai_info = await ai_service.generate_album_info(artist_name, album.title)
    
    if not ai_info:
        raise HTTPException(status_code=500, detail="Erreur génération info IA")
    
    # Sauvegarder
    if not album.album_metadata:
        metadata = Metadata(album_id=album.id, ai_info=ai_info)
        db.add(metadata)
    else:
        album.album_metadata.ai_info = ai_info
    
    db.commit()
    
    return {
        "album_id": album_id,
        "ai_info": ai_info
    }


@router.post("/ai/enrich-all")
async def enrich_all_albums(
    limit: int = 10,  # Limiter à 10 albums par défaut pour éviter rate limiting
    db: Session = Depends(get_db)
):
    """Enrichir tous les albums avec Spotify et IA."""
    import logging
    import asyncio
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔄 Début enrichissement de {limit} albums")
    settings = get_settings()
    secrets = settings.secrets
    
    spotify_config = secrets.get('spotify', {})
    ai_config = secrets.get('euria', {})
    
    spotify_service = SpotifyService(
        client_id=spotify_config.get('client_id'),
        client_secret=spotify_config.get('client_secret')
    )
    
    ai_service = AIService(
        url=ai_config.get('url'),
        bearer=ai_config.get('bearer')
    )
    
    try:
        # Récupérer UNIQUEMENT les albums sans ai_info (ignorant spotify_url)
        # On enrichit d'abord l'IA pour tous, puis Spotify sera fait séparément
        albums = db.query(Album).options(joinedload(Album.album_metadata)).outerjoin(
            Metadata, Album.id == Metadata.album_id
        ).filter(
            (Metadata.id == None) | (Metadata.ai_info == None)
        ).limit(limit).all()
        
        logger.info(f"📀 {len(albums)} albums à enrichir")
        
        spotify_added = 0
        ai_added = 0
        errors = 0
        
        for album in albums:
            try:
                updated = False
                artist_name = album.artists[0].name if album.artists else ""
                
                logger.info(f"📀 Traitement: {album.title} (ID:{album.id}) - Spotify:{album.spotify_url is not None} Meta:{album.album_metadata is not None} AI:{album.album_metadata.ai_info if album.album_metadata else None}")
                
                # Enrichir Spotify si manquant
                if not album.spotify_url:
                    try:
                        spotify_url = await spotify_service.search_album_url(artist_name, album.title)
                        if spotify_url:
                            album.spotify_url = spotify_url
                            spotify_added += 1
                            updated = True
                            logger.info(f"🎵 Spotify ajouté: {album.title}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur Spotify pour {album.title}: {e}")
                
                # Enrichir IA si manquant - délai pour éviter rate limit
                if not album.album_metadata or not album.album_metadata.ai_info:
                    try:
                        await asyncio.sleep(1.0)  # Délai de 1s entre appels IA (2000 chars = plus long)
                        ai_info = await ai_service.generate_album_info(artist_name, album.title)
                        if ai_info:
                            if not album.album_metadata:
                                metadata = Metadata(album_id=album.id, ai_info=ai_info)
                                db.add(metadata)
                            else:
                                album.album_metadata.ai_info = ai_info
                            ai_added += 1
                            updated = True
                            logger.info(f"🤖 IA ajoutée: {album.title}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur IA pour {album.title}: {e}")
                
                if updated:
                    db.commit()
                    
            except Exception as e:
                logger.error(f"❌ Erreur enrichissement {album.title}: {e}")
                db.rollback()
                errors += 1
                continue
        
        logger.info(f"✅ Enrichissement terminé: {spotify_added} Spotify, {ai_added} IA, {errors} erreurs")
        
        return {
            "status": "success",
            "albums_processed": len(albums),
            "spotify_added": spotify_added,
            "ai_added": ai_added,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur enrichissement: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur enrichissement: {str(e)}")
