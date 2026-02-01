"""Script pour mettre à jour les durées manquantes dans la base de données."""
import json
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Track, Album
from app.services.spotify_service import SpotifyService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config():
    """Charger la configuration depuis config/secrets.json."""
    try:
        with open('config/secrets.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Fichier config/secrets.json introuvable")
        return {}


def update_durations():
    """Mettre à jour les durées manquantes en utilisant Spotify."""
    config = load_config()
    spotify_config = config.get('spotify', {})
    
    if not spotify_config.get('client_id') or not spotify_config.get('client_secret'):
        logger.error("Configuration Spotify manquante")
        return
    
    # Initialiser Spotify
    spotify = SpotifyService(
        client_id=spotify_config['client_id'],
        client_secret=spotify_config['client_secret']
    )
    
    db = SessionLocal()
    try:
        # Récupérer tous les tracks sans durée
        tracks_without_duration = db.query(Track).filter(
            (Track.duration_seconds == None) | (Track.duration_seconds == 0)
        ).join(Album).limit(500).all()
        
        logger.info(f"🔍 Trouvé {len(tracks_without_duration)} tracks sans durée")
        
        updated_count = 0
        for track in tracks_without_duration:
            album = track.album
            if not album or not album.artists:
                continue
            
            artist_name = album.artists[0].name if album.artists else None
            if not artist_name:
                continue
            
            # Rechercher sur Spotify
            logger.debug(f"Recherche: {artist_name} - {track.title}")
            
            try:
                spotify_track = spotify.search_track(artist_name, track.title)
                if spotify_track and 'duration_ms' in spotify_track:
                    duration_seconds = spotify_track['duration_ms'] // 1000
                    track.duration_seconds = duration_seconds
                    updated_count += 1
                    
                    if updated_count % 10 == 0:
                        db.commit()
                        logger.info(f"✅ Mis à jour {updated_count} tracks...")
            except Exception as e:
                logger.error(f"Erreur pour {track.title}: {e}")
                continue
        
        # Commit final
        db.commit()
        logger.info(f"✅ Terminé: {updated_count} tracks mis à jour avec une durée")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    update_durations()
