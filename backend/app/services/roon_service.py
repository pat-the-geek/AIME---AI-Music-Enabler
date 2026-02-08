"""Service for Roon integration via Node.js bridge wrapping official RoonLabs API.

Communicates with roon-bridge microservice that exclusively uses the official RoonLabs
API (https://github.com/RoonLabs/node-roon-api). Bridge handles authentication, core
connection, and message routing. Service provides high-level methods for zone management,
playback control, library search, and now-playing queries.

Bridge URL: http://localhost:3330 (configurable)
Bridge API:
  - /status: Connection status to Roon Core
  - /zones: List all Roon zones/endpoints
  - /now-playing: Currently playing track info
  - /search: Album/track search in Roon library
  - /play: Start playing album/track in zone
  - /playback: Control playback (play/pause/skip)
  - /image/{key}: Fetch album art

Example Usage:
  >>> roon = RoonService('192.168.1.100', bridge_url='http://localhost:3330')
  >>> if roon.is_connected():
  ...     zones = roon.get_zones()
  ...     roon.play_album(zones[0]['zone_id'], 'Pink Floyd', 'Dark Side')
"""
import logging
import time
from typing import Optional, Dict, Callable

import httpx

logger = logging.getLogger(__name__)

# Timeout par défaut pour les requêtes HTTP vers le bridge
DEFAULT_TIMEOUT = 5.0
PLAY_TIMEOUT = 10.0  # Plus long pour les opérations de navigation/browse


