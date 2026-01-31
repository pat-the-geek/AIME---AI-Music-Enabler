"""Service Discogs pour la gestion de collection."""
import discogs_client
from typing import Optional, List, Dict, Any
import logging
import time
from app.core.retry import CircuitBreaker, retry_with_backoff
from app.core.exceptions import DiscogsServiceException

logger = logging.getLogger(__name__)

# Circuit breaker pour le service Discogs
discogs_circuit_breaker = CircuitBreaker(
    "Discogs",
    failure_threshold=5,
    success_threshold=3,
    timeout=60,
    recovery_timeout=300
)


class DiscogsService:
    """Client pour l'API Discogs avec retry logic et circuit breaker."""
    
    def __init__(self, api_key: str, username: str):
        self.api_key = api_key
        self.username = username
        self.client = discogs_client.Client(
            'MusicTrackerApp/4.0',
            user_token=api_key
        )
        self.rate_limit_delay = 0.5  # Délai entre requêtes pour respecter les limites
        self.last_request_time = 0
    
    def _rate_limit_wait(self):
        """Attendre le délai minimum entre requêtes."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    @retry_with_backoff(max_attempts=3, initial_delay=2.0, max_delay=10.0)
    def get_collection(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Récupérer la collection Discogs de l'utilisateur avec retry logic.
        
        Args:
            limit: Nombre maximum d'albums à récupérer (None = tous)
        """
        try:
            # Vérifier le circuit breaker
            if discogs_circuit_breaker.state == "OPEN":
                logger.warning("⚠️ Circuit breaker Discogs ouvert - service indisponible temporairement")
                raise DiscogsServiceException("Service Discogs temporairement indisponible")
            
            logger.info("🔍 Début récupération collection Discogs")
            self._rate_limit_wait()
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
                    self._rate_limit_wait()
                    release_data = release.release
                    count += 1
                    
                    if count % 10 == 0:
                        logger.info(f"📀 Traitement album {count}...")
                    
                    # Valider les données avant de les ajouter
                    album_info = self._extract_album_info(release_data, count)
                    if album_info:
                        albums.append(album_info)
                    
                except Exception as e:
                    # Log détaillé pour identifier le release problématique
                    error_str = str(e)
                    if '404' in error_str or 'not found' in error_str.lower():
                        error_info = f"Position {count}, Release ID: {getattr(release, 'id', 'unknown')}"
                        errors_404.append(error_info)
                        logger.warning(f"⚠️ Erreur traitement release (404): {error_info} - Album supprimé de Discogs")
                    else:
                        logger.warning(f"⚠️ Erreur traitement release à position {count}: {e}")
                    continue
            
            if errors_404:
                logger.info(f"📋 {len(errors_404)} releases 404 ignorés (supprimés de Discogs): {', '.join(errors_404[:5])}{' ...' if len(errors_404) > 5 else ''}")
            
            logger.info(f"✅ Collection récupérée: {len(albums)} albums")
            discogs_circuit_breaker.record_success()
            return albums
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération collection Discogs: {e}")
            discogs_circuit_breaker.record_failure()
            raise
    
    def _extract_album_info(self, release_data, position: int) -> Optional[Dict[str, Any]]:
        """Extraire et valider les informations d'un album."""
        try:
            # Valider les champs obligatoires
            if not release_data.title or not release_data.artists:
                logger.warning(f"⚠️ Album à position {position} a des champs manquants")
                return None
            
            artists = [artist.name for artist in release_data.artists if artist.name]
            if not artists:
                logger.warning(f"⚠️ Album à position {position} n'a pas d'artiste valide")
                return None
            
            # Valider et nettoyer les données
            year = release_data.year if release_data.year and release_data.year > 0 else None
            
            album_info = {
                "release_id": release_data.id,
                "title": release_data.title.strip(),
                "year": year,
                "artists": artists,
                "labels": [label.name for label in release_data.labels if hasattr(release_data, 'labels') and label.name] if hasattr(release_data, 'labels') else [],
                "genres": list(release_data.genres) if hasattr(release_data, 'genres') and release_data.genres else [],
                "styles": list(release_data.styles) if hasattr(release_data, 'styles') and release_data.styles else [],
                "cover_image": release_data.images[0]['uri'] if release_data.images else None,
                "discogs_url": release_data.url if hasattr(release_data, 'url') else None,
                "formats": [f.get('name', 'Unknown') for f in release_data.formats if f.get('name')] if hasattr(release_data, 'formats') and release_data.formats else []
            }
            
            return album_info
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur extraction album à position {position}: {e}")
            return None
    
    @retry_with_backoff(max_attempts=2, initial_delay=1.0, max_delay=5.0)
    def get_release_info(self, release_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer les informations d'une release Discogs avec retry logic."""
        try:
            if discogs_circuit_breaker.state == "OPEN":
                logger.warning("⚠️ Circuit breaker Discogs ouvert")
                return None
            
            self._rate_limit_wait()
            release = self.client.release(release_id)
            
            artists = [artist.name for artist in release.artists if artist.name]
            
            info = {
                "release_id": release.id,
                "title": release.title,
                "year": release.year if release.year and release.year > 0 else None,
                "artists": artists,
                "labels": [label.name for label in release.labels if hasattr(release, 'labels') and label.name] if hasattr(release, 'labels') else [],
                "genres": list(release.genres) if hasattr(release, 'genres') else [],
                "styles": list(release.styles) if hasattr(release, 'styles') else [],
                "cover_image": release.images[0]['uri'] if release.images else None,
                "discogs_url": release.url if hasattr(release, 'url') else None,
                "notes": release.notes if hasattr(release, 'notes') and release.notes else None,
                "tracklist": self._extract_tracklist(release) if hasattr(release, 'tracklist') else []
            }
            
            discogs_circuit_breaker.record_success()
            return info
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération release {release_id} Discogs: {e}")
            discogs_circuit_breaker.record_failure()
            return None
    
    def _extract_tracklist(self, release) -> List[Dict[str, Any]]:
        """Extraire la tracklist en validant les données."""
        tracklist = []
        try:
            if hasattr(release, 'tracklist') and release.tracklist:
                for track in release.tracklist:
                    try:
                        track_info = {
                            "position": track.position if hasattr(track, 'position') else None,
                            "title": track.title if hasattr(track, 'title') else "Unknown",
                            "duration": track.duration if hasattr(track, 'duration') else None
                        }
                        tracklist.append(track_info)
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur extraction track: {e}")
                        continue
        except Exception as e:
            logger.warning(f"⚠️ Erreur extraction tracklist: {e}")
        
        return tracklist
