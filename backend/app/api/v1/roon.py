"""Routes API pour le contrôle Roon."""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.config import get_settings
from app.api.v1.services import get_roon_service as get_roon_service_singleton

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Schémas Pydantic
# ============================================================================

class RoonPlayRequest(BaseModel):
    """Requête pour jouer un track sur Roon."""
    zone_name: str
    track_title: str
    artist: str
    album: Optional[str] = None


class RoonControlRequest(BaseModel):
    """Requête pour contrôler la lecture."""
    zone_name: str
    control: str  # play, pause, stop, next, previous


class RoonPlayTrackByIdRequest(BaseModel):
    """Requête pour jouer un track par son ID (depuis la base de données)."""
    zone_name: str
    track_id: int


class RoonPlayPlaylistRequest(BaseModel):
    """Requête pour jouer une playlist entière sur Roon."""
    zone_name: str
    playlist_id: int


# ============================================================================
# Helpers
# ============================================================================

def is_roon_enabled() -> bool:
    """Vérifier si le contrôle Roon est activé."""
    settings = get_settings()
    roon_control_config = settings.app_config.get('roon_control', {})
    return roon_control_config.get('enabled', False)


def check_roon_enabled():
    """Vérifier si Roon est activé, sinon lever une exception."""
    if not is_roon_enabled():
        raise HTTPException(
            status_code=403,
            detail="Le contrôle Roon n'est pas activé. Activez-le dans config/app.json (roon_control.enabled)"
        )


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/status")
async def get_roon_status():
    """Vérifier si le contrôle Roon est activé et disponible."""
    enabled = is_roon_enabled()
    
    if not enabled:
        return {
            "enabled": False,
            "available": False,
            "message": "Contrôle Roon désactivé"
        }
    
    # Vérifier la configuration Roon
    settings = get_settings()
    roon_config = settings.secrets.get('roon', {})
    
    if not roon_config.get('server'):
        return {
            "enabled": True,
            "available": False,
            "message": "Roon non configuré (serveur manquant)"
        }
    
    # Utiliser le singleton pour éviter de créer plusieurs connexions
    try:
        roon_service = get_roon_service_singleton()
        if roon_service is None:
            return {
                "enabled": True,
                "available": False,
                "message": "Roon non configuré (serveur manquant)"
            }
        
        connected = roon_service.is_connected()
        
        return {
            "enabled": True,
            "available": connected,
            "message": "Roon disponible" if connected else "Impossible de se connecter à Roon"
        }
    except Exception as e:
        return {
            "enabled": True,
            "available": False,
            "message": f"Erreur: {str(e)}"
        }


def get_roon_service():
    """Obtenir l'instance singleton du service Roon."""
    roon_service = get_roon_service_singleton()
    
    if roon_service is None:
        raise HTTPException(status_code=503, detail="Roon non configuré")
    
    if not roon_service.is_connected():
        raise HTTPException(status_code=503, detail="Impossible de se connecter à Roon")
    
    return roon_service


