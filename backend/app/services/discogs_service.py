"""Service Discogs pour la gestion de collection."""
import discogs_client
from typing import Optional, List, Dict, Any
import logging
import time
import requests
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
    def get_collection(self, limit: Optional[int] = None, skip_ids: Optional[set] = None) -> List[Dict[str, Any]]:
        """Récupérer la collection Discogs de l'utilisateur avec retry logic.
        
        Args:
            limit: Nombre maximum d'albums à récupérer (None = tous)
            skip_ids: Set d'IDs Discogs à ignorer (pour éviter appels API inutiles)
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
            
            collection_folder = user.collection_folders[0]
            logger.info(f"📁 Folder: {collection_folder.name}, Count: {collection_folder.count}")
            
            albums = []
            count = 0
            errors_404 = []
            total_expected = user.num_collection
            
            # PAGINATION EXPLICITE PAR API DIRECTE
            # Récupérer les URLs de la collection pour faire des appels API directs
            # Cela évite les problèmes de l'itérateur auto-pagé de discogs_client
            
            page_num = 1
            page_size = 100
            
            while True:
                try:
                    logger.info(f"📑 Chargement page {page_num} ({page_size} items/page)...")
                    self._rate_limit_wait()
                    
                    # Augmenter le délai entre les requêtes pour éviter les 429
                    if page_num > 1:
                        time.sleep(1.5)  # Délai supplémentaire entre les pages pour respecter rate limit
                    
                    # Construire l'URL d'API pour récupérer les releases avec pagination explicite
                    # Utiliser l'API Discogs directement pour avoir un meilleur contrôle
                    headers = {'User-Agent': 'MusicTrackerApp/4.0', 'Authorization': f'Discogs token={self.api_key}'}
                    url = f"https://api.discogs.com/users/{self.username}/collection/folders/0/releases"
                    params = {
                        'page': page_num,
                        'per_page': page_size
                    }
                    
                    response = requests.get(url, headers=headers, params=params, timeout=15)
                    response.raise_for_status()
                    data = response.json()
                    
                    releases = data.get('releases', [])
                    pagination_info = data.get('pagination', {})
                    
                    if not releases:
                        logger.info(f"✅ Fin de pagination atteinte (page {page_num} vide)")
                        break
                    
                    logger.info(f"📊 Page {page_num}: {len(releases)} releases (Pages totales: {pagination_info.get('pages', '?')})")
                    
                    # Traiter chaque release de cette page
                    for release_item in releases:
                        if limit and count >= limit:
                            logger.info(f"⚠️ Limite de {limit} albums atteinte")
                            logger.info(f"✅ Collection récupérée: {len(albums)} albums")
                            return albums  # Retourner directement
                        
                        try:
                            release_id = release_item['id']
                            
                            # ⚠️ OPTIMISATION: Si l'album existe déjà, ne pas faire l'appel API
                            if skip_ids and str(release_id) in skip_ids:
                                logger.debug(f"⏭️ Release {release_id} existe déjà, skipped")
                                continue
                            
                            self._rate_limit_wait()
                            
                            # Récupérer l'objet release complet depuis le client discogs_client
                            release_data = self.client.release(release_id)
                            count += 1
                            
                            # Log de progression
                            if count % 50 == 0:
                                logger.info(f"📀 Traitement album {count}/{total_expected}...")
                            
                            # Valider les données avant de les ajouter
                            album_info = self._extract_album_info(release_data, count)
                            if album_info:
                                albums.append(album_info)
                            
                        except Exception as e:
                            # Log détaillé pour identifier le release problématique
                            error_str = str(e)
                            if '404' in error_str or 'not found' in error_str.lower():
                                error_info = f"Position {count}, Release ID: {release_id}"
                                errors_404.append(error_info)
                                logger.warning(f"⚠️ Erreur traitement release (404): {error_info} - Album supprimé de Discogs")
                            else:
                                logger.warning(f"⚠️ Erreur traitement release {release_id} à position {count}: {e}")
                            continue
                    
                    # Passer à la page suivante
                    if page_num >= pagination_info.get('pages', 1):
                        logger.info(f"✅ Dernière page atteinte")
                        break
                    
                    page_num += 1
                    
                except requests.exceptions.Timeout:
                    logger.error(f"❌ Timeout lors du chargement page {page_num}")
                    logger.info(f"⚠️ Arrêt de la pagination à la page {page_num}, {count} albums récupérés")
                    break
                except requests.exceptions.HTTPError as e:
                    # Gestion spéciale du 429 (Too Many Requests)
                    if e.response.status_code == 429:
                        logger.warning(f"⚠️ Rate-limit atteint (429) à la page {page_num}")
                        logger.info(f"✅ {count} albums récupérés avant le rate-limit")
                        logger.info(f"⚠️ Arrêt de la pagination, {count} albums récupérés")
                        break
                    else:
                        logger.error(f"❌ Erreur HTTP {e.response.status_code} page {page_num}: {e}")
                        logger.info(f"⚠️ Arrêt de la pagination à la page {page_num}, {count} albums récupérés")
                        break
                except requests.exceptions.RequestException as e:
                    logger.error(f"❌ Erreur requête page {page_num}: {e}")
                    logger.info(f"⚠️ Arrêt de la pagination à la page {page_num}, {count} albums récupérés")
                    break
                except Exception as e:
                    logger.error(f"❌ Erreur inattendue page {page_num}: {e}")
                    logger.info(f"⚠️ Arrêt de la pagination à la page {page_num}, {count} albums récupérés")
                    break
            
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
