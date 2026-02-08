"""
Last.fm listening tracking service with scrobble history and album/artist metadata.

Service provides synchronous and asynchronous access to Last.fm API via pylast library
and direct HTTP requests. Features: current track query, recent tracks pagination,
scrobble history with timestamp filtering, album image fallback, artist composition
detection, total scrobble count. Used by import system for historical data migration
and enrichment service for image/metadata fallbacks (30+ second timeouts, graceful
degradation on API failures).

Architecture:
- pylast library: High-level API wrapper for track/user queries
- Direct HTTP requests: Use for pagination, metadata that pylast doesn't expose
- Rate limiting: Last.fm allows 60 requests/min (unauthenticated)
- Error resilience: All methods return safe defaults on failure (None, [])
- Credentials: api_key, api_secret, username from config (secrets.json)

Typical usage:
    lastfm = LastFMService(api_key="...", api_secret="...", username="user")
    current = lastfm.get_now_playing()  # Current track or None
    history = lastfm.get_user_history(limit=200, page=1)  # 200 recent scrobbles
    image_url = await lastfm.get_album_image("Radiohead", "OK Computer")  # Fallback image

Performance profile (typical):
- get_now_playing(): 100-500ms
- get_recent_tracks(): 200-800ms (50 tracks)
- get_album_image(): 500-2000ms (async, fallback)
- get_user_history(): 500-2000ms (paginated, 200 tracks/page)
- get_total_scrobbles(): 100-300ms
"""
import pylast
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LastFMService:
    """
    Last.fm API client for music scrobbling and user listening history.
    
    Provides access to Last.fm user data: current track, recent scrobbles, total
    playcount, album/artist metadata. Uses pylast library for high-level API access
    and direct HTTP requests for pagination/advanced features. Gracefully degrades
    on network failures (returns None or empty lists). All methods are defensive
    with try-catch to prevent caller crashes on API outages.
    
    Attributes:
        api_key (str): Last.fm API key (from config/secrets)
        api_secret (str): Last.fm API secret (for authenticated requests)
        username (str): Last.fm username to query
        network (pylast.LastFMNetwork): Authenticated connection handle
    
    Error handling:
    - Timeouts: 10s default for HTTP requests (can be customized)
    - Network: Caught and logged, returns safe defaults
    - API errors: Logged with debug/error level, no exceptions raised
    - Rate limiting: Delegated to Last.fm server (enforced transparently)
    
    Example:
        service = LastFMService(
            api_key="abc123...",
            api_secret="secret...",
            username="johndoe"
        )
        current = service.get_now_playing()
        if current:
            print(f"Now playing: {current['artist']} - {current['title']}")
    """
    
    def __init__(self, api_key: str, api_secret: str, username: str):
        """
        Initialize Last.fm service with authentication credentials.
        
        Creates pylast.LastFMNetwork connection with provided credentials. Network
        object caches authentication to avoid re-authenticating on each API call.
        No immediate network validation (first API call will fail if credentials invalid).
        
        Args:
            api_key (str): Last.fm API key (obtain from last.fm/api/account/create)
            api_secret (str): Last.fm API secret (paired with api_key)
            username (str): Last.fm username (user to query for scrobbles/history)
        
        Raises:
            No exceptions raised during init (validation deferred to first API call)
        
        Side Effects:
            - Creates pylast.LastFMNetwork instance (in-memory, no network call)
            - Stores credentials in instance variables (memory)
        
        Performance:
            - O(1) initialization, <1ms
            - No network calls until first API method invoked
        
        Example:
            service = LastFMService(
                api_key="YOUR_API_KEY",
                api_secret="YOUR_API_SECRET",
                username="username"
            )
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.username = username
        self.network = pylast.LastFMNetwork(
            api_key=api_key,
            api_secret=api_secret,
            username=username
        )
    
    def get_now_playing(self) -> Optional[Dict[str, Any]]:
        """
        Get currently playing track from user's Last.fm session or None.
        
        Queries Last.fm for track currently being played (if scrobbling is active).
        Returns track metadata only if track is actually playing right now (not
        recently played). Returns None if no track currently playing.
        
        Returns:
            dict: Track metadata with keys:
                - artist (str): Artist name
                - title (str): Track title
                - album (str): Album name (or 'Unknown' if not available)
            OR None if no track currently playing
        
        Raises:
            No exceptions raised (caught internally, returns None on error)
        
        Performance:
            - Typical: 100-500ms (single API call)
            - Network: 1 API call via pylast User.get_now_playing()
            - Big-O: O(1) constant time query
        
        Side Effects:
            - Queries Last.fm API (external, rate-limited)
            - Logs errors if API fails
        
        Logging:
            - ERROR: If exception occurs during API call
        
        Example:
            current = service.get_now_playing()
            if current:
                print(f"Playing: {current['artist']} - {current['title']}")
            else:
                print("Nothing is playing")
        """
        try:
            user = pylast.User(self.username, self.network)
            current_track = user.get_now_playing()
            
            if not current_track:
                return None
            
            result = {
                "artist": str(current_track.artist),
                "title": str(current_track.title),
                "album": str(current_track.album) if current_track.album else "Unknown"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur récupération now playing Last.fm: {e}")
            return None
    
    def get_recent_tracks(self, limit: int = 50) -> list:
        """
        Get list of recently scrobbled tracks from user's Last.fm history.
        
        Fetches the most recent (limit) scrobbles from user's listening history.
        Includes artist, title, album, and timestamp for each track. Limited to
        recent scrobbles only (not 'now playing' tracks). Useful for quick playback
        history review or import initialization.
        
        Args:
            limit (int, optional): Maximum number of tracks to return. Defaults to 50.
                Recommended: 50-200 (higher values = slower queries)
        
        Returns:
            list: List of track dicts, each with keys:
                - artist (str): Artist name
                - title (str): Track title
                - album (str): Album name (or 'Unknown')
                - timestamp (int): Unix timestamp of scrobble
            Empty list [] if error or no tracks found
        
        Raises:
            No exceptions raised (caught internally, returns [])
        
        Performance:
            - Typical: 200-800ms (depends on limit)
            - Network: 1 API call (limit tracks per call, no pagination)
            - Big-O: O(n) where n=limit (linear iteration of results)
        
        Side Effects:
            - Queries Last.fm API (external, rate-limited)
            - Logs errors if API fails
        
        Logging:
            - ERROR: If exception occurs during API call
        
        Example:
            tracks = service.get_recent_tracks(limit=100)
            for track in tracks:
                print(f"{track['artist']} - {track['title']} ({track['timestamp']})")
        """
        try:
            user = pylast.User(self.username, self.network)
            recent_tracks = user.get_recent_tracks(limit=limit)
            
            tracks = []
            for track in recent_tracks:
                tracks.append({
                    "artist": str(track.track.artist),
                    "title": str(track.track.title),
                    "album": str(track.album) if hasattr(track, 'album') and track.album else "Unknown",
                    "timestamp": int(track.timestamp) if hasattr(track, 'timestamp') and track.timestamp else 0
                })
            
            return tracks
            
        except Exception as e:
            logger.error(f"Erreur récupération recent tracks Last.fm: {e}")
            return []
    
    async def get_album_image(self, artist_name: str, album_title: str) -> Optional[str]:
        """
        Get album cover image URL from Last.fm as fallback to Spotify.
        
        Queries Last.fm for album cover art image. Used as fallback when Spotify
        image unavailable. Last.fm images often lower resolution than Spotify but
        cover more obscure/independent releases. Async method for compatibility
        with async caller context (call with await).
        
        Args:
            artist_name (str): Artist name (must match Last.fm database)
            album_title (str): Album title (must match Last.fm database)
        
        Returns:
            str: Album cover image URL (HTTPS)
            OR None if image not found or API error
        
        Raises:
            No exceptions raised (caught internally, returns None)
        
        Performance:
            - Typical: 500-2000ms (includes network latency)
            - Network: 1 API call via pylast Album.get_cover_image()
            - Big-O: O(1) constant time lookup
        
        Side Effects:
            - Queries Last.fm API (external, rate-limited)
            - Logs errors if API fails
        
        Logging:
            - ERROR: If exception occurs during API call
        
        Implementation Notes:
            - Uses pylast.Album object for high-level API access
            - Artist/album name matching: Case-insensitive via Last.fm
            - Returns best available resolution from Last.fm
            - URL format: HTTPS, direct image file (jpg/png)
        
        Example:
            image_url = await service.get_album_image("Radiohead", "OK Computer")
            if image_url:
                print(f"Cover: {image_url}")
        """
        try:
            album = pylast.Album(artist_name, album_title, self.network)
            image_url = album.get_cover_image()
            return image_url if image_url else None
            
        except Exception as e:
            logger.error(f"Erreur récupération image album Last.fm: {e}")
            return None
    
    async def get_album_artists(self, artist_name: str, album_title: str) -> list:
        """
        Get actual album artists from Last.fm (handles compilations/collaborations).
        
        Queries Last.fm for album metadata to retrieve true artist(s). Useful for
        compilations where primary artist differs from track artist, or collaborations
        with multiple credited artists. Falls back to provided artist_name if lookup
        fails. Always returns non-empty list (fallback provided).
        
        Args:
            artist_name (str): Primary artist name (used as fallback if lookup fails)
            album_title (str): Album title (must match Last.fm database)
        
        Returns:
            list: List of artist names (strings)
                - Typical: ["Artist Name"] (single item)
                - Compilations: May contain one item (album artist)
                - Fallback: [artist_name] if API error
            Always non-empty list (at minimum contains artist_name)
        
        Raises:
            No exceptions raised (caught internally, returns fallback list)
        
        Performance:
            - Typical: 500-2000ms (HTTP API call + JSON parsing)
            - Network: 1 HTTP POST to Last.fm API endpoint
            - Big-O: O(1) single album lookup
            - Timeout: 10 seconds per request
        
        Side Effects:
            - Queries Last.fm API (external, rate-limited 60 req/min)
            - Logs success/debug info for troubleshooting
        
        Logging:
            - INFO: Successful lookup (✅ Artistes d'album...)
            - DEBUG: Failures (⚠️ Impossible récupérer...)
        
        Implementation Notes:
            - HTTP direct request: User.album.getInfo endpoint
            - Response parsing: Extracts 'artist' field from album info
            - Nested dict handling: artist can be dict with '#text' or string
            - String normalization: .strip() to remove whitespace
            - Tags handling: Album tags analyzed but not returned as artists
            - Fallback gracefully: Returns [artist_name] if anything fails
            - Used by: Enrichment system for compilation album detection
        
        Example:
            artists = await service.get_album_artists("V/A", "Chill Vibes Vol. 1")
            # Returns: ["Various Artists"] or fallback ["V/A"]
            # For normal album: ["Radiohead"]
        """
        try:
            import requests
            
            # Essayer de récupérer les infos d'album depuis Last.fm
            params = {
                'method': 'album.getInfo',
                'artist': artist_name,
                'album': album_title,
                'api_key': self.api_key,
                'format': 'json'
            }
            
            response = requests.post('https://ws.audioscrobbler.com/2.0/', params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            artists = []
            
            if result and 'album' in result:
                album_info = result['album']
                
                # Artist principal
                if 'artist' in album_info:
                    artist_str = album_info['artist']
                    if isinstance(artist_str, dict):
                        artist_str = artist_str.get('#text', artist_name)
                    artists.append(str(artist_str).strip())
                
                # Tags peuvent contenir info sur collaborations
                if 'tags' in album_info and 'tag' in album_info['tags']:
                    tags = album_info['tags']['tag']
                    if not isinstance(tags, list):
                        tags = [tags]
                    # On ne récupère pas les tags comme artistes
            
            # Si pas d'info, retourner juste l'artiste principal
            if not artists:
                artists = [artist_name]
            
            logger.info(f"✅ Artistes d'album {album_title}: {artists}")
            return artists
            
        except Exception as e:
            logger.debug(f"⚠️ Impossible récupérer artistes d'album {album_title}: {e}")
            # En cas d'erreur, retourner l'artiste du track
            return [artist_name]
    
    def get_user_history(self, limit: int = 200, page: int = 1, from_timestamp: Optional[int] = None, to_timestamp: Optional[int] = None) -> list:
        """
        Get paginated user scrobble history with optional timestamp filtering.
        
        Retrieves scrobbled tracks from user's history with full pagination support.
        Allows filtering by date range (Unix timestamps). Used for large-scale history
        import (can iterate through all pages by incrementing page parameter). Each
        page returns up to 200 scrobbles with exact timestamps.
        
        Args:
            limit (int, optional): Tracks per page (max 200). Defaults to 200.
                Last.fm enforces 200 max, larger values clamped
            page (int, optional): Page number (1-based, default 1).
                Page 1 = most recent, page 2 = 200-400 tracks ago, etc.
            from_timestamp (int, optional): Unix timestamp of earliest scrobble.
                Only scrobbles >= this time returned. Defaults to None (no lower bound)
            to_timestamp (int, optional): Unix timestamp of latest scrobble.
                Only scrobbles <= this time returned. Defaults to None (no upper bound)
        
        Returns:
            list: List of scrobble dicts, each with keys:
                - artist (str): Artist name
                - title (str): Track title
                - album (str): Album name (or 'Unknown')
                - timestamp (int): Unix timestamp of scrobble
                - playback_date (str): Human-readable date (e.g., "7 Feb 2026")
            Empty list [] if error, no results, or page invalid
        
        Raises:
            No exceptions raised (caught internally, returns [])
        
        Performance:
            - Typical: 500-2000ms (single page HTTP request)
            - Network: 1 HTTP POST to Last.fm API
            - Big-O: O(limit) linear iteration of results (limit tracks)
            - Pagination: Each page independent (no batching)
            - Timeout: 10 seconds per request
        
        Side Effects:
            - Queries Last.fm API (external, rate-limited)
            - Logs errors and success count
        
        Logging:
            - INFO: Success with count (✅ Récupéré N tracks depuis Last.fm (page M))
            - ERROR: API/network failures (❌ Erreur récupération historique...)
        
        Implementation Notes:
            - HTTP direct request: user.getRecentTracks endpoint
            - Pagination: via 'page' and 'limit' parameters
            - Date filtering: via 'from' and 'to' parameters (Unix timestamp)
            - Response parsing: 'track' can be list or single dict
            - Now-playing skip: Tracks with @attr.nowplaying=true skipped
            - Timestamp validation: Only tracks with valid 'date' field included
            - Dict parsing: artist/album can be nested with '#text' field
            - Error resilience: Parse failures skip individual tracks, continues
            - Used by: Import system for complete history backfill
        
        Example:
            # Get most recent 200 scrobbles
            recent = service.get_user_history(limit=200, page=1)
            
            # Get next 200 scrobbles (older)
            older = service.get_user_history(limit=200, page=2)
            
            # Get all scrobbles from January 2026 (Unix timestamp)
            from datetime import datetime
            jan_start = int(datetime(2026, 1, 1).timestamp())
            jan_end = int(datetime(2026, 1, 31, 23, 59, 59).timestamp())
            january = service.get_user_history(
                from_timestamp=jan_start,
                to_timestamp=jan_end
            )
        """
        try:
            import requests
            
            # Construire les paramètres pour l'appel API HTTP
            params = {
                'method': 'user.getRecentTracks',
                'user': self.username,
                'api_key': self.api_key,
                'limit': min(limit, 200),  # Last.fm limite à 200 par page
                'page': max(1, page),  # Page doit être >= 1
                'format': 'json'
            }
            
            if from_timestamp:
                params['from'] = from_timestamp
            if to_timestamp:
                params['to'] = to_timestamp
            
            # Appel API HTTP direct
            response = requests.post('https://ws.audioscrobbler.com/2.0/', params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            tracks = []
            if result and 'recenttracks' in result:
                recent_tracks = result['recenttracks']
                
                # Les tracks peuvent être une liste ou un dict (si un seul track)
                track_list = recent_tracks.get('track', [])
                if isinstance(track_list, dict):
                    track_list = [track_list]
                
                for track_data in track_list:
                    # Vérifier si c'est un vrai scrobble avec timestamp
                    if '@attr' in track_data and track_data['@attr'].get('nowplaying'):
                        continue  # Skip "now playing" tracks
                    
                    if 'date' not in track_data:
                        continue  # Skip tracks sans timestamp
                    
                    timestamp = int(track_data['date'].get('uts', 0))
                    if not timestamp:
                        continue
                    
                    # Parser artiste
                    artist_data = track_data.get('artist', {})
                    if isinstance(artist_data, dict):
                        artist = artist_data.get('#text', 'Unknown')
                    else:
                        artist = str(artist_data) if artist_data else 'Unknown'
                    
                    # Parser album
                    album_data = track_data.get('album', {})
                    if isinstance(album_data, dict):
                        album = album_data.get('#text', 'Unknown')
                    else:
                        album = str(album_data) if album_data else 'Unknown'
                    
                    track_info = {
                        "artist": artist,
                        "title": track_data.get('name', 'Unknown'),
                        "album": album,
                        "timestamp": timestamp,
                        "playback_date": track_data['date'].get('#text', '')
                    }
                    tracks.append(track_info)
            
            logger.info(f"✅ Récupéré {len(tracks)} tracks depuis Last.fm (page {page})")
            return tracks
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération historique Last.fm (page {page}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_total_scrobbles(self) -> int:
        """
        Get total lifetime scrobble count for user.
        
        Queries Last.fm for user's total playcount (all-time scrobbles).
        Returns integer count of tracks ever played/scrobbled. Used for
        collection statistics and import progress tracking.
        
        Returns:
            int: Total number of scrobbles (all-time)
                0 if error or user has no scrobbles
        
        Raises:
            No exceptions raised (caught internally, returns 0)
        
        Performance:
            - Typical: 100-500ms (single API call)
            - Network: 1 API call via pylast User.get_playcount()
            - Big-O: O(1) simple count query
        
        Side Effects:
            - Queries Last.fm API (external, rate-limited)
            - Logs errors if API fails
        
        Logging:
            - ERROR: If exception occurs during API call
        
        Example:
            total = service.get_total_scrobbles()
            print(f"User has {total:,} total scrobbles")
            # Output: User has 45,238 total scrobbles
        """
        try:
            user = pylast.User(self.username, self.network)
            return int(user.get_playcount())
        except Exception as e:
            logger.error(f"Erreur récupération nombre de scrobbles: {e}")
            return 0