@router.get("/zones")
async def get_zones():
    """Récupérer les zones Roon disponibles."""
    check_roon_enabled()  # Vérifier que Roon est activé
    
    try:
        roon_service = get_roon_service()
        zones = roon_service.get_zones()
        
        return {
            "zones": [
                {
                    "zone_id": zone_id,
                    "name": zone_info.get("display_name", "Unknown"),
                    "state": zone_info.get("state", "unknown")
                }
                for zone_id, zone_info in zones.items()
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")


@router.get("/now-playing")
async def get_now_playing():
    """Récupérer le morceau en cours de lecture."""
    check_roon_enabled()  # Vérifier que Roon est activé
    
    try:
        roon_service = get_roon_service()
        now_playing = roon_service.get_now_playing()
        
        if not now_playing:
            return {"message": "Aucune lecture en cours"}
        
        return now_playing
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")


@router.post("/play")
async def play_track(request: RoonPlayRequest):
    """Démarrer la lecture d'un track sur Roon."""
    check_roon_enabled()  # Vérifier que Roon est activé
    
    try:
        roon_service = get_roon_service()
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(request.zone_name)
        if not zone_id:
            zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{request.zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Démarrer la lecture
        success = roon_service.play_track(
            zone_or_output_id=zone_id,
            track_title=request.track_title,
            artist=request.artist,
            album=request.album
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors du démarrage de la lecture sur Roon. "
                       "Vérifiez que l'artiste et l'album sont présents dans votre bibliothèque Roon."
            )
        
        return {
            "message": f"Lecture démarrée: {request.track_title} - {request.artist}",
            "zone": request.zone_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")


@router.post("/control")
async def control_playback(request: RoonControlRequest):
    """Contrôler la lecture (play, pause, stop, next, previous)."""
    check_roon_enabled()  # Vérifier que Roon est activé
    
    try:
        roon_service = get_roon_service()
        
        # Vérifier la commande
        valid_controls = ['play', 'pause', 'stop', 'next', 'previous']
        if request.control not in valid_controls:
            raise HTTPException(
                status_code=400,
                detail=f"Contrôle invalide. Valeurs acceptées: {', '.join(valid_controls)}"
            )
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(request.zone_name)
        if not zone_id:
            zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{request.zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Exécuter la commande
        success = roon_service.playback_control(zone_id, request.control)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Erreur exécution commande '{request.control}'")
        
        return {
            "message": f"Commande '{request.control}' exécutée",
            "zone": request.zone_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")


@router.post("/pause-all")
async def pause_all():
    """Mettre en pause toutes les zones."""
    check_roon_enabled()  # Vérifier que Roon est activé
    
    try:
        roon_service = get_roon_service()
        success = roon_service.pause_all()
        
        if not success:
            raise HTTPException(status_code=500, detail="Erreur pause globale")
        
        return {"message": "Toutes les zones mises en pause"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")


@router.post("/play-track")
async def play_track_by_id(request: RoonPlayTrackByIdRequest):
    """Jouer un track depuis la base de données AIME sur Roon.
    
    Cette fonction facilite la lecture d'un track depuis l'interface web
    en utilisant directement l'ID du track dans la base de données.
    """
    check_roon_enabled()  # Vérifier que Roon est activé
    
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models import Track, Album, Artist
    
    # Créer une session de base de données
    db: Session = SessionLocal()
    
    try:
        # Récupérer le track depuis la base
        track = db.query(Track).filter(Track.id == request.track_id).first()
        if not track:
            raise HTTPException(status_code=404, detail=f"Track {request.track_id} non trouvé")
        
        # Récupérer l'album et les artistes
        album = db.query(Album).filter(Album.id == track.album_id).first()
        if not album:
            raise HTTPException(status_code=404, detail="Album non trouvé pour ce track")
        
        # Récupérer les artistes de l'album
        artists = [a.name for a in album.artists] if album.artists else ["Unknown"]
        artist_name = ", ".join(artists)
        
        # Initialiser Roon
        roon_service = get_roon_service()
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(request.zone_name)
        if not zone_id:
            zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{request.zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Démarrer la lecture
        success = roon_service.play_track(
            zone_or_output_id=zone_id,
            track_title=track.title,
            artist=artist_name,
            album=album.title
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors du démarrage de la lecture sur Roon. "
                       "Vérifiez que l'artiste et l'album sont présents dans votre bibliothèque Roon."
            )
        
        return {
            "message": f"Lecture démarrée: {track.title} - {artist_name}",
            "track": {
                "id": track.id,
                "title": track.title,
                "artist": artist_name,
                "album": album.title
            },
            "zone": request.zone_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        db.close()


# @router.post("/play-playlist")
# async def play_playlist(request: RoonPlayPlaylistRequest):
#     """DEPRECATED: Remplacé par les collections d'albums."""
#     pass
    
    db: Session = SessionLocal()
    
    try:
        # Récupérer la playlist
        playlist = db.query(Playlist).filter(Playlist.id == request.playlist_id).first()
        if not playlist:
            raise HTTPException(status_code=404, detail=f"Playlist {request.playlist_id} non trouvée")
        
        # Récupérer les tracks de la playlist
        playlist_tracks = db.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == request.playlist_id
        ).order_by(PlaylistTrack.position).all()
        
        if not playlist_tracks:
            raise HTTPException(status_code=400, detail="La playlist est vide")
        
        # Initialiser Roon
        roon_service = get_roon_service()
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(request.zone_name)
        if not zone_id:
            zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{request.zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Préparer la liste des tracks avec leurs infos
        tracks_info = []
        for pt in playlist_tracks:
            track = db.query(Track).filter(Track.id == pt.track_id).first()
            if not track:
                continue
            
            album = db.query(Album).filter(Album.id == track.album_id).first()
            if not album:
                continue
            
            artists = [a.name for a in album.artists] if album.artists else ["Unknown"]
            artist_name = ", ".join(artists)
            
            # Récupérer la durée si disponible
            duration = track.duration_seconds if hasattr(track, 'duration_seconds') else None
            
            tracks_info.append({
                'title': track.title,
                'artist': artist_name,
                'album': album.title,
                'duration_seconds': duration,
                'track_id': track.id
            })
        
        if not tracks_info:
            raise HTTPException(
                status_code=400,
                detail="Aucun track valide dans la playlist"
            )
        
        # Démarrer la queue avec enchaînement automatique
        queue_manager = PlaylistQueueManager(roon_service)
        
        # Callbacks pour logging
        def on_track_started(track_data):
            logger.info(f"▶️  Lecture: {track_data.get('title')} - {track_data.get('artist')}")
        
        def on_queue_complete():
            logger.info(f"✅ Playlist terminée: {playlist.name}")
        
        queue = queue_manager.start_playlist_queue(
            zone_id=zone_id,
            tracks=tracks_info,
            on_track_started=on_track_started,
            on_queue_complete=on_queue_complete
        )
        
        # Récupérer le premier track pour la réponse
        first_track_info = tracks_info[0]
        
        return {
            "message": f"Lecture de la playlist démarrée avec enchaînement automatique: {playlist.name}",
            "playlist": {
                "id": playlist.id,
                "name": playlist.name,
                "track_count": len(tracks_info)
            },
            "now_playing": {
                "title": first_track_info['title'],
                "artist": first_track_info['artist'],
                "album": first_track_info['album']
            },
            "queue_info": {
                "total_tracks": len(tracks_info),
                "mode": "automatic_sequential",
                "description": "Les tracks seront lus séquentiellement avec synchronisation basée sur la durée"
            },
            "zone": request.zone_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur play_playlist: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        db.close()


# @router.get("/debug/playlist/{playlist_id}")
# async def debug_playlist(playlist_id: int):
#     """DEPRECATED: Remplacé par les collections d'albums."""
#     pass
    
    db: Session = SessionLocal()
    
    try:
        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist:
            raise HTTPException(status_code=404, detail=f"Playlist {playlist_id} non trouvée")
        
        playlist_tracks = db.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist_id
        ).order_by(PlaylistTrack.position).all()
        
        tracks_info = []
        for pt in playlist_tracks:
            track = db.query(Track).filter(Track.id == pt.track_id).first()
            if track:
                album = db.query(Album).filter(Album.id == track.album_id).first()
                artists = [a.name for a in album.artists] if (album and album.artists) else ["Unknown"]
                
                tracks_info.append({
                    "position": pt.position,
                    "track_id": track.id,
                    "title": track.title,
                    "artist": ", ".join(artists),
                    "album": album.title if album else "Unknown"
                })
        
        return {
            "playlist": {
                "id": playlist.id,
                "name": playlist.name,
                "algorithm": playlist.algorithm
            },
            "track_count": len(tracks_info),
            "tracks": tracks_info[:5]  # Montrer les 5 premiers tracks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        db.close()


class RoonPlayAlbumRequest(BaseModel):
    """Requête pour jouer un album entier sur Roon."""
    zone_name: str
    album_id: int


@router.post("/play-album")
async def play_album(request: RoonPlayAlbumRequest):
    """Jouer un album entier sur Roon.
    
    Cette fonction permet de démarrer la lecture d'un album
    en jouant le premier track disponible, puis les suivants automatiquement.
    """
    check_roon_enabled()  # Vérifier que Roon est activé
    
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models import Album, Track
    
    db: Session = SessionLocal()
    
    try:
        # Récupérer l'album
        album = db.query(Album).filter(Album.id == request.album_id).first()
        if not album:
            raise HTTPException(status_code=404, detail=f"Album {request.album_id} non trouvé")
        
        # Récupérer les tracks de l'album
        tracks = db.query(Track).filter(Track.album_id == request.album_id).all()
        
        if not tracks:
            raise HTTPException(status_code=400, detail="L'album n'a pas de tracks")
        
        # Initialiser Roon
        roon_service = get_roon_service()
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(request.zone_name)
        if not zone_id:
            zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{request.zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Récupérer les infos de l'artiste principal
        artist_name = ", ".join([a.name for a in album.artists]) if album.artists else "Unknown"
        
        # Essayer de jouer l'album complet directement
        success = roon_service.play_album(
            zone_or_output_id=zone_id,
            artist=artist_name,
            album=album.title
        )
        
        if not success:
            # Si l'approche album ne marche pas, essayer track par track en dernier recours
            logger.info(f"⚠️ Lecture directe de l'album échouée, tentative track par track...")
            
            first_track = None
            skipped_count = 0
            
            for track in tracks:
                # Tenter de lancer ce track
                track_success = roon_service.play_track(
                    zone_or_output_id=zone_id,
                    track_title=track.title,
                    artist=artist_name,
                    album=album.title
                )
                
                if track_success:
                    # Track trouvé et lancé !
                    first_track = track
                    break
                else:
                    skipped_count += 1
            
            if not first_track:
                raise HTTPException(
                    status_code=400,
                    detail=f"Impossible de lancer l'album: aucun track trouvé dans Roon ({skipped_count}/{len(tracks)} tracks non trouvés)"
                )
        else:
            # La lecture directe a marché, prendre le premier track pour les infos
            first_track = tracks[0] if tracks else None
        
        # Préparer les infos de l'album
        tracks_info = []
        for track in tracks[:10]:  # Limiter à 10 tracks pour l'affichage
            artists = [a.name for a in album.artists] if album.artists else ["Unknown"]
            
            tracks_info.append({
                "track_id": track.id,
                "title": track.title,
                "artist": ", ".join(artists),
                "album": album.title
            })
        
        return {
            "album": {
                "id": album.id,
                "title": album.title,
                "artist": ", ".join([a.name for a in album.artists]) if album.artists else "Unknown",
                "year": album.year
            },
            "zone": request.zone_name,
            "first_track": {
                "id": first_track.id,
                "title": first_track.title
            },
            "track_count": len(tracks),
            "tracks": tracks_info  # Montrer les 10 premiers tracks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        db.close()


class RoonPlaybackControlRequest(BaseModel):
    """Requête pour contrôler la lecture."""
    zone_name: str
    control: str  # play, pause, stop, next, previous


@router.post("/control")
async def control_playback(request: RoonPlaybackControlRequest):
    """Contrôler la lecture sur une zone Roon."""
    check_roon_enabled()
    
    try:
        roon_service = get_roon_service()
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(request.zone_name)
        if not zone_id:
            zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{request.zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Valider la commande
        valid_controls = ["play", "pause", "stop", "next", "previous"]
        if request.control.lower() not in valid_controls:
            raise HTTPException(
                status_code=400,
                detail=f"Commande invalide: {request.control}. Valides: {', '.join(valid_controls)}"
            )
        
        # Exécuter la commande
        success = roon_service.playback_control(zone_id, request.control.lower())
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'exécution de {request.control}")
        
        return {
            "message": f"Commande exécutée: {request.control}",
            "zone": request.zone_name,
            "control": request.control
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# ============================================================================
# Route supplémentaire pour magazine
# ============================================================================

class RoonPlayByNameRequest(BaseModel):
    """Requête pour jouer un album par son nom d'artiste et titre."""
    artist_name: Optional[str] = None
    album_title: str
    zone_name: Optional[str] = None  # Zone optionnelle


@router.post("/play-album-by-name")
async def play_album_by_name(request: RoonPlayByNameRequest):
    """Jouer un album via son nom d'artiste et titre (depuis le magazine).
    
    Cherche l'album dans la base de données et le joue sur la première zone disponible.
    """
    logger.info(f"📡 Requête play_album_by_name: {request.artist_name} - {request.album_title}")
    
    check_roon_enabled()
    
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models import Album
    
    db: Session = SessionLocal()
    
    try:
        # Initialiser Roon en premier
        logger.info("🔌 Initialisation du service Roon...")
        try:
            roon_service = get_roon_service_singleton()
            logger.info("✅ Service Roon initialisé")
        except Exception as e:
            logger.error(f"❌ Impossible d'initialiser Roon: {e}")
            raise HTTPException(status_code=503, detail=f"Roon non disponible: {str(e)}")
        
        # Vérifier la connectivité
        try:
            zones = roon_service.get_zones()
            logger.info(f"📍 Zones Roon trouvées: {list(zones.keys())}")
            if not zones:
                logger.error("❌ Aucune zone Roon disponible")
                raise HTTPException(status_code=503, detail="Aucune zone Roon disponible. Vérifiez que Roon Core est en ligne.")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des zones: {e}")
            raise HTTPException(status_code=503, detail=f"Impossible de communiquer avec Roon: {str(e)}")
        
        # Déterminer la zone à utiliser
        zone_id = None
        if request.zone_name:
            zone_id = roon_service.get_zone_by_name(request.zone_name)
            if not zone_id:
                raise HTTPException(status_code=404, detail=f"Zone '{request.zone_name}' non trouvée")
        else:
            zone_id = list(zones.keys())[0]
            logger.info(f"📍 Utilisation de la zone par défaut: {zone_id}")
        
        # Chercher l'album par titre et artiste
        query = db.query(Album).filter(Album.title == request.album_title)
        
        if request.artist_name:
            from app.models import Artist
            query = query.join(Artist, Album.artists).filter(
                Artist.name == request.artist_name
            )
        
        album = query.first()
        
        if album:
            logger.info(f"✅ Album trouvé en base: ID={album.id}")
            artist_name = ", ".join([a.name for a in album.artists]) if album.artists else request.artist_name or "Unknown"
        else:
            logger.warning(f"⚠️ Album non trouvé en base: {request.artist_name} - {request.album_title}")
            artist_name = request.artist_name or "Unknown"
        
        # Jouer l'album
        logger.info(f"▶️ Lancement de la lecture: {artist_name} - {request.album_title}")
        try:
            success = roon_service.play_album(
                zone_or_output_id=zone_id,
                artist=artist_name,
                album=request.album_title
            )
            logger.info(f"{'✅' if success else '⚠️'} Résultat play_album: {success}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'appel play_album: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur Roon play_album: {str(e)}")
        
        return {
            "status": "playing" if success else "not_found",
            "message": "Album en lecture" if success else "Album lancé (non trouvé dans la librairie Roon)",
            "album_id": album.id if album else None,
            "artist": artist_name,
            "album": request.album_title
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur play_album_by_name: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        try:
            db.close()
        except:
            pass

