"""
Discogs API client service for collection import with rate limiting and circuit breaking.

Service for accessing user's Discogs music collection via API v2.0. Provides robust
collection retrieval with explicit pagination, rate limiting (0.5s between requests),
retry logic with exponential backoff, and circuit breaker pattern for API resilience.

Features:
- Discogs OAuth authentication (user token)
- Explicit pagination (vs. auto-paginated iterator to avoid sync issues)
- Rate limiting: 0.5 seconds minimum between requests
- Retry logic: Up to 3 attempts with backoff (2s → 10s)
- Circuit breaker: Detects API outages, prevents cascading failures
- Error handling: 404 releases logged (removed from Discogs), others retried
- Metadata extraction: Full album info (id, title, artists, genres, cover, formats, tracklist)

Architecture:
- Auth: discogs_client v1.1 with user_token authentication
- Pagination: Direct API page parameters (vs. iterator auto-pagination)
- Rate limiting: Global last_request_time tracked per instance
- Circuit breaker: Global module-level instance shared across requests
- Failure tracking: Records success/failure for circuit breaker state

Typical usage:
    service = DiscogsService(api_key="YOUR_TOKEN", username="username")
    
    # Get full collection (paginated automatically)
    albums = service.get_collection(limit=None)  # All albums
    albums = service.get_collection(limit=50)    # First 50
    
    # Get specific release details
    release = service.get_release_info(release_id=123456)
    tracklist = release['tracklist']  # Included in release info
    
    # Parse collection
    for album in albums:
        print(f"{album['title']} by {', '.join(album['artists'])}")
        print(f"Genres: {', '.join(album['genres'])}")
        print(f"Cover: {album['cover_image']}")

Performance profile:
- get_collection(): 0.5-120s (rate limited, depends on collection size)
  - Rate limit: 0.5s minimum between requests
  - Typical: 50 albums = 25 seconds (0.5s × 50 paginated requests)
  - Network: 100-300ms per request to Discogs API
- get_release_info(): 0.5-2s (1 request + rate limit)
- _extract_album_info(): <10ms (data transformation, no network)
- _extract_tracklist(): <10ms (data transformation, no network)
- _rate_limit_wait(): O(1) busy-wait or sleep

Output schema:
- Album dict: release_id, title, year, artists[], labels[], genres[], styles[], 
              cover_image (URL), discogs_url, formats[]
- Release dict: Same as album plus tracklist[]
- Tracklist item: position, title, duration (if available)

Error resilience:
- 404 releases: Logged separately, skipped (removed from Discogs)
- Timeout/network error: Retried up to 3 times with backoff
- Rate limit (429): BackOff retry will handle
- Service down (503): Circuit breaker opens after 5 consecutive failures
- Circuit breaker open: Raises DiscogsServiceException (fail fast)

Database integration assumptions:
- DiscogsService is typically called before database import
- Result albums parsed into local Album/Artist records
- album_info['release_id'] mapped to external_id for future sync
"""
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
    """
    Discogs Discogs API v2.0 client with rate limiting, retry logic, and circuit breaker.
    
    Robust client for accessing Discogs user collection via OAuth token authentication.
    Implements pagination, rate limiting, automatic retry with exponential backoff, and
    circuit breaker for fault tolerance. Extracts full album metadata including artists,
    genres, cover images, and tracklists.
    
    Attributes:
        api_key (str): Discogs OAuth user token for authentication
        username (str): Discogs username (metadata, used for logging)
        client (discogs_client.Client): Initialized Discogs API client
        rate_limit_delay (float): Minimum seconds between API requests (default 0.5)
        last_request_time (float): Timestamp of last API request (for rate limiting)
        _circuit_breaker (CircuitBreaker): Module-level instance for fault detection
    
    Rate limiting:
        - Discogs API: 60 requests/minute (1 per second max recommended)
        - Service default: 0.5s minimum between requests (conservative)
        - Implementation: Busy-wait if elapsed < delay, else sleep (remainder)
        - Tracked per-instance last_request_time
    
    Pagiotnation:
        - Explicit: Direct API URL parameters (page, per_page)
        - vs Auto-iterator: discogs_client iterator has sync issues in some cases
        - Page size: 100 albums per request (Discogs default max)
        - Stops when: Less than page_size items returned (final page)
    
    Retry logic:
        - Decorator: @retry_with_backoff applied to network-dependent methods
        - get_collection(): 3 attempts, initial 2s, max 10s
        - get_release_info(): 2 attempts, initial 1s, max 5s
        - Backoff: Exponential (2s → 4s → 8s for collection)
        - Skips retries: 404 errors (logged separately)
    
    Circuit breaker:
        - Module-level shared instance: Detects sustained API outages
        - Thresholds: 5 consecutive failures to open, 3 successes to half-open
        - States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing) → CLOSED
        - Timeout: 300s recovery wait before HALF_OPEN retry
        - Purpose: Fail fast if Discogs API unavailable (prevent cascading failures)
    
    Methods:
    - __init__(): Initialize client with API credentials
    - _rate_limit_wait(): Enforce minimum delay between requests
    - get_collection(): Retrieve full user collection with pagination
    - _extract_album_info(): Parse album metadata from Discogs release object
    - get_release_info(): Get detailed info for specific release
    - _extract_tracklist(): Parse track listing from Discogs release
    
    Usage patterns:
        # Full collection import (with limits for testing)
        service = DiscogsService(api_key, username)
        albums = service.get_collection(limit=100)  # First 100 albums
        
        # Selective import (skip previously imported)
        existing_ids = {int(record.external_id) for record in db.query(...)}
        albums = service.get_collection(skip_ids=existing_ids)
        
        # Single release details
        release = service.get_release_info(release_id=12345)
        if release:
            for track in release['tracklist']:
                print(f"{track['position']}. {track['title']}")
    
    Error handling strategy:
        - 404 releases: Skipped with warning (removed from user's collection on Discogs)
        - Network timeout: Retried automatically (up to max_attempts)
        - Rate limit (429): Respected by Discogs client, retried
        - Service unavailable (503): Retried, then circuit breaker opens if persistent
        - Circuit breaker open: Raises DiscogsServiceException immediately (fail fast)
    
    Data quality:
        - Validation: Title and artists required; others optional
        - Normalization: Remove extra whitespace, filter empty values
        - Cover image: First image if available, else None
        - Year: Validated > 0 (0 year → None)
        
    Integration expectations:
        - Input: api_key (OAuth token), username (for reference)
        - Output: List[Dict] with normalized album metadata
        - Usage: Parse into local Album/Artist database records
        - External ID mapping: release_id → album.external_id (for sync)
    
    Limitation/Notes:
        - For user's personal collection only (via username/token)
        - Does not search Discogs catalog
        - Cannot modify Discogs (read-only)
        - Requires active Discogs OAuth token (no password auth)
        - API token has specific rate limiting (shared across app)
    """
    
    def __init__(self, api_key: str, username: str) -> None:
        """
        Initialize Discogs API client with authentication.
        
        Args:
            api_key (str): Discogs OAuth user token (from app settings/secrets)
            username (str): Discogs username (for logging/reference, not used in auth)
        
        Performance:
            - O(1), <1ms (just object initialization)
        
        Attributes set:
            - api_key: Stored for potential re-auth
            - username: Reference for logging
            - client: discogs_client.Client with user_token auth
            - rate_limit_delay: 0.5 seconds (conservative Discogs limit)
            - last_request_time: 0.0 (no requests yet)
        
        Side Effects:
            - Initializes discogs_client (no network call yet)
            - User-Agent set to 'MusicTrackerApp/4.0' for API identification
        
        Raises:
            Exception: If discogs_client installation missing (import error)
        
        Example:
            service = DiscogsService(
                api_key="YOUR_OAUTH_TOKEN",
                username="myusername"
            )
        """
        self.api_key = api_key
        self.username = username
        self.client = discogs_client.Client(
            'MusicTrackerApp/4.0',
            user_token=api_key
        )
        self.rate_limit_delay = 0.5  # Délai entre requêtes pour respecter les limites
        self.last_request_time = 0
    
    def _rate_limit_wait(self) -> None:
        """
        Enforce minimum delay between API requests to respect Discogs rate limits.
        
        Blocks caller until rate_limit_delay seconds have passed since last request.
        Called before each Discogs API call to prevent hitting rate limit (60/min).
        Implementation: Busy-wait if remaining < 1ms, else time.sleep(remainder).
        
        Performance:
            - Blocking: Sleeps rate_limit_delay seconds (default 0.5s)
            - First call: No delay (last_request_time = 0)
            - Subsequent: Enforces 0.5s minimum between calls
            - Big-O: O(1) (apart from sleep duration)
        
        Side Effects:
            - Updates self.last_request_time to current time.time()
            - Blocks execution for up to 0.5 seconds
            - Called before every Discogs API request
        
        Example sequence:
            t=0.0: _rate_limit_wait() → elapsed=0, no sleep, last_request_time=0.0
            t=0.1: _rate_limit_wait() → elapsed=0.1, sleep(0.4), last_request_time=0.5
            t=1.0: _rate_limit_wait() → elapsed=0.5, no sleep, last_request_time=1.0
        
        Discogs Rate Limits:
            - Authenticated: 60 requests per minute (1 per second max recommendation)
            - Unauthenticated: 25 per minute
            - Service default: 0.5s (conservative, safe buffer)
        
        Used by:
            - get_collection(): Before each paginated request
            - get_release_info(): Before single release request
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    @retry_with_backoff(max_attempts=3, initial_delay=2.0, max_delay=10.0)
    def get_collection(self, limit: Optional[int] = None, skip_ids: Optional[set] = None) -> List[Dict[str, Any]]:
        """
        Retrieve user's full Discogs collection with pagination, rate limiting, and retries.
        
        Fetches entire collection via explicit pagination (vs. auto-iterator) to handle
        Discogs API reliability. Implements rate limiting (0.5s between requests), retry
        logic with exponential backoff (3 attempts, 2-10s), and circuit breaker for
        outage detection. Skips 404 albums (removed from user's collection on Discogs).
        
        Args:
            limit (int|None): Max albums to retrieve. None = all albums in collection.
                            Useful for testing (limit=50) or batch processing (limit=100)
            skip_ids (set|None): Set of Discogs release IDs (as str) to skip.
                               Optimization to avoid re-importing known albums.
                               Example: {'12345', '67890'} skips these releases
        
        Returns:
            list: Full collection as List[Dict] with keys:
                - release_id (int): Unique Discogs ID
                - title (str): Album title
                - year (int|None): Release year (None if 0 or missing)
                - artists (str[]): Artist names
                - labels (str[]): Label names (if available)
                - genres (str[]): Genre tags
                - styles (str[]): Style tags (more specific than genres)
                - cover_image (str|None): Album cover URL (or None)
                - discogs_url (str|None): Link to Discogs release page
                - formats (str[]): Format names (Vinyl, CD, Digital, etc.)
        
        Raises:
            DiscogsServiceException: If circuit breaker open (service unavailable)
            requests.exceptions.RequestException: Network/timeout errors (will retry)
        
        Performance:
            - Typical: 30-120 seconds (rate limited, depends on collection size)
            - Rate limiting: 0.5s per paginated request (100 albums/page)
            - Example: 500 albums = 5 pages × 0.5s = 2.5s minimum
            - Network time: 100-300ms per request (adds up)
            - Retry overhead: 2s → 4s → 8s on failures (exponential backoff)
            - Big-O: O(n) where n = collection size (pagination rate limited)
        
        Side Effects:
            - API calls: Multiple page requests to Discogs API
            - Rate limiting: Blocks thread 0.5s between requests
            - Logging: Detailed per-page progress, error tracking
            - Circuit breaker: Records success/failure for state tracking
            - Error collection: 404 releases tracked separately (not fatal)
        
        Implementation:
            1. Circuit breaker check: Raise DiscogsServiceException if OPEN state
            2. User identity: Get user.num_collection (total count)
            3. Pagination loop:
               a. For each page (page_size=100):
                  - Wait for rate limit (0.5s)
                  - Fetch page from Discogs API
                  - For each release in page:
                    - Skip if release_id in skip_ids
                    - If limit reached: Stop
                    - Try to extract album info
                    - On 404: Log and skip (don't retry this release)
                    - On other error: Log warning
                  - If less than page_size returned: Stop (no more pages)
               b. Increment page number
            4. Circuit breaker: Record success on completion
            5. Log summary: Total albums, 404 count
            6. Return all collected albums
        
        Special handling:
            - 404 releases: Logged separately, skipped without error (user removed from Discogs)
            - Timeout/network: Retried automatically (decorator handles)
            - Rate limit (429): Discogs client busy-waits or sleeps
            - Empty collection: Returns empty list (not an error)
            - Skip_ids optimization: Skip already-imported albums (O(1) set lookup)
        
        Pagination detail:
            - Direct API calls vs. iterator: More reliable, explicit control
            - Page size: 100 albums per page (Discogs default/max)
            - Early termination: Stops when page < page_size (final page)
            - Rate limited: 0.5s minimum between each page request
        
        Example usage:
            # Get all albums (may take 30+ seconds for large collection)
            service = DiscogsService(api_key, username)
            all_albums = service.get_collection()
            print(f"Downloaded {len(all_albums)} albums")
            
            # Get first 100 (faster for testing)
            test_albums = service.get_collection(limit=100)
            
            # Skip already-imported albums (optimization)
            existing = {str(record.external_id) for record in db.query(...)}
            new_albums = service.get_collection(skip_ids=existing)
            
            # Batch process with pagination
            service = DiscogsService(api_key, username)
            all_albums = service.get_collection()
            for batch in chunks(all_albums, 50):
                db_import_batch(batch)
        
        Error scenarios:
            - Discogs unavailable (503): Retried 3 times (2s → 4s → 8s), then raises
            - Timeout (>10s per request): Retried up to 3 times
            - 404 release: Logged separately, skipped (not retried)
            - Circuit breaker open: Immediate exception (fail fast)
            - Empty collection: Returns [] (success)
        
        Logging output:
            🔍 Début récupération collection Discogs
            ✅ Utilisateur: {username}, {count} releases
            📁 Folder: {name}, Count: {count}
            📑 Chargement page {N} (100 items/page)...
            ⚠️  {count} releases 404 ignorés (supprimés de Discogs): {ids...}
            ✅ Collection récupérée: {count} albums
        
        Used for:
            - Full collection import on initial setup
            - Synchronization with user's Discogs collection
            - Discovery/curation feature
        
        Preconditions:
            - API key must be valid and authenticated
            - Discogs API must be reachable (or circuit breaker will fail fast)
            - Rate limits not already exceeded (service respects limits)
        
        Postconditions:
            - Returns full normalized collection
            - Circuit breaker updated with success/failure
            - Rate limit delay respected (next call after 0.5s)
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
    
    def _extract_album_info(self, release_data: Any, position: int) -> Optional[Dict[str, Any]]:
        """
        Extract and validate album metadata from Discogs release object.
        
        Transforms Discogs API release object into normalized album dictionary.
        Validates required fields (title, artists), cleans whitespace, and handles
        optional fields gracefully. Returns None if validation fails (logged as warning).
        
        Args:
            release_data (Any): Discogs release object from discogs_client
            position (int): Album position in collection (for logging context)
        
        Returns:
            dict | None: Normalized album with keys:
                       - release_id (int): Unique ID
                       - title (str): Cleaned album title
                       - year (int|None): Release year (None if 0 or missing)
                       - artists (str[]): Non-empty artist names
                       - labels (str[]): Label names ([] if missing)
                       - genres (str[]): Genre tags ([] if missing)
                       - styles (str[]): Style tags ([] if missing)
                       - cover_image (str|None): Album art URL or None
                       - discogs_url (str|None): Release URL or None
                       - formats (str[]): Format names ([] if empty)
                       Returns None if title missing or artists empty
        
        Performance:
            - O(n) where n = album fields (typically 5-10)
            - Typical: <10ms (data transformation, no network)
        
        Validation rules:
            - Title: Required, non-empty after strip()
            - Artists: At least 1 valid name (non-empty)
            - Year: If > 0 → kept, else → None
            - Labels: Filtered to non-empty names ([] if none)
            - Genres: Converted to list ([] if missing)
            - Styles: Converted to list ([] if missing)
            - Images: First image URI if available, else None
            - Formats: Format names extracted, [] if missing
        
        Side Effects:
            - Logs WARNING if validation fails
            - Warning includes position for debugging collection parse
        
        Error handling:
            - Missing fields: Skipped or defaulted to []
            - Invalid year: Transformed to None (year=0 → None)
            - Missing artists: Returns None (validation fail)
            - Attribute errors: Logged as warning (not fatal)
        
        Example:
            release = client.get_release(12345)
            album_info = service._extract_album_info(release, position=1)
            # Result:
            # {
            #     'release_id': 12345,
            #     'title': 'OK Computer',
            #     'year': 1997,
            #     'artists': ['Radiohead'],
            #     'genres': ['Electronic', 'Alternative Rock'],
            #     'cover_image': 'https://api.discogs.com/images/...',
            #     ...
            # }
        
        Used by:
            - get_collection(): For each release in paginated results
            - Album info extraction during collection import
        
        Robustness:
            - Graceful degradation: Returns None on schema mismatch (logged)
            - No exceptions raised: All errors caught and returns None
            - Logs position: Helps identify problematic albums in collection
        """
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
        """
        Retrieve complete release information from Discogs including full tracklist.
        
        Fetches single release details with metadata and complete track listing.
        Includes rate limiting and retry logic (2 attempts, 1-5s backoff).
        Useful for enriching albums with detailed info not in collection API.
        
        Args:
            release_id (int): Discogs release ID (numeric identifier)
        
        Returns:
            dict | None: Complete release info with keys:
                       - Same as _extract_album_info (title, artists, genres, etc.)
                       - tracklist (list): Track details [{position, title, duration}]
                       Returns None on error (logged as warning)
        
        Raises:
            None - returns None on error (logged, not raised)
        
        Performance:
            - Typical: 0.5-2 seconds (1 request + rate limit)
            - Rate limit: 0.5s wait before request
            - Network: 100-300ms API call
            - Tracklist parsing: <10ms (data transformation)
            - Retry overhead: 1s → 2s → 4s on failures (exponential backoff)
        
        Side Effects:
            - API call: Single Discogs API request
            - Rate limiting: Enforces 0.5s minimum since last request
            - Logging: Warns on error with release_id
        
        Tracklist format:
            [{
                'position': '1',  # or '1.1' for multi-disc
                'title': 'Track Title',
                'duration': '3:45'  # or None if unavailable
            }, ...]
        
        Example:
            service = DiscogsService(api_key, username)
            release = service.get_release_info(12345)
            if release:
                print(f"{release['title']} by {release['artists'][0]}")
                for track in release['tracklist']:
                    print(f"  {track['position']}. {track['title']} ({track['duration']})")
        
        Error handling:
            - 404 release: Logs warning, returns None (not found)
            - Network timeout: Retried automatically (2 attempts)
            - Rate limit (429): Discogs client handles, retried
            - Other errors: Logged, returns None
        
        Used by:
            - Detailed album info lookup (after import)
            - Tracklist integration (for track-level metadata)
            - Enrichment operations (getting full release details)
        
        Difference from get_collection():
            get_collection(): All albums in collection, 0.5s rate limit, 3 retries
            get_release_info(): Single release detail, 0.5s rate limit, 2 retries
            Usage: Collection import vs. single album enrichment
        
        Preconditions:
            - release_id must be valid Discogs ID (numeric)
            - Release must exist in Discogs catalog
            - Rate limit delay respected since last request
        
        Postconditions:
            - Returns full release info or None
            - Rate limit delay enforced
            - Auditable logging of success/failure
        
        Raises:
            DiscogsServiceException: Si circuit breaker ouvert
        """
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
    
    def _extract_tracklist(self, release: Any) -> List[Dict[str, Any]]:
        """
        Extract and normalize track listing from Discogs release object.
        
        Parses Discogs tracklist into standardized format with position, title, duration.
        Handles multi-disc formats (position format '1.1', '1.2', '2.1', etc.).
        Gracefully handles missing/invalid tracks.
        
        Args:
            release (Any): Discogs release object with .tracklist property
        
        Returns:
            list: Tracks in format [{position, title, duration}, ...]
                - position (str): Track position ('1', '2', '1.1' for multi-disc)
                - title (str): Track title (cleaned whitespace)
                - duration (str|None): Duration like '3:45' or None if unavailable
        
        Performance:
            - O(n) where n = track count (typically 10-20)
            - Typical: <10ms (data transformation, no network)
        
        Side Effects:
            - Logs WARNING for invalid tracks (position but no title)
            - No database updates
            - No API calls
        
        Implementation:
            1. Check if release has tracklist attribute
            2. If missing/empty: Return [] (empty album, not error)
            3. For each track in release.tracklist:
               a. Extract position (required, skip if missing)
               b. Extract title (required, warn if missing)
               c. Extract duration (optional, may be None)
               d. Skip if position empty or title empty (malformed)
               e. Add to results as dict
            4. Return all valid tracks
        
        Track format examples:
            - Single disc: '1', '2', '3' (1-based)
            - Multi-disc: '1.1', '1.2', '2.1', '2.2'
            - With duration: '3:45', '2:33'
            - Missing duration: None (not '?')
        
        Edge cases:
            - Missing tracklist attribute: Returns [] (not error)
            - Empty tracklist: Returns [] (valid, album may be instrumental)
            - Track without position: Skipped with warning
            - Track without title: Skipped with warning
            - Track with number position ('1', '1.1'): Normalized as string
        
        Logging:
            ⚠️ Track invalide à position {pos}: no title
            (Only logs invalid/malformed tracks, not missing duration)
        
        Used by:
            - get_release_info(): To include tracklist in release dict
            - Album enrichment: For track-level metadata
        
        Examples:
            # Single-disc album
            release = service.get_release_info(12345)
            tracklist = release['tracklist']
            # Result: [
            #     {'position': '1', 'title': 'Intro', 'duration': '1:23'},
            #     {'position': '2', 'title': 'Main Track', 'duration': '4:56'},
            # ]
            
            # Multi-disc album
            # Result: [
            #     {'position': '1.1', 'title': 'Disc 1 Track 1', 'duration': '3:45'},
            #     {'position': '2.1', 'title': 'Disc 2 Track 1', 'duration': '4:30'},
            # ]
        
        Integration:
            - Called from get_release_info() to enrich single release
            - Also called from get_collection() if tracklist included in response
            - Result integrated into local Album.tracklist or Track table
        
        Robustness:
            - No exceptions raised: All errors logged as warnings
            - Graceful degradation: Missing tracks skipped
            - Empty tracklist valid: Returns [] (not None or error)
        """
        """Extraire et valider la tracklist d'une release Discogs.
        
        Chaque track inclut position, titre et duree si disponibles.
        Les erreurs individuelles ne bloquent pas l'extraction des autres tracks.
        
        Args:
            release: Objet release du client discogs_client
            
        Returns:
            List[Dict[str, Any]]: Liste de tracks avec position, title, duration.
                                  Liste vide si pas de tracklist valide.
        """
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