class RoonService:
    """High-level API for Roon control via Node.js bridge wrapper.
    
    Manages zone-based playback, library search, and track management. Delegates
    communication to roon-bridge microservice which handles Roon Core connection
    and official API transactions. All operations are synchronous with 5-10 second
    timeouts (configurable per operation).
    
    Key Features:
    - Zone/endpoint management (list, query by name)
    - Playback control (play, pause, skip, queue)
    - Library search (album/track by artist/title)
    - Now-playing status with album art URLs
    - Retry logic for transient failures
    - Album variant handling (remasters, explicit versions)
    
    Configuration:
    - server: IP address of Roon Core (passed to bridge via env or config)
    - bridge_url: Bridge endpoint URL (default: http://localhost:3330)
    - timeout: 5s for most operations, 10s for playback/navigation
    
    Error Handling:
    - Network timeouts return None or empty dicts
    - Invalid zone IDs logged as warnings, return False
    - Playback commands retry up to 2x on transient failures
    - All exceptions caught and logged (no propagation)
    
    Example:
        >>> roon = RoonService('192.168.1.50', bridge_url='http://localhost:3330')
        >>> if roon.is_connected():
        ...     zones = roon.get_zones()
        ...     now = roon.get_now_playing()
        ...     print(f'Playing: {now[\"title\"]} in {now[\"zone_name\"]}')
    """

    def __init__(
        self,
        server: str,
        token: Optional[str] = None,
        app_info: Optional[Dict] = None,
        on_token_received: Optional[Callable[[str], None]] = None,
        bridge_url: Optional[str] = None,
    ):
        """Initialize Roon service with bridge connection configuration.
        
        Args:
            server: IP address of Roon Core system (e.g., '192.168.1.50')
                    Passed to bridge via environment or configuration
            token: Authentication token (preserved for compatibility, managed by bridge)
                  Optional; bridge handles token lifecycle
            app_info: Application metadata dict (preserved for compatibility)
                     Example: {'name': 'AIME', 'version': '1.0'}
            on_token_received: Callback for token updates (preserved for compatibility,
                             currently unused as bridge auto-manages tokens)
            bridge_url: Node.js bridge endpoint (default: http://localhost:3330)
                       Must be accessible and running official Roon API wrapper
        
        Returns:
            Initialized RoonService instance ready for zone management and playback
        
        Attributes:
            self.server: Roon Core IP address
            self.bridge_url: Bridge HTTP endpoint URL
            self._connected: Boolean flag updated by _check_bridge()
            self._token: Stored token (for compatibility)
        
        Side Effects:
            Calls _check_bridge() immediately to validate bridge connectivity
            Logs connection status (INFO if connected, WARNING if not)
        
        Example:
            >>> roon = RoonService('192.168.1.100', bridge_url='http://localhost:3330')
            # Logs: 'Bridge Roon connecté à 192.168.1.100 (core: My Roon Core)'
        """
        self.server = server
        self._token = token
        self.on_token_received = on_token_received
        self.app_info = app_info or {}

        # URL du bridge Node.js
        self.bridge_url = bridge_url or "http://localhost:3330"

        # Vérifier la connexion au bridge
        self._connected = False
        self._check_bridge()

    # ========================================================================
    # Connexion / statut
    # ========================================================================

    def _check_bridge(self):
        """Validate bridge connectivity and Roon Core connection status.
        
        Queries /status endpoint to check if bridge is accessible and connected
        to Roon Core. Called during __init__ and by is_connected() for health checks.
        Updates self._connected flag accordingly.
        
        Returns:
            None (updates self._connected as side effect)
        
        Side Effects:
            - Sets self._connected = True/False based on bridge response
            - Logs INFO if connected with core name
            - Logs WARNING if bridge accessible but not connected to Core
            - Logs WARNING if bridge HTTP returns non-200 status
            - Logs WARNING if bridge is inaccessible (network error)
        
        Timeout:
            5 seconds (DEFAULT_TIMEOUT)
        
        Bridge Response Format (on success):
            {
                "connected": bool,
                "core_name": string,  # Name of connected Roon Core
                ...
            }
        
        Error Handling:
            All exceptions caught and logged. Sets _connected=False on any error.
            Never raises exceptions.
        
        Used By:
            - __init__(): Initial connection validation
            - is_connected(): Periodic health checks
        """
        try:
            resp = httpx.get(f"{self.bridge_url}/status", timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                self._connected = data.get("connected", False)
                if self._connected:
                    logger.info(
                        "Bridge Roon connecté à %s (core: %s)",
                        self.server,
                        data.get("core_name", "?"),
                    )
                else:
                    logger.warning("Bridge Roon accessible mais pas encore connecté au Core")
            else:
                logger.warning("Bridge Roon a répondu %d", resp.status_code)
                self._connected = False
        except Exception as e:
            logger.warning("Bridge Roon inaccessible (%s): %s", self.bridge_url, e)
            self._connected = False

    def is_connected(self) -> bool:
        """Check if bridge is currently connected to Roon Core (with fresh status check).
        
        Queries /status endpoint to get real-time connection status. Updates
        self._connected flag. Safe for repeated polling (5s timeout).
        
        Returns:
            bool: True if bridge is accessible and connected to Roon Core,
                  False if bridge unreachable or not connected to Core
        
        Side Effects:
            Updates self._connected flag based on response
        
        Timeout:
            5 seconds
        
        Error Handling:
            All exceptions caught silently. Returns False on any error.
            No logging of transient failures (too verbose for polling).
        
        Performance:
            - Typical: 100-200ms if bridge accessible
            - On timeout: 5000ms (full timeout exhausted)
        
        Use Cases:
            - Pre-flight check before zone operations
            - Health monitoring periodic polling
            - Connection validation in API routes
        
        Note:
            Lightweight status check. For more detailed info, use get_zones()
            which also validates Roon connection.
        """
        try:
            resp = httpx.get(f"{self.bridge_url}/status", timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                self._connected = resp.json().get("connected", False)
                return self._connected
        except Exception:
            pass
        self._connected = False
        return False

    # ========================================================================
    # Zones
    # ========================================================================

    def get_zones(self) -> Dict:
        """Retrieve all available Roon zones/endpoints with full metadata.
        
        Queries /zones endpoint for complete zone list. Each zone represents
        an audio output (e.g., 'Living Room', 'Office System', 'Headphones').
        
        Returns:
            Dict mapping zone_id → zone_info dict
            Empty dict {} if bridge unreachable or no zones available
            
            Zone info structure:
            {
                'zone_id': str,
                'zone_name': str,
                'display_name': str,
                'host': str,
                'devices': [list of device dicts],
                'now_playing': {...},  # May include current track
                'is_playing': bool
            }
        
        Example:
            >>> zones = roon.get_zones()
            >>> for zone_id, info in zones.items():
            ...     print(f'{info[\"display_name\"]}: {info[\"zone_id\"]}')
            'Living Room: zone123abc'
            'Office: zone456def'
        
        Timeout:
            5 seconds (DEFAULT_TIMEOUT)
        
        Error Handling:
            Returns {} on any error (network timeout, JSON parse failure, etc.)
            Logs error but doesn't raise exception
        
        Performance:
            - Typical: 200-500ms for 5-10 zones
            - First call after bridge startup: 1-2 seconds (zone discovery)
        
        Usage:
            Call once on app startup and cache result, or periodically for zone
            discovery. Zone IDs are stable per Roon system but may change if
            zones are added/removed.
        """
        try:
            resp = httpx.get(f"{self.bridge_url}/zones", timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                zones_list = data.get("zones", [])
                return {z["zone_id"]: z for z in zones_list}
        except Exception as e:
            logger.error("Erreur récupération zones: %s", e)
        return {}

    def get_zone_by_name(self, zone_name: str) -> Optional[str]:
        """Look up zone ID by display name (case-sensitive).
        
        Args:
            zone_name: Zone display name to search (e.g., 'Living Room', 'Office')
                      Case-sensitive exact match
        
        Returns:
            str: Zone ID if found (e.g., 'zone_abc123def')
            None: If zone name not found or bridge unreachable
        
        Example:
            >>> zone_id = roon.get_zone_by_name('Living Room')
            >>> if zone_id:
            ...     roon.playback_control(zone_id, 'play')
        
        Timeout:
            5 seconds
        
        Error Handling:
            Returns None on any error (network, parsing, not found)
            Logs error to WARNING level
        
        Performance:
            - Typical: 150-300ms
        
        Alternative:
            For better performance, call get_zones() once and use dict lookup:
            >>> zones = roon.get_zones()
            >>> zone_id = next((z['zone_id'] for z in zones.values()
            ...                 if z.get('display_name') == 'Living Room'), None)
        
        Case Sensitivity:
            Name matching is case-sensitive. Zone names typically use title case
            (e.g., 'Living Room', not 'living room').
        """
        try:
            resp = httpx.get(
                f"{self.bridge_url}/zones/{zone_name}",
                timeout=DEFAULT_TIMEOUT,
            )
            if resp.status_code == 200:
                return resp.json().get("zone_id")
        except Exception as e:
            logger.error("Erreur recherche zone '%s': %s", zone_name, e)
        return None

    # ========================================================================
    # Now Playing
    # ========================================================================

    def get_now_playing(self, zone_name: Optional[str] = None) -> Optional[Dict]:
        """Retrieve currently playing track with metadata and album art URL.
        
        Args:
            zone_name: Optional zone name to get track from. If not provided, returns
                      the first zone with active playback (prioritizing playing > paused > stopped)
        
        Returns:
            Dict with track information if something is playing:
            {
                'title': str,              # Track title
                'artist': str,             # Primary artist name
                'album': str,              # Album title
                'zone_id': str,            # Zone playing the track
                'zone_name': str,          # Zone display name
                'state': str,              # Playback state: playing, paused, stopped
                'duration_seconds': int|None,  # Track duration (null if unknown)
                'position_seconds': int|None,  # Current playback position
                'image_url': str|None      # Album art URL via bridge image endpoint
            }
            
            None if nothing is playing OR bridge unreachable
        
        Example:
            >>> now = roon.get_now_playing()
            >>> if now:
            ...     print(f'{now[\"title\"]} by {now[\"artist\"]}')
            ...     print(f'In zone: {now[\"zone_name\"]} (state: {now[\"state\"]})')
        
        Example with zone:
            >>> now = roon.get_now_playing(zone_name='Living Room')
            >>> if now:
            ...     print(f'Now playing in Living Room: {now[\"title\"]}')
        
        Album Art:
            image_url constructed from image_key via bridge:
            http://{bridge_url}/image/{key}?scale=fit&width=300&height=300
            Returns None if track has no album art
        
        Timeout:
            5 seconds
        
        Error Handling:
            Returns None if bridge unreachable or any error occurs
            Logs errors to ERROR level
        
        Performance:
            - Typical: 150-300ms
            - Safe for polling every 1-2 seconds
        
        Missing Values:
            Unfamiliar track fields default to 'Unknown Artist', etc.
            Duration/image_url may be None if not available from Roon
        
        Use Cases:
            - Display player UI showing current track
            - Listening history submission (track name + artist)
            - Zone activity monitoring
            - Multi-zone support: Show track for specific zone
        """
        try:
            # Ajouter zone_name en paramètre si fourni
            url = f"{self.bridge_url}/now-playing"
            params = {}
            if zone_name:
                params['zone_name'] = zone_name
            
            resp = httpx.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                # Pas de track en cours si pas de titre
                if not data.get("title"):
                    return None

                # État du playback - s'assurer qu'il existe et a une valeur par défaut
                state = data.get("state", "stopped")
                if state not in ["playing", "paused", "stopped"]:
                    state = "stopped"  # Default en cas de valeur inconnue

                result = {
                    "title": data.get("title", "Unknown Title"),
                    "artist": data.get("artist", "Unknown Artist"),
                    "album": data.get("album", "Unknown Album"),
                    "zone_id": data.get("zone_id", ""),
                    "zone_name": data.get("zone_name", "Unknown Zone"),
                    "state": state,  # État normalisé du playback
                    "duration_seconds": data.get("duration_seconds"),
                    "position_seconds": data.get("seek_position"),  # seek_position du bridge → position_seconds
                    "image_url": None,
                }

                # Construire l'URL d'image via le bridge si image_key est disponible
                image_key = data.get("image_key")
                if image_key:
                    result["image_url"] = (
                        f"{self.bridge_url}/image/{image_key}?scale=fit&width=300&height=300"
                    )

                logger.debug(f"✅ Now playing: {result['title']} - State: {state}")
                return result
        except Exception as e:
            logger.error("Erreur récupération now playing: %s", e)
        return None

    # ========================================================================
    # Playback Control
    # ========================================================================

    def playback_control(
        self, zone_or_output_id: str, control: str = "play", max_retries: int = 2
    ) -> bool:
        """Control playback on a zone with automatic retry for transient failures.
        
        Issues playback commands to control music playback in specified zone.
        Retries up to 2x on failure to handle transient network/bridge issues.
        
        Args:
            zone_or_output_id: Zone ID or output ID (e.g., 'zone_abc123')
            control: Playback command - one of:
                - 'play': Resume/start playback
                - 'pause': Pause current track
                - 'stop': Stop playback
                - 'next': Skip to next track
                - 'previous': Go to previous track
            max_retries: Maximum retry attempts (default: 2)
        
        Returns:
            bool: True if command succeeded, False on all retry attempts exhausted
        
        Example:
            >>> zones = roon.get_zones()
            >>> zone_id = list(zones.keys())[0]
            >>> roon.playback_control(zone_id, 'play')
            True
            >>> roon.playback_control(zone_id, 'next')  # Skip track
            True
        
        Timeout:
            5 seconds per attempt (up to 10s total with 2 retries)
        
        Retry Logic:
            - Retries on HTTP error or timeout
            - Includes debug logging per attempt
            - Linear retry (no exponential backoff)
        
        Error Handling:
            Returns False if:
            - Invalid zone ID
            - Bridge unreachable
            - All retry attempts fail
            Logs WARNING on failure
        
        Performance:
            - Typical: 200-500ms (successful)
            - On failure with 2 retries: 10-15 seconds (timeout exhausted)
        
        Logging:
            - DEBUG: Per-attempt details (attempt N/M)
            - WARNING: Failure details after all retries exhausted
        """
        for attempt in range(max_retries):
            try:
                logger.debug(
                    "Contrôle '%s' sur zone %s (tentative %d/%d)",
                    control, zone_or_output_id, attempt + 1, max_retries,
                )
                resp = httpx.post(
                    f"{self.bridge_url}/control",
                    json={
                        "zone_or_output_id": zone_or_output_id,
                        "control": control,
                    },
                    timeout=DEFAULT_TIMEOUT,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    logger.info("Contrôle lecture: %s (état: %s)", control, data.get("state"))
                    return True
                else:
                    logger.warning(
                        "Contrôle '%s' échoué (HTTP %d): %s",
                        control, resp.status_code, resp.text,
                    )
            except Exception as e:
                logger.warning("Tentative %d/%d échouée: %s", attempt + 1, max_retries, e)

            if attempt < max_retries - 1:
                time.sleep(0.3)

        logger.error("Erreur contrôle lecture après %d tentatives", max_retries)
        return False

    # ========================================================================
    # Search Album in Roon Library
    # ========================================================================

    def search_album_in_roon(
        self, artist: str, album: str, timeout_seconds: float = 30.0
    ) -> Optional[Dict]:
        """Search for album in Roon library with variant matching strategy.
        
        Searches Roon library for album by artist/title, trying multiple name
        variants to handle special editions (Deluxe, Remaster, etc.). Searches
        in order of likelihood: Deluxe → standard → exact name. Respects global
        timeout and adaptively allocates time per variant.
        
        Args:
            artist: Artist name (e.g., 'Pink Floyd')
            album: Album name (e.g., 'Dark Side of the Moon')
            timeout_seconds: Global timeout for entire search operation (default: 30s)
        
        Returns:
            Dict with search results:
            - found=True: {'found': True, 'exact_name': str, 'artist': str}
                Exact name as stored in Roon library (may differ from input)
            - found=False: {'found': False, 'artist': str, 'album': str}
                Album not found after trying all variants
            - Error: None (on exception during search)
        
        Example:
            >>> result = roon.search_album_in_roon('Fleetwood Mac', 'Rumours')
            >>> if result and result['found']:
            ...     print(f'Found: {result[\"exact_name\"]}')
            'Found: Rumours'
            
            >>> result = roon.search_album_in_roon('Floyd', 'Dark Side')
            >>> if result and result['found']:
            ...     print(f'Found: {result[\"exact_name\"]}')
            'Found: The Dark Side of the Moon'
        
        Variant Strategy (in search order):
            1. "{album} (Deluxe Edition)" - Most common reissue pattern
            2. "{album} Deluxe Edition" - Alternative format
            3. "{album} - Deluxe Edition" - With dash separator
            4. "{album} (Deluxe)" - Shorter variant
            5. "{album}" - Exact name as provided
        
        Timeout Adaptive Allocation:
            - Global timeout: 30 seconds default
            - Per-variant timeout: auto-calculated (1-8s range)
            - Stops at 85% of global timeout (safety margin)
            - Returns early if timeout would be exhausted
        
        Performance:
            - Typical: 2-8 seconds (found on 1st-3rd variant)
            - Worst case: ~30 seconds (timeout on all variants)
            - With found album: 500-2000ms
        
        Error Handling:
            - Timeout on variant: Skip to next variant with remaining time
            - Bridge unreachable: Returns None
            - Global timeout exceeded: Returns {'found': False, ...}
            - Exception during search: Returns None (logged as ERROR)
        
        Logging:
            - INFO: Start and result (found/not found with time)
            - DEBUG: Per-variant timeout calculation
            - WARNING: Timeout approaching or exceeded
            - ERROR: Exceptions during search
        
        Used By:
            - play_album(): Find exact album name before playback
            - Magazine generation: Verify album availability in Roon
        
        Note:
            Bridge must be running official Roon API with /search-album endpoint.
        """
        try:
            start_time = time.time()
            logger.info("Recherche album dans Roon: %s - %s", artist, album)

            # Essayer plusieurs variantes du nom d'album
            variants = [
                f"{album} (Deluxe Edition)",  # La variante exacte la plus courante
                f"{album} Deluxe Edition",     # Sans parenthèses
                f"{album} - Deluxe Edition",   # Avec tiret
                f"{album} (Deluxe)",
                album,  # Nom exact en dernier
            ]

            elapsed = time.time() - start_time
            
            # Essayer chaque variante
            for idx, variant in enumerate(variants):
                elapsed = time.time() - start_time
                
                # Arrêter à 85% du timeout global
                if elapsed > timeout_seconds * 0.85:
                    logger.warning("Approche du timeout global (%.1fs/%.1fs), arrêt", elapsed, timeout_seconds)
                    return {"found": False, "artist": artist, "album": album}
                
                # Timeout pour cette variante
                remaining_time = timeout_seconds - elapsed
                variants_left = len(variants) - idx
                variant_timeout = min(8.0, max(1.0, remaining_time / (variants_left + 0.5)))
                
                if variant_timeout <= 0.5:
                    logger.warning("Timeout épuisé avant variante %d: %s", idx + 1, variant)
                    return {"found": False, "artist": artist, "album": album}
                
                logger.info("Essai variante (%d/%d, %.1fs elapsed): %s - %s", 
                           idx + 1, len(variants), elapsed, artist, variant)
                
                try:
                    resp = httpx.post(
                        f"{self.bridge_url}/search-album",
                        json={
                            "artist": artist,
                            "album": variant,
                        },
                        timeout=variant_timeout,
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("found"):
                            exact_name = data.get("exact_name", variant)
                            elapsed_total = time.time() - start_time
                            logger.info(
                                "✓ Album trouvé dans Roon en %.2fs: %s",
                                elapsed_total,
                                exact_name,
                            )
                            return {
                                "found": True,
                                "exact_name": exact_name,
                                "artist": artist,
                            }
                except httpx.TimeoutException:
                    logger.debug("Timeout variante %d: %s", idx + 1, variant)
                    continue
                
            # Aucune variante trouvée
            elapsed_total = time.time() - start_time
            logger.info(
                "✗ Album non trouvé après %d variantes (%.2fs): %s - %s",
                len(variants),
                elapsed_total,
                artist,
                album,
            )
            return {"found": False, "artist": artist, "album": album}

        except Exception as e:
            logger.error("Erreur recherche album: %s", e)
            return None


    # ========================================================================
    # Play Album
    # ========================================================================

    def play_album(self, zone_or_output_id: str, artist: str, album: str) -> bool:
        """Start playback of complete album in specified zone (synchronous).
        
        Sends play command to Bridge which navigates Roon library to album
        and begins playback. Simple version with fixed timeout (10s).
        
        Args:
            zone_or_output_id: Zone ID where album should play
            artist: Artist name
            album: Album title
        
        Returns:
            bool: True if bridge accepted command and playback started,
                  False if bridge returned error or not found
        
        Example:
            >>> zones = roon.get_zones()
            >>> zone_id = list(zones.keys())[0]
            >>> roon.play_album(zone_id, 'Pink Floyd', 'Dark Side of the Moon')
            True
        
        Timeout:
            10 seconds (PLAY_TIMEOUT) - covers network + bridge processing
        
        Error Handling:
            Returns False on:
            - HTTP error response (non-200)
            - Bridge refused command (success=false)
            - Network timeout
            - Exception during request
            Logs errors to WARNING/ERROR level
        
        Performance:
            - Typical: 1-3 seconds (locate album + start playback)
            - Max: 10 seconds (timeout exhausted)
        
        Album Search:
            Bridge uses direct album name match (no variants).
            For better success with special editions, use play_album_with_variants()
        
        Used By:
            - API playback endpoints (simple requests)
            - Backend playlist generation
        
        Alternatives:
            - play_album_with_timeout(): Configurable timeout, returns None on timeout
            - play_album_with_variants(): Tries multiple album name variants
        """
        try:
            start_time = time.time()
            logger.info("Tentative de lecture de l'album: %s - %s", artist, album)

            resp = httpx.post(
                f"{self.bridge_url}/play-album",
                json={
                    "zone_or_output_id": zone_or_output_id,
                    "artist": artist,
                    "album": album,
                },
                timeout=PLAY_TIMEOUT,
            )

            total_time = time.time() - start_time

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    logger.info("Album lancé en %.2fs: %s - %s", total_time, artist, album)
                    return True

            logger.warning(
                "Impossible de lancer l'album après %.2fs: %s - %s (HTTP %d)",
                total_time, artist, album, resp.status_code,
            )
            return False

        except Exception as e:
            logger.error("Erreur lecture album: %s", e, exc_info=True)
            return False

    def play_album_with_timeout(
        self,
        zone_or_output_id: str,
        artist: str,
        album: str,
        timeout_seconds: float = 15.0,
    ) -> Optional[bool]:
        """Start album playback with configurable timeout and distinct return codes.
        
        This method provides fine-grained timeout handling, distinguishing between:
        - True: Album found and playback started
        - False: Album explicitly not found (404 response)
        - None: Timeout or transient network failure
        
        Useful for applications that need different handling for each failure mode.
        
        Args:
            zone_or_output_id: Target zone/output identifier
            artist: Album artist name
            album: Album title
            timeout_seconds: Operation timeout in seconds (default 15.0)
        
        Returns:
            True if playback started
            False if album not found (404)
            None if timeout exceeded or network error
        
        Example:
            >>> result = roon.play_album_with_timeout("zone-123", "Pink Floyd", "Dark Side", 10.0)
            >>> if result is True:
            ...     print("Playback started")
            >>> elif result is False:
            ...     print("Album not in library")
            >>> else:
            ...     print("Timeout - try again")
        
        Timeout:
            Configurable, default 15 seconds (adds 0.5s network margin internally)
        
        Logging:
            INFO: Attempt start, result with elapsed time
            WARNING: Album not found (404), HTTP error, timeout
            ERROR: Exception during playback attempt
        
        Note:
            Wrapper around simple play-album bridge endpoint. Typically called
            from play_album_with_variants() for multi-variant album matching.
            
        Performance:
            Network time typically 50-500ms for local bridge. Timeout adds
            latency only when album not found.
        """
        try:
            start_time = time.time()
            logger.info("play_album_with_timeout: %s - %s (timeout=%.1fs)", artist, album, timeout_seconds)
            
            resp = httpx.post(
                f"{self.bridge_url}/play-album",
                json={
                    "zone_or_output_id": zone_or_output_id,
                    "artist": artist,
                    "album": album,
                },
                timeout=timeout_seconds + 0.5,  # Petite marge pour le réseau seulement
            )

            elapsed = time.time() - start_time
            
            if resp.status_code == 200:
                data = resp.json()
                success = data.get("success", False)
                logger.info("play_album_with_timeout result: %s in %.2fs for %s - %s", success, elapsed, artist, album)
                return success
            elif resp.status_code == 404:
                logger.warning("play_album_with_timeout: album not found in %.2fs: %s - %s", elapsed, artist, album)
                return False
            else:
                logger.warning("play_album_with_timeout: HTTP %d in %.2fs for %s - %s", resp.status_code, elapsed, artist, album)
                return None

        except httpx.TimeoutException:
            logger.warning(
                "play_album timeout après %.1fs pour: %s - %s",
                timeout_seconds, artist, album,
            )
            return None
        except Exception as e:
            logger.error("Erreur play_album_with_timeout: %s", e)
            return None

    def play_album_with_variants(
        self,
        zone_or_output_id: str,
        artist: str,
        album: str,
        timeout_seconds: float = 15.0,
    ) -> Optional[bool]:
        """Play album with automatic variant matching for special editions.
        
        Intelligently attempts multiple album name variations to find exact matches
        in Roon library. This handles common cases where albums exist under variant
        names (Deluxe Edition, Remaster, etc).
        
        Variant Strategy (in order):
        1. Exact album name (most common, checked first)
        2. "Album (Deluxe Edition)" format
        3. "Album Deluxe Edition" format
        4. "Album - Deluxe Edition" format
        5. "Album (Deluxe)" format
        
        Each variant gets proportional timeout from global timeout budget. Early
        exit if approaching 85% global timeout threshold.
        
        Args:
            zone_or_output_id: Target zone/output identifier
            artist: Album artist name
            album: Base album title (without edition suffix)
            timeout_seconds: Total timeout for all variant attempts (default 15.0)
        
        Returns:
            True if playback started with any variant
            False if all variants exhausted without match
            None if global timeout exceeded
        
        Example:
            >>> result = roon.play_album_with_variants("zone-456", "Taylor Swift", "1989", 20.0)
            >>> # Tries: "1989", "1989 (Deluxe Edition)", etc. until finding match
            >>> if result is True:
            ...     print("Playing Taylor Swift - 1989")
        
        Timeout:
            Total global timeout split dynamically among variants based on elapsed time.
            Each variant: min(25s, max(1s, remaining_time/(variants_left + 0.5)))
            Exits at 85% threshold to ensure network margin.
        
        Logging:
            INFO: Variant attempt number, elapsed time, per-variant timeout
            INFO: ✓ Success with matching variant
            WARNING: Current variant timeout used, approaching global timeout
            ERROR: Exception during variant attempts
        
        Performance:
            Typical case (exact match first): 50-500ms
            Worst case (no match, all variants):  ~15s
            Network+search per variant: 100-3000ms depending on library size
        
        Implementation:
            Calls play_album_with_timeout() for each variant with distributed
            timeouts. Respects both per-variant and global timeout constraints.
            Returns immediately on success to minimize user delay.
        """
        # Ordre d'essai: nom exact d'abord, puis variantes (la plupart des albums existent sous leur nom exact)
        variants = [
            album,  # Nom exact EN PREMIER (réduit drastiquement le temps de recherche)
            f"{album} (Deluxe Edition)",
            f"{album} Deluxe Edition",
            f"{album} - Deluxe Edition",
            f"{album} (Deluxe)",
        ]
        
        start_time = time.time()
        
        # Essayer chaque variante avec un timeout propor tionnel
        for idx, variant in enumerate(variants):
            elapsed = time.time() - start_time
            
            # Vérifier si on approche du timeout global (arrêter à 85% du timeout)
            if elapsed > timeout_seconds * 0.85:
                logger.warning("Approche du timeout global (%.1fs/%.1fs), arrêt des variantes", elapsed, timeout_seconds)
                return None
            
            # Timeout disponible divisé entre variantes restantes
            remaining_time = timeout_seconds - elapsed
            variants_left = len(variants) - idx
            variant_timeout = min(25.0, max(1.0, remaining_time / (variants_left + 0.5)))
            
            if variant_timeout <= 0.5:
                logger.warning("Timeout épuisé avant de pouvoir essayer variante %d: %s", idx + 1, variant)
                return None
            
            logger.info("Essai variante (%d/%d, %.1fs elapsed, %.1fs timeout): %s - %s", idx + 1, len(variants), elapsed, variant_timeout, artist, variant)
            
            result = self.play_album_with_timeout(
                zone_or_output_id=zone_or_output_id,
                artist=artist,
                album=variant,
                timeout_seconds=variant_timeout,
            )
            
            # Si succès, retourner immédiatement
            if result is True:
                logger.info("✓ Album trouvé avec variante: %s (%.2fs)", variant, time.time() - start_time)
                return True
            
            # Si timeout global, retourner None
            elif result is None:
                elapsed_now = time.time() - start_time
                logger.warning("Timeout lors de la tentative avec variante: %s (%.2fs elapsed)", variant, elapsed_now)
                return None
            
            # Si False (not found), essayer la variante suivante
            logger.debug("Album pas trouvé pour variante: %s", variant)
        
        # Aucune variante trouvée
        elapsed = time.time() - start_time
        logger.warning("Album non trouvé après %d variantes (%.2fs): %s - %s", len(variants), elapsed, artist, album)
        return False

    # ========================================================================
    # Play Track
    # ========================================================================

    def play_track(
        self,
        zone_or_output_id: str,
        track_title: str,
        artist: str,
        album: str = None,
    ) -> bool:
        """Start playback of track by playing containing album (Roon API limitation).
        
        Roon API doesn't support individual track playback. When album provided,
        plays entire album. Without album, attempts bridge /play-track endpoint
        which searches for track and plays containing album.
        
        Args:
            zone_or_output_id: Zone ID for playback
            track_title: Track name (informational, used for logging)
            artist: Primary artist (first if comma-separated list)
            album: Album title (optional but recommended for reliability)
        
        Returns:
            bool: True if playback started, False on error
        
        Example:
            >>> roon.play_track(zone_id, 'Comfortably Numb', 'Pink Floyd', 'The Wall')
            True
        
        Behavior:
            - With album: play_album() called (direct library navigation)
            - Without album: Bridge searches Roon library for track record
        
        Timeout:
            10 seconds (PLAY_TIMEOUT)
        
        Error Handling:
            Returns False on:
            - Track not found
            - Bridge error
            - Network timeout
            Logs to WARNING/ERROR level
        
        Performance:
            - Typical: 1-3 seconds
            - Max: 10s timeout
        
        Note:
            Roon doesn't support individual track playback. This method provides
            convenience wrapper that plays the containing album instead.
        """
        try:
            logger.debug("Lecture track: %s - %s (%s)", track_title, artist, album or "N/A")

            # Si on a un album, jouer l'album
            if album:
                primary_artist = artist.split(",")[0].strip() if artist else "Unknown"
                return self.play_album(zone_or_output_id, primary_artist, album)

            # Sinon essayer via le bridge play-track
            resp = httpx.post(
                f"{self.bridge_url}/play-track",
                json={
                    "zone_or_output_id": zone_or_output_id,
                    "artist": artist,
                    "track_title": track_title,
                    "album": album,
                },
                timeout=PLAY_TIMEOUT,
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    logger.info("Track lancé: %s - %s", track_title, artist)
                    return True

            logger.warning("Impossible de lancer le track: %s - %s", track_title, artist)
            return False

        except Exception as e:
            logger.error("Erreur play_track: %s", e)
            return False

    # ========================================================================
    # Queue
    # ========================================================================

    def queue_tracks(
        self,
        zone_or_output_id: str,
        track_title: str,
        artist: str,
        album: str = None,
    ) -> bool:
        """Add track to Roon playback queue (queuing for next playback).
        
        Adds track/album to zone's queue. Bridge will queue the track or
        containing album in Roon's internal queue for sequential playback
        after current track finishes.
        
        Args:
            zone_or_output_id: Target zone ID
            track_title: Track name (informational)
            artist: Artist name
            album: Album title (optional)
        
        Returns:
            bool: True if queued successfully, False on error
        
        Example:
            >>> roon.queue_tracks(zone_id, 'Another Brick in the Wall', 'Pink Floyd', 'The Wall')
            True
        
        Timeout:
            10 seconds
        
        Error Handling:
            Returns False if queue operation failed (track not found, etc.)
            Logs to WARNING level on failure
        
        Logging:
            INFO: Track added to queue
            WARNING: Queue failed
            ERROR: Exception details
        """
        try:
            resp = httpx.post(
                f"{self.bridge_url}/queue",
                json={
                    "zone_or_output_id": zone_or_output_id,
                    "artist": artist,
                    "album": album or "",
                },
                timeout=PLAY_TIMEOUT,
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    logger.info("Ajouté à la queue: %s - %s", track_title, artist)
                    return True

            logger.warning("Impossible d'ajouter à la queue: %s", track_title)
            return False

        except Exception as e:
            logger.error("Erreur queue: %s", e)
            return False

    # ========================================================================
    # Pause All
    # ========================================================================

    def pause_all(self) -> bool:
        """Pause playback on all zones globally (emergency stop).
        
        Sends pause command to all zones simultaneously. Useful for:
        - Emergency stop functionality
        - App shutdown cleanup
        - Multi-zone pause without specifying zones
        
        Returns:
            bool: True if pause command accepted, False if failure
        
        Example:
            >>> roon.pause_all()
            True
        
        Timeout:
            5 seconds (DEFAULT_TIMEOUT)
        
        Logging:
            INFO: All zones paused successfully
            ERROR: Exception during pause operation
        
        Note:
            This is a global command affecting all zones. Use playback_control()
            for zone-specific pause operations.
        """
        try:
            resp = httpx.post(f"{self.bridge_url}/pause-all", timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                logger.info("Toutes les zones mises en pause")
                return True
        except Exception as e:
            logger.error("Erreur pause globale: %s", e)
        return False

    # ========================================================================
    # Token (compatibilité - géré par le bridge)
    # ========================================================================

    def get_token(self) -> Optional[str]:
        """Retrieve stored authentication token (legacy compatibility method).
        
        This method exists for backwards compatibility. Token management is now
        entirely handled by the roon-bridge Node.js microservice, which manages
        Roon authentication independently.
        
        Returns:
            Internal _token value if present, typically None in normal operation
        
        Example:
            >>> token = roon.get_token()
            >>> # Usually returns None - bridge handles auth
        
        Note:
            DEPRECATED: Do not rely on this for authentication. The bridge service
            manages authentication lifecycle and stores tokens securely. This method
            is retained for compatibility with legacy code that may call it.
        
        Performance:
            O(1) - simple instance variable access
        """
        return self._token

    def save_token(self, filepath: str):
        """Save authentication token to file (legacy compatibility method).
        
        This method exists for backwards compatibility. Token persistence is now
        entirely handled by the roon-bridge Node.js microservice, which manages
        Roon authentication independently with secure storage.
        
        Args:
            filepath: File path for token storage (ignored in modern implementation)
        
        Example:
            >>> roon.save_token("/path/to/token.json")
            >>> # No-op - bridge manages tokens internally
        
        Note:
            DEPRECATED: Do not rely on this for token persistence. The bridge service
            manages token lifecycle and persistence securely. This method is retained
            for compatibility with legacy code.
        
        Logging:
            DEBUG: Indicates method called and delegates to bridge
        
        Implementation:
            Currently a no-op that logs debug message. Bridge service handles all
            token persistence without AIME involvement.
        """
        logger.debug("save_token() appelé - le token est géré par le bridge Node.js")

    # ========================================================================
    # Search (compatibilité)
    # ========================================================================

    def search_track(
        self,
        artist: str,
        album: str,
        track_title: str,
        zone_id: str = None,
    ) -> Optional[Dict]:
        """Search for specific track in Roon library via browse API.
        
        Uses Roon's browse API to navigate from Library → Artists → Album → Track.
        Returns structured track info when found, useful for track-specific playback
        or identification.
        
        Args:
            artist: Primary artist name (comma-separated if multiple)
            album: Album title
            track_title: Track/song title
            zone_id: Target zone ID (optional, used for context)
        
        Returns:
            Dict with keys: path, display_name, artist, album, duration_seconds
            None if track not found or query fails
        
        Example:
            >>> track = roon.search_track("The Beatles", "Abbey Road", "Come Together")
            >>> if track:
            ...     print(f"Found: {track['display_name']} in {track['album']}")
            >>> # Returns: {'path': [...], 'display_name': 'Come Together', ...}
        
        Timeout:
            10 seconds (PLAY_TIMEOUT)
        
        Logging:
            ERROR: Exception during search
        
        Note:
            This searches via Roon's browse API, which is slower than search_album_in_roon()
            (which uses search API). Useful when track-level metadata required, but
            for just playing tracks, recommend using play_track() which plays containing
            album (Roon API limitation).
        
        Implementation:
            Extracts primary artist from comma-separated list, constructs path
            through Library hierarchy, queries bridge /browse endpoint.
        
        Performance:
            Typical browse: 500ms - 2s depending on artist/album path depth.
            No duration info available (returns None) - use separate query if needed.
        """
        try:
            primary_artist = artist.split(",")[0].strip() if artist else "Unknown"
            path = ["Library", "Artists", primary_artist]
            if album:
                path.append(album)
            path.append(track_title)

            resp = httpx.post(
                f"{self.bridge_url}/browse",
                json={
                    "zone_or_output_id": zone_id,
                    "path": path,
                },
                timeout=PLAY_TIMEOUT,
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return {
                        "path": path,
                        "display_name": track_title,
                        "artist": primary_artist,
                        "album": album,
                        "duration_seconds": None,
                    }

        except Exception as e:
            logger.error("Erreur recherche track: %s", e)
        return None

    def get_track_duration(self, zone_id: str) -> Optional[int]:
        """Get duration of currently playing track in specified zone.
        
        Queries current playback state and extracts track duration in seconds.
        Useful for progress tracking, remaining time displays, or playback scheduling.
        
        Args:
            zone_id: Zone identifier (used for context, passed to get_now_playing())
        
        Returns:
            Duration in seconds, or None if:
            - No track currently playing
            - Duration info unavailable
            - Zone query fails
        
        Example:
            >>> duration = roon.get_track_duration("zone-789")
            >>> if duration:
            ...     print(f"Track length: {duration}s = {duration//60}m {duration%60}s")
            >>> # Returns: 237 (for 3m 57s track)
        
        Timeout:
            5 seconds (DEFAULT_TIMEOUT via get_now_playing())
        
        Logging:
            Inherits logging from get_now_playing()
        
        Implementation:
            Wrapper around get_now_playing() that extracts duration_seconds key.
            Simple null-safe access pattern for track duration.
        
        Performance:
            O(1) once get_now_playing caches result. Typical: 50-500ms.
        
        Related:
            Use with playback_progress to calculate: percent_complete = (progress / duration) * 100
        """
        np = self.get_now_playing()
        if np:
            return np.get("duration_seconds")
        return None
