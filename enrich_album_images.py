#!/usr/bin/env python3
"""Enrichir la base de données avec les images d'albums manquantes."""
import sys
import os
import asyncio
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.models.album import Album
from app.models.image import Image
from app.services.lastfm_service import LastFMService
from app.services.discogs_service import DiscogsService

# Charger les secrets
with open('config/secrets.json', 'r') as f:
    secrets = json.load(f)

# Connexion à la base de données avec timeout amélioré
db_path = os.path.join(os.path.dirname(__file__), 'data', 'musique.db')
engine = create_engine(
    f'sqlite:///{db_path}',
    connect_args={'timeout': 30},  # 30 secondes de timeout
    pool_pre_ping=True  # Vérifier les connections avant utilisation
)
Session = sessionmaker(bind=engine)
session = Session()

# Initialiser les services
lastfm_service = LastFMService(
    api_key=secrets['lastfm']['api_key'],
    api_secret=secrets['lastfm']['api_secret'],
    username=secrets['lastfm']['username']
)

discogs_service = DiscogsService(
    api_key=secrets['discogs']['api_key'],
    username=secrets['discogs']['username']
)


async def enrich_album_from_lastfm(album: Album) -> bool:
    """Enrichir un album avec une image depuis Last.fm."""
    album_title = album.title if hasattr(album, 'title') else 'Unknown'
    album_id = album.id if hasattr(album, 'id') else 'Unknown'
    
    try:
        # Récupérer le nom de l'artiste principal
        artist_name = album.artists[0].name if album.artists else "Unknown"
        
        logger.info(f"🔍 Recherche Last.fm: {artist_name} - {album_title}")
        image_url = await lastfm_service.get_album_image(artist_name, album_title)
        
        if image_url and image_url.strip():
            # Vérifier si l'image existe déjà
            existing_image = session.query(Image).filter(
                Image.album_id == album_id,
                Image.url == image_url
            ).first()
            
            if not existing_image:
                # Créer une nouvelle image
                new_image = Image(
                    url=image_url,
                    image_type='album',
                    source='lastfm',
                    album_id=album_id
                )
                session.add(new_image)
                
                # Mettre à jour l'URL de l'album
                album.image_url = image_url
                session.commit()
                
                logger.info(f"✅ Image ajoutée depuis Last.fm: {album_title}")
                return True
            else:
                logger.info(f"⚠️ Image déjà existante: {album_title}")
                return False
        else:
            logger.info(f"❌ Aucune image trouvée sur Last.fm: {album_title}")
            return False
            
    except Exception as e:
        try:
            session.rollback()
        except:
            pass
        logger.error(f"❌ Erreur Last.fm pour {album_title} (ID:{album_id}): {e}")
        return False


def enrich_album_from_discogs(album: Album) -> bool:
    """Enrichir un album avec une image depuis Discogs."""
    try:
        if not album.discogs_id:
            return False
        
        logger.info(f"🔍 Recherche Discogs ID: {album.discogs_id} - {album.title}")
        
        # Récupérer le release Discogs
        release = discogs_service.client.release(album.discogs_id)
        
        # Extraire l'image principale
        if release.images and len(release.images) > 0:
            image_url = release.images[0]['uri']
            
            # Vérifier si l'image existe déjà
            existing_image = session.query(Image).filter(
                Image.album_id == album.id,
                Image.url == image_url
            ).first()
            
            if not existing_image:
                # Créer une nouvelle image
                new_image = Image(
                    url=image_url,
                    image_type='album',
                    source='discogs',
                    album_id=album.id
                )
                session.add(new_image)
                
                # Mettre à jour l'URL de l'album
                album.image_url = image_url
                session.commit()
                
                logger.info(f"✅ Image ajoutée depuis Discogs: {album.title}")
                return True
            else:
                logger.info(f"⚠️ Image déjà existante: {album.title}")
                return False
        else:
            logger.info(f"❌ Aucune image trouvée sur Discogs: {album.title}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur Discogs pour {album.title}: {e}")
        session.rollback()
        return False


async def enrich_albums(limit: int = 100):
    """Enrichir les albums sans images."""
    logger.info("=" * 80)
    logger.info("🎨 ENRICHISSEMENT DES IMAGES D'ALBUMS")
    logger.info("=" * 80)
    
    # Récupérer les albums sans images
    albums_without_images = session.query(Album).filter(
        (Album.image_url.is_(None)) | (Album.image_url == '')
    ).limit(limit).all()
    
    total = len(albums_without_images)
    logger.info(f"\n📊 {total} albums sans images trouvés (limite: {limit})\n")
    
    if total == 0:
        logger.info("✅ Tous les albums ont déjà des images !")
        return
    
    success_count = 0
    failed_count = 0
    
    for idx, album in enumerate(albums_without_images, 1):
        logger.info(f"\n--- Album {idx}/{total} ---")
        artist_name = album.artists[0].name if album.artists else "Unknown"
        logger.info(f"📀 {artist_name} - {album.title} ({album.year or 'N/A'})")
        
        # Essayer d'abord Discogs si on a un discogs_id
        if album.discogs_id:
            if enrich_album_from_discogs(album):
                success_count += 1
                await asyncio.sleep(0.6)  # Rate limiting Discogs
                continue
        
        # Sinon essayer Last.fm
        if await enrich_album_from_lastfm(album):
            success_count += 1
            await asyncio.sleep(0.3)  # Rate limiting Last.fm
        else:
            failed_count += 1
        
        # Pause pour respecter les rate limits
        if idx % 10 == 0:
            logger.info(f"\n⏸️  Pause après {idx} albums...")
            await asyncio.sleep(2)
    
    # Statistiques finales
    logger.info("\n" + "=" * 80)
    logger.info("📊 RÉSUMÉ")
    logger.info("=" * 80)
    logger.info(f"✅ Images ajoutées: {success_count}")
    logger.info(f"❌ Échecs: {failed_count}")
    logger.info(f"📈 Taux de succès: {(success_count/total*100):.1f}%")
    
    # Vérifier le nouveau total
    albums_with_images = session.query(Album).filter(
        Album.image_url.isnot(None),
        Album.image_url != '',
        Album.image_url.like('http%')
    ).count()
    total_albums = session.query(Album).count()
    
    logger.info(f"\n📊 Base de données:")
    logger.info(f"   Total albums: {total_albums}")
    logger.info(f"   Avec images: {albums_with_images}")
    logger.info(f"   Pourcentage: {(albums_with_images/total_albums*100):.1f}%")
    logger.info("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrichir les images d\'albums')
    parser.add_argument('--limit', type=int, default=100, help='Nombre maximum d\'albums à traiter (défaut: 100)')
    args = parser.parse_args()
    
    try:
        asyncio.run(enrich_albums(limit=args.limit))
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interruption utilisateur")
    finally:
        session.close()
        logger.info("🔒 Session fermée")
