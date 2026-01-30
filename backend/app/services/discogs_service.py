"""Service Discogs pour la gestion de collection."""
import discogs_client
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DiscogsService:
    """Client pour l'API Discogs."""
    
    def __init__(self, api_key: str, username: str):
        self.api_key = api_key
        self.username = username
        self.client = discogs_client.Client(
            'MusicTrackerApp/4.0',
            user_token=api_key
        )
    
    def get_collection(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Récupérer la collection Discogs de l'utilisateur.
        
        Args:
            limit: Nombre maximum d'albums à récupérer (None = tous)
        """
        try:
            logger.info("🔍 Début récupération collection Discogs")
            user = self.client.identity()
            logger.info(f"✅ Utilisateur: {user.username}, {user.num_collection} releases")
            
            collection = user.collection_folders[0].releases
            logger.info(f"📁 Folder: {user.collection_folders[0].name}, Count: {user.collection_folders[0].count}")
            
            albums = []
            count = 0
            errors_404 = []
            
            for release in collection:
                if limit and count >= limit:
                    logger.info(f"⚠️ Limite de {limit} albums atteinte")
                    break
                
                try:
                    release_data = release.release
                    count += 1
                    
                    if count % 10 == 0:
                        logger.info(f"📀 Traitement album {count}...")
                    
                    album_info = {
                        "release_id": release_data.id,
                        "title": release_data.title,
                        "year": release_data.year,
                        "artists": [artist.name for artist in release_data.artists],
                        "labels": [label.name for label in release_data.labels] if hasattr(release_data, 'labels') else [],
                        "genres": release_data.genres if hasattr(release_data, 'genres') else [],
                        "styles": release_data.styles if hasattr(release_data, 'styles') else [],
                        "cover_image": release_data.images[0]['uri'] if release_data.images else None,
                        "discogs_url": release_data.url,
                        "formats": [f.get('name', 'Unknown') for f in release_data.formats] if hasattr(release_data, 'formats') else []
                    }
                    
                    albums.append(album_info)
                    
                except Exception as e:
                    # Log détaillé pour identifier le release problématique
                    if '404' in str(e):
                        error_info = f"Position {count}, Release ID: {getattr(release, 'id', 'unknown')}"
                        errors_404.append(error_info)
                        logger.warning(f"⚠️ Erreur traitement release (404): {error_info} - Album supprimé de Discogs")
                    else:
                        logger.warning(f"⚠️ Erreur traitement release à position {count}: {e}")
                    continue
            
            if errors_404:
                logger.info(f"📋 {len(errors_404)} releases 404 ignorés (supprimés de Discogs): {', '.join(errors_404[:5])}{' ...' if len(errors_404) > 5 else ''}")
            
            logger.info(f"✅ Collection récupérée: {len(albums)} albums")
            return albums
            
        except Exception as e:
            logger.error(f"Erreur récupération collection Discogs: {e}")
            return []
    
    def get_release_info(self, release_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer les informations d'une release Discogs."""
        try:
            release = self.client.release(release_id)
            
            info = {
                "release_id": release.id,
                "title": release.title,
                "year": release.year,
                "artists": [artist.name for artist in release.artists],
                "labels": [label.name for label in release.labels] if hasattr(release, 'labels') else [],
                "genres": release.genres if hasattr(release, 'genres') else [],
                "styles": release.styles if hasattr(release, 'styles') else [],
                "cover_image": release.images[0]['uri'] if release.images else None,
                "discogs_url": release.url,
                "notes": release.notes if hasattr(release, 'notes') else None,
                "tracklist": [
                    {
                        "position": track.position,
                        "title": track.title,
                        "duration": track.duration if hasattr(track, 'duration') else None
                    }
                    for track in release.tracklist
                ] if hasattr(release, 'tracklist') else []
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Erreur récupération release {release_id} Discogs: {e}")
            return None
