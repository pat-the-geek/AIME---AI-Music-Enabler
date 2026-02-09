"""Service de tracking Last.fm en arrière-plan."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import logging

from app.database import SessionLocal
from app.services.spotify_service import SpotifyService
from app.services.lastfm_service import LastFMService
from app.services.external.ai_service import AIService
from app.models import Track, ListeningHistory, Artist, Album, Image, Metadata

logger = logging.getLogger(__name__)


class TrackerService:
    """
    Background Last.fm listening tracker with automatic enrichment.

    Polls Last.fm at regular intervals to detect newly played tracks and
    automatically enriches them with metadata from Spotify and AI descriptions.
    Prevents duplicate tracking with 10-minute deduplication window.

    Features:
        - Async polling with configurable intervals
        - Multi-source enrichment (Spotify, Last.fm, EurIA AI)
        - Duplicate detection across sources (10-minute rule)
        - Automatic artist/album image fetching
        - AI-generated album descriptions
        - Graceful error handling with fallbacks

    Configuration:
        Expects config dict with:
        - lastfm: {api_key, api_secret, username}
        - spotify: {client_id, client_secret}
        - euria: {url, bearer, max_attempts}
        - tracker: {interval_seconds, listen_start_hour, listen_end_hour}

    Lifecycle:
        1. Initialize with config -> services set up
        2. start() -> begins polling Last.fm
        3. stop() -> shuts down scheduler
        4. get_status() -> check state anytime

    Example:
        >>> config = load_config()
        >>> tracker = TrackerService(config)
        >>> await tracker.start()
        >>> # Polling runs in background
        >>> status = tracker.get_status()
        >>> print(f"Running: {status['running']}")
        >>> await tracker.stop()
    """
    
    def __init__(self, config: dict):
        """
        Initialize the Last.fm tracking service with configuration.

        Sets up all required sub-services (Last.fm, Spotify, EurIA AI) and
        the async scheduler for background polling.

        Args:
            config: Configuration dictionary with keys:
                - lastfm: {api_key, api_secret, username}
                  Credentials for Last.fm API access
                - spotify: {client_id, client_secret}
                  OAuth2 credentials for Spotify enrichment
                - euria: {url, bearer, max_attempts, default_error_message}
                  EurIA API configuration for AI descriptions
                - tracker: {interval_seconds, listen_start_hour, listen_end_hour}
                  Polling configuration

        Attributes Initialized:
            - config: Stored configuration
            - scheduler: APScheduler AsyncIOScheduler instance
            - is_running: Boolean flag (initially False)
            - last_track_key: Cache of last detected track (prevents duplicates)
            - last_poll_time: Timestamp of last polling attempt
            - recent_detections: Dict tracking recently-seen tracks (10-min window)
            - lastfm: LastFMService instance
            - spotify: SpotifyService instance
            - ai: AIService instance

        Example:
            >>> config = {
            ...     "lastfm": {"api_key": "...", "api_secret": "...", "username": "..."},
            ...     "spotify": {"client_id": "...", "client_secret": "..."},
            ...     "euria": {"url": "...", "bearer": "..."},
            ...     "tracker": {"interval_seconds": 120}
            ... }
            >>> tracker = TrackerService(config)
            >>> print(f"Tracker initialized, running: {tracker.is_running}")
            Tracker initialized, running: False

        Error Handling:
            - No exceptions raised during init
            - Services use defaults if config missing
            - Deferred errors appear on first track save
        """
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.last_track_key = None
        self.last_poll_time = None  # Dernière fois où le tracker a vérifié Last.fm
        self.recent_detections = {}  # Dict tracking recently-seen tracks (10-min window)
        
        # Initialiser les services
        lastfm_config = config.get('lastfm', {})
        spotify_config = config.get('spotify', {})
        euria_config = config.get('euria', {})
        
        self.lastfm = LastFMService(
            api_key=lastfm_config.get('api_key'),
            api_secret=lastfm_config.get('api_secret'),
            username=lastfm_config.get('username')
        )
        
        self.spotify = SpotifyService(
            client_id=spotify_config.get('client_id'),
            client_secret=spotify_config.get('client_secret')
        )
        
        self.ai = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer'),
            max_attempts=euria_config.get('max_attempts', 5),
            default_error_message=euria_config.get('default_error_message', 'Aucune information disponible')
        )
    
    async def start(self):
        """
        Start the background Last.fm polling scheduler.

        Launches the async scheduler with a recurring job that polls Last.fm
        at the configured interval. Does nothing if already running.

        Polling Behavior:
            - Interval: configurable via config['tracker']['interval_seconds']
            - Default: 150 seconds (2.5 minutes)
            - Runs continuously until stop() called
            - Non-blocking; executes in background via APScheduler

        Example:
            >>> tracker = TrackerService(config)
            >>> await tracker.start()
            >>> print("Polling started")
            >>> # Tracker now polls Last.fm every 150 seconds

        Side Effects:
            - Creates APScheduler job 'lastfm_tracker'
            - Sets is_running = True
            - Starts scheduler in background thread

        Logging:
            - Logs INFO when starting with interval
            - Logs INFO if already running (no-op)
            - Logs ERROR if startup fails

        Error Handling:
            Catches and logs exceptions but doesn't raise them,
            allowing app startup to continue if tracker fails.
        """
        if self.is_running:
            logger.info("Tracker Last.fm déjà en cours d'exécution")
            return
        
        interval = self.config.get('tracker', {}).get('interval_seconds', 150)
        
        self.scheduler.add_job(
            self._poll_lastfm,
            trigger=IntervalTrigger(seconds=interval),
            id='lastfm_tracker',
            replace_existing=True
        )
        
        try:
            self.scheduler.start()
            self.is_running = True
            logger.info(f"✅ Tracker Last.fm démarré (intervalle: {interval}s)")
        except Exception as e:
            logger.error(f"❌ Erreur démarrage Last.fm tracker: {e}", exc_info=True)
            self.is_running = False
            # Ne pas lever l'exception pour ne pas bloquer le startup de l'app

    
    async def stop(self):
        """
        Stop the background tracking scheduler.

        Shuts down the APScheduler instance, stopping all polling. Does nothing
        if tracker is not running.

        Example:
            >>> await tracker.stop()
            >>> print(f"Running: {tracker.is_running}")
            Running: False
            >>> # No more polling happening

        Side Effects:
            - Calls scheduler.shutdown()
            - Sets is_running = False
            - In-flight polls complete before shutdown

        Logging:
            - Logs INFO on successful stop
            - Logs INFO if already stopped (no-op)
        """
        if not self.is_running:
            logger.info("Tracker n'est pas en cours d'exécution")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Tracker arrêté")
    
    def get_status(self) -> dict:
        """
        Get current status of the tracking service.

        Returns a snapshot of tracker state including running status, last
        detected track, and next scheduled polling time.

        Returns:
            Dict with keys:
                - running (bool): Whether polling is active
                - last_track (str|None): Last detected track as "artist|title|album"
                - interval_seconds (int): Seconds between polls
                - last_poll_time (str|None): ISO 8601 timestamp of last poll
                - next_run_time (str|None): ISO 8601 of next scheduled poll
                  (None if not running or scheduler unavailable)

        Example:
            >>> status = tracker.get_status()
            >>> print(f"Running: {status['running']}")
            >>> print(f"Last track: {status['last_track']}")
            >>> print(f"Next poll at: {status['next_run_time']}")
            Running: True
            Last track: Pink Floyd|Shine On You Crazy Diamond|Wish You Were Here
            Next poll at: 2024-02-15T10:25:30+00:00

        Error Handling:
            - Returns next_run_time=None if scheduler query fails
            - Logs WARNING on scheduler error
            - Always returns complete status dict (never None)

        Logging:
            - Logs WARNING if unable to get next run time
        """
        next_run_time = None
        if self.is_running:
            try:
                job = self.scheduler.get_job('lastfm_tracker')
                if job and job.next_run_time:
                    next_run_time = job.next_run_time.isoformat()
            except Exception as e:
                logger.warning(f"Unable to get next run time: {e}")
        
        return {
            "running": self.is_running,
            "last_track": self.last_track_key,
            "interval_seconds": self.config.get('tracker', {}).get('interval_seconds', 150),
            "last_poll_time": self.last_poll_time.isoformat() if self.last_poll_time else None,
            "next_run_time": next_run_time
        }
    
    async def _poll_lastfm(self):
        """Interroger Last.fm et enregistrer les nouveaux tracks."""
        try:
            # Enregistrer l'heure du poll
            self.last_poll_time = datetime.now(timezone.utc)
            
            # 🔍 DEBUG: Log à chaque poll pour tracer
            logger.debug(f"📡 Polling Last.fm à {self.last_poll_time.isoformat()}")
            
            # ⚠️ DÉSACTIVÉ: Le filtre horaire empêchait l'enregistrement des lectures
            # Les lectures détectées par Last.fm doivent être enregistrées 24h/24
            # current_hour = datetime.now().hour
            # start_hour = self.config.get('tracker', {}).get('listen_start_hour', 8)
            # end_hour = self.config.get('tracker', {}).get('listen_end_hour', 22)
            # if not (start_hour <= current_hour < end_hour):
            #     logger.debug(f"Hors plage horaire d'écoute ({start_hour}h-{end_hour}h), skip polling")
            #     return
            
            # Récupérer les tracks récents (le plus récent sera le premier)
            recent_tracks = self.lastfm.get_recent_tracks(limit=1)
            
            if not recent_tracks:
                logger.debug("❌ Aucun track récent trouvé")
                return
            
            current_track = recent_tracks[0]
            
            # Créer clé unique pour éviter doublons
            track_key = f"{current_track['artist']}|{current_track['title']}|{current_track['album']}"
            
            # RÈGLE 1: Vérifier si on vient de détecter ce track (same track consecutively)
            if track_key == self.last_track_key:
                logger.debug(f"⏭️ Même track qu'avant, skip: {track_key}")
                return
            
            # RÈGLE 2: Vérifier la règle des 10 minutes - éviter les doublons immédiats
            now = int(datetime.now(timezone.utc).timestamp())
            ten_minutes_ago = now - 600  # 10 minutes en secondes
            
            if track_key in self.recent_detections:
                last_detection = self.recent_detections[track_key]
                time_diff = now - last_detection
                if time_diff < 600:  # Moins de 10 minutes
                    logger.info(f"🔄 DOUBLON 10min DÉTECTÉ (tracker): {track_key} " +
                              f"(écart: {time_diff}s). Skip enregistrement.")
                    return
            
            # Nettoyer les anciennes détections (> 10 min)
            expired_keys = [k for k, v in self.recent_detections.items() if now - v > 600]
            for k in expired_keys:
                del self.recent_detections[k]
                logger.debug(f"🧹 Détection expirée (>10min): {k}")
            
            # Enregistrer cette détection
            self.recent_detections[track_key] = now
            self.last_track_key = track_key
            logger.info(f"✨ Nouveau track détecté: {track_key}")
            
            # Enregistrer en base de données
            await self._save_track(current_track)
            
        except Exception as e:
            logger.error(f"❌ Erreur polling Last.fm: {e}", exc_info=True)
    
    def _check_duplicate(self, db: Session, artist_name: str, track_title: str, album_title: str, source: str) -> bool:
        """
        Check if a track was recently played (10-minute deduplication window).

        Implements the "10-minute rule": prevents duplicate recording of the
        same track if detected again within 10 minutes. Also prevents cross-source
        duplicates (e.g., same track detected by Roon and Last.fm simultaneously).

        Args:
            db: SQLAlchemy database session.
            artist_name: Artist name (case-insensitive matching).
            track_title: Track title (case-insensitive matching).
            album_title: Album title (case-insensitive matching).
            source: Source of detection ('lastfm' or 'roon').
                Used to tag duplicate entries and detect cross-source dupes.

        Returns:
            bool: True if this is a duplicate (should skip), False otherwise.
                - True: Track was recorded <10 minutes ago (same or different source)
                - False: Track not in database OR last record is >10 minutes old

        Example:
            >>> is_duplicate = service._check_duplicate(
            ...     db,
            ...     "Pink Floyd",
            ...     "Shine On You Crazy Diamond",
            ...     "Wish You Were Here",
            ...     "lastfm"
            ... )
            >>> if is_duplicate:
            ...     logger.info("Skip this track, already recorded recently")

        10-Minute Rule:
            - Any duplicate within 600 seconds (10 minutes) is skipped
            - Applies to same source (e.g., Last.fm duplicate within 10 min)
            - Also applies cross-source (Roon and Last.fm detect same play)
            - After 10 minutes, same track can be recorded again

        Implementation:
            - Case-insensitive DB matching using lower()
            - Queries ListeningHistory with 10-minute window
            - Checks both track existence and recent plays
            - Handles case where track not in DB (no duplicate)

        Logging:
            - Logs DEBUG for checks and lookups
            - Logs WARNING for duplicate detection
            - Logs INFO for cross-source duplicates (informational)
        """
        # Timestamp il y a 10 minutes (RÈGLE DES 10 MINUTES)
        ten_minutes_ago = int(datetime.now(timezone.utc).timestamp()) - 600
        
        logger.debug(f"🔍 Vérification doublons: {artist_name} - {track_title} ({album_title})")
        
        # Chercher le track et l'album correspondant
        # AMÉLIORATION: Utiliser LOWER() pour case-insensitive matching sur le nom d'artiste
        from sqlalchemy import func
        track = db.query(Track).join(Album).join(Album.artists).filter(
            func.lower(Track.title) == func.lower(track_title),
            func.lower(Album.title) == func.lower(album_title),
            func.lower(Artist.name) == func.lower(artist_name)
        ).first()
        
        if not track:
            logger.debug(f"✅ Pas de track en base pour: {artist_name} - {track_title}")
            return False  # Pas de doublon si le track n'existe pas
        
        # Vérifier si une entrée récente existe pour ce track
        recent_entries = db.query(ListeningHistory).filter(
            ListeningHistory.track_id == track.id,
            ListeningHistory.timestamp >= ten_minutes_ago
        ).all()
        
        if not recent_entries:
            logger.debug(f"✅ Aucune entrée récente (< 10 min) pour ce track")
            return False  # Pas d'entrée récente
        
        logger.debug(f"⚠️ {len(recent_entries)} entrée(s) récente(s) trouvée(s) pour ce track")
        
        # Vérifier les doublons par source
        for entry in recent_entries:
            time_diff = abs(datetime.now(timezone.utc).timestamp() - entry.timestamp)
            
            if entry.source == source:
                # Doublon de la même source
                logger.warning(f"🔄 DOUBLON DÉTECTÉ ({source}): {artist_name} - {track_title} " +
                             f"déjà enregistré il y a {int(time_diff)}s")
                return True
            else:
                # Doublon d'une autre source (les deux trackers ont capté le même morceau)
                logger.info(f"ℹ️ Morceau déjà capté par {entry.source}: {artist_name} - {track_title} " +
                          f"(écart: {int(time_diff)}s). Skip enregistrement {source}.")
                return True
        
        return False
    
    async def _save_track(self, track_data: dict):
        """
        Save a newly detected track with full enrichment to the database.

        Handles the complete enrichment pipeline:
        1. Creates artist if missing (fetches Spotify image)
        2. Creates album if missing (fetches Spotify details, images, AI info)
        3. Updates existing album if missing enrichments
        4. Creates track entry if missing
        5. Records listening history entry

        Args:
            track_data: Dictionary with track information:
                - artist (str): Artist name
                - title (str): Track title
                - album (str): Album title

        Side Effects:
            - Creates/updates Album, Artist, Track, Image, Metadata records
            - Makes async calls to Spotify and EurIA services
            - Logs detailed info about enrichments added

        Enrichments Performed:
            - Artist image from Spotify (if missing)
            - Album Spotify URL and release year
            - Album images (Spotify + Last.fm)
            - AI-generated album description
            - Listening history record with correct timestamp

        Error Handling:
            - Catches exceptions per operation (doesn't fail entire save)
            - Rolls back transaction on failure
            - Logs errors without stopping process
            - Graceful fallback if Spotify/EurIA unavailable

        Example:
            >>> track_data = {
            ...     "artist": "Pink Floyd",
            ...     "title": "Shine On You Crazy Diamond",
            ...     "album": "Wish You Were Here"
            ... }
            >>> await service._save_track(track_data)
            >>> # Track now in DB with all enrichments

        Performance:
            - Async operations run in parallel where possible
            - May take 2-10 seconds total (API calls)
            - Database transaction commits atomically

        Logging:
            - Logs INFO for successful enrichments
            - Logs WARNING for skipped tracks (duplicates)
            - Logs ERROR on database errors
            - Final INFO on successful save with timestamp
        """
        db = SessionLocal()
        try:
            artist_name = track_data['artist']
            track_title = track_data['title']
            album_title = track_data['album']
            
            # Vérifier les doublons avant d'enregistrer
            if self._check_duplicate(db, artist_name, track_title, album_title, 'lastfm'):
                logger.debug(f"Skip enregistrement doublon: {artist_name} - {track_title}")
                db.close()
                return
            
            # Créer/récupérer artiste
            artist = db.query(Artist).filter_by(name=artist_name).first()
            if not artist:
                artist = Artist(name=artist_name)
                db.add(artist)
                db.flush()
                
                # Récupérer image artiste depuis Spotify
                artist_image = await self.spotify.search_artist_image(artist_name)
                if artist_image:
                    img = Image(
                        url=artist_image,
                        image_type='artist',
                        source='spotify',
                        artist_id=artist.id
                    )
                    db.add(img)
                    logger.info(f"🎤 Image artiste créée pour nouveau artiste: {artist_name}")
            else:
                # Artiste existant : vérifier si l'image manque
                has_artist_image = db.query(Image).filter_by(
                    artist_id=artist.id,
                    image_type='artist'
                ).first() is not None
                
                if not has_artist_image:
                    artist_image = await self.spotify.search_artist_image(artist_name)
                    if artist_image:
                        img = Image(
                            url=artist_image,
                            image_type='artist',
                            source='spotify',
                            artist_id=artist.id
                        )
                        db.add(img)
                        logger.info(f"🎤 Image artiste ajoutée pour artiste existant: {artist_name}")
            
            # Créer/récupérer album - AVEC FILTRE ARTISTE pour éviter les doublons
            album = db.query(Album).filter(
                Album.title == album_title,
                Album.artists.any(Artist.id == artist.id)
            ).first()
            if not album:
                album = Album(title=album_title, source='lastfm')
                if artist not in album.artists:
                    album.artists.append(artist)
                db.add(album)
                db.flush()
                
                # Récupérer détails Spotify (URL + année + image)
                spotify_details = await self.spotify.search_album_details(artist_name, album_title)
                if spotify_details:
                    if spotify_details.get("spotify_url"):
                        album.spotify_url = spotify_details["spotify_url"]
                        logger.info(f"🎵 URL Spotify ajoutée: {spotify_details['spotify_url']}")
                    if spotify_details.get("year"):
                        album.year = spotify_details["year"]
                        logger.info(f"📅 Année ajoutée: {spotify_details['year']}")
                    
                    # Image Spotify depuis les détails
                    if spotify_details.get("image_url"):
                        img_spotify = Image(
                            url=spotify_details["image_url"],
                            image_type='album',
                            source='spotify',
                            album_id=album.id
                        )
                        db.add(img_spotify)
                
                album_image_lastfm = await self.lastfm.get_album_image(artist_name, album_title)
                if album_image_lastfm:
                    img_lastfm = Image(
                        url=album_image_lastfm,
                        image_type='album',
                        source='lastfm',
                        album_id=album.id
                    )
                    db.add(img_lastfm)
                
                # Générer info IA
                ai_info = await self.ai.generate_album_info(artist_name, album_title)
                if ai_info:
                    metadata = Metadata(
                        album_id=album.id,
                        ai_info=ai_info
                    )
                    db.add(metadata)
            else:
                # Album existant : vérifier si les enrichissements manquent
                # Vérifier URL Spotify et année
                if not album.spotify_url or not album.year:
                    spotify_details = await self.spotify.search_album_details(artist_name, album_title)
                    if spotify_details:
                        if not album.spotify_url and spotify_details.get("spotify_url"):
                            album.spotify_url = spotify_details["spotify_url"]
                            logger.info(f"🎵 URL Spotify ajoutée: {spotify_details['spotify_url']}")
                        if not album.year and spotify_details.get("year"):
                            album.year = spotify_details["year"]
                            logger.info(f"📅 Année ajoutée: {spotify_details['year']}")
                
                # Vérifier images Spotify
                has_spotify_image = db.query(Image).filter_by(
                    album_id=album.id,
                    image_type='album',
                    source='spotify'
                ).first() is not None
                
                if not has_spotify_image:
                    album_image_spotify = await self.spotify.search_album_image(artist_name, album_title)
                    if album_image_spotify:
                        img_spotify = Image(
                            url=album_image_spotify,
                            image_type='album',
                            source='spotify',
                            album_id=album.id
                        )
                        db.add(img_spotify)
                        logger.info(f"🎵 Image Spotify ajoutée pour {album_title}")
                
                # Vérifier images Last.fm
                has_lastfm_image = db.query(Image).filter_by(
                    album_id=album.id,
                    image_type='album',
                    source='lastfm'
                ).first() is not None
                
                if not has_lastfm_image:
                    album_image_lastfm = await self.lastfm.get_album_image(artist_name, album_title)
                    if album_image_lastfm:
                        img_lastfm = Image(
                            url=album_image_lastfm,
                            image_type='album',
                            source='lastfm',
                            album_id=album.id
                        )
                        db.add(img_lastfm)
                        logger.info(f"🎵 Image Last.fm ajoutée pour {album_title}")
                
                # Vérifier info IA
                has_ai_info = db.query(Metadata).filter_by(album_id=album.id).first() is not None
                
                if not has_ai_info:
                    ai_info = await self.ai.generate_album_info(artist_name, album_title)
                    if ai_info:
                        metadata = Metadata(
                            album_id=album.id,
                            ai_info=ai_info
                        )
                        db.add(metadata)
                        logger.info(f"🤖 Info IA ajoutée pour {album_title}")
            
            # Créer track
            track = db.query(Track).filter_by(
                album_id=album.id,
                title=track_title
            ).first()
            
            if not track:
                track = Track(
                    album_id=album.id,
                    title=track_title
                )
                db.add(track)
                db.flush()
            
            # Créer entrée historique avec timestamp correct
            now = datetime.now(timezone.utc)
            timestamp = int(now.timestamp())
            date_str = now.strftime("%Y-%m-%d %H:%M")
            
            history = ListeningHistory(
                track_id=track.id,
                timestamp=timestamp,
                date=date_str,
                source='lastfm',
                loved=False
            )
            db.add(history)
            
            db.commit()
            logger.info(f"✅ Track enregistré: {artist_name} - {track_title} (timestamp={timestamp}, date={date_str})")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erreur sauvegarde track: {e}")
        finally:
            db.close()
