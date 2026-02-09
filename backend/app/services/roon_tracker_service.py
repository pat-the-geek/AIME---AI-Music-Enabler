"""Service de tracking Roon en arrière-plan."""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import logging

from app.database import SessionLocal
from app.services.roon_service import RoonService
from app.services.spotify_service import SpotifyService
from app.services.external.ai_service import AIService
from app.models import Track, ListeningHistory, Artist, Album, Image, Metadata

logger = logging.getLogger(__name__)


class RoonTrackerService:
    """
    Background Roon playback tracker with automatic enrichment.

    Polls Roon server at regular intervals to detect now-playing tracks and
    automatically enriches them with metadata from Spotify and AI descriptions.
    Similar to TrackerService but specific to Roon integration.

    Features:
        - Async polling of Roon zones
        - Multi-source enrichment (Spotify, Last.fm, EurIA AI)
        - Duplicate detection across sources (10-minute rule)
        - Zone-aware playback detection
        - Graceful handling of Roon disconnection
        - Automatic artist/album enrichment

    Configuration:
        Expects config dict with:
        - roon_server: Roon server address (primary)
        - roon: {server, token} (alternative config)
        - spotify: {client_id, client_secret}
        - euria: {url, bearer, max_attempts}
        - roon_tracker: {interval_seconds, listen_start_hour, listen_end_hour}

    Roon Integration:
        - Requires active Roon server connection
        - Polls all zones for now-playing track
        - Uses zone_name for context tracking
        - Gracefully handles disconnection/reconnection

    Example:
        >>> config = load_config()
        >>> tracker = RoonTrackerService(config)
        >>> await tracker.start()
        >>> status = tracker.get_status()
        >>> print(f"Connected: {status['connected']}, Zones: {status['zones_count']}")
        Connected: True, Zones: 2
    """
    
    def __init__(self, config: dict, roon_service: 'RoonService' = None):
        """
        Initialize the Roon tracking service.

        Sets up Roon connection and sub-services (Spotify, EurIA AI) for track
        enrichment. Can use an existing RoonService instance (singleton pattern)
        or create a new one if not provided.

        Args:
            config: Configuration dictionary with keys:
                - roon_server (str): Roon server IP/hostname (preferred)
                - roon: {server, token} (alternative format)
                - spotify: {client_id, client_secret}
                - euria: {url, bearer, max_attempts}
                - roon_tracker: {interval_seconds, listen_start_hour, listen_end_hour}
            roon_service: Optional pre-initialized RoonService instance.
                If provided, skips Roon initialization (singleton pattern).
                If None, attempts to initialize from config.

        Attributes Initialized:
            - config: Stored configuration
            - scheduler: APScheduler AsyncIOScheduler instance
            - is_running: Boolean flag (initially False)
            - last_track_key: Cache of last detected track
            - last_poll_time: Timestamp of last polling attempt
            - recent_detections: Dict tracking recently-seen tracks (10-min window)
            - roon: RoonService instance (or None if connection fails)
            - spotify: SpotifyService instance
            - ai: AIService instance

        Roon Initialization:
            - Uses roon_service parameter if provided (preferred for singleton)
            - Falls back to creating from config if not provided
            - Handles missing roon_server gracefully (roon=None, continues)
            - Logs ERROR if initialization fails

        Example:
            >>> config = {"roon_server": "192.168.1.50", ...}
            >>> tracker = RoonTrackerService(config)
            >>> status = tracker.get_status()
            >>> print(f"Configured: {status['configured']}")
            Configured: True

        Error Handling:
            - Continues even if Roon connection fails
            - start() will fail gracefully if Roon not connected
            - Logs errors without raising exceptions
        """
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.last_track_key = None
        self.last_poll_time = None
        self.recent_detections = {}
        
        # Use provided RoonService instance or create new one
        if roon_service is not None:
            self.roon = roon_service
        else:
            # Try to initialize Roon from config
            roon_config = config.get('roon', {})
            try:
                self.roon = RoonService(
                    server=roon_config.get('server'),
                    token=roon_config.get('token')
                )
            except Exception as e:
                logger.error(f"❌ Erreur initialisation RoonService: {e}")
                self.roon = None
        
        # Initialize Spotify service
        spotify_config = config.get('spotify', {})
        self.spotify = SpotifyService(
            client_id=spotify_config.get('client_id'),
            client_secret=spotify_config.get('client_secret')
        )
        
        # Initialize AI service
        euria_config = config.get('euria', {})
        self.ai = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer'),
            max_attempts=euria_config.get('max_attempts', 5),
            default_error_message=euria_config.get('default_error_message', 'Aucune information disponible')
        )
    
    async def start(self):
        """
        Start the background Roon polling scheduler.

        Launches async polling of Roon's now-playing state at configured intervals.
        Validates Roon connection before starting.

        Validation:
            - Checks Roon connectivity
            - Logs detailed info about available zones
            - Fails gracefully with ERROR logging if not connected

        Example:
            >>> tracker = RoonTrackerService(config)
            >>> await tracker.start()
            >>> print("Roon polling started")
            Roon polling started

        Polling Behavior:
            - Interval: configurable via config['roon_tracker']['interval_seconds']
            - Default: 120 seconds (2 minutes)
            - Respects listen_start_hour/listen_end_hour time window
            - Runs continuously until stop() called

        Error Handling:
            - Logs ERROR and returns silently if not connected
            - No exceptions raised to caller
            - Idempotent: calling when already running logs info (no-op)

        Logging:
            - Logs INFO when starting successfully
            - Logs ERROR if not connected or other issues
            - Logs INFO with available zones on successful start
        """
        if self.is_running:
            logger.info("🎵 Tracker Roon déjà en cours d'exécution")
            return
        
        if not self.roon or not self.roon.is_connected():
            logger.error("❌ Impossible de démarrer le tracker Roon: non connecté au serveur")
            return
        
        interval = self.config.get('roon_tracker', {}).get('interval_seconds', 120)
        
        self.scheduler.add_job(
            self._poll_roon,
            trigger=IntervalTrigger(seconds=interval),
            id='roon_tracker',
            replace_existing=True
        )
        
        try:
            self.scheduler.start()
            self.is_running = True
            logger.info(f"✅ Tracker Roon démarré (intervalle: {interval}s)")
        except Exception as e:
            logger.error(f"❌ Erreur démarrage Roon tracker: {e}", exc_info=True)
            self.is_running = False
            # Ne pas lever l'exception pour ne pas bloquer le startup de l'app

    
    async def stop(self):
        """
        Stop the background Roon polling scheduler.

        Shuts down the APScheduler, terminating all Roon polling. Does nothing
        if tracker is not running.

        Example:
            >>> await tracker.stop()
            >>> status = tracker.get_status()
            >>> print(f"Running: {status['running']}")
            Running: False
        """
        if not self.is_running:
            logger.info("🎵 Tracker Roon n'est pas en cours d'exécution")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("🎵 Tracker Roon arrêté")
    
    def get_status(self) -> dict:
        """
        Get current Roon tracker status including connection and zones.

        Returns comprehensive status including connection state, zone count,
        and scheduling information.

        Returns:
            Dict with keys:
                - running (bool): Whether polling is active
                - connected (bool): Roon server connection status
                - configured (bool): Whether roon_server is configured
                - last_track (str|None): Last detected track key
                - interval_seconds (int): Polling interval
                - last_poll_time (str|None): ISO 8601 of last poll
                - next_run_time (str|None): ISO 8601 of next poll
                - server (str|None): Roon server address
                - zones_count (int): Number of active Roon zones

        Example:
            >>> status = tracker.get_status()
            >>> print(f"Zones: {status['zones_count']}, Connected: {status['connected']}")
            Zones: 2, Connected: True
        """
        next_run_time = None
        zones_count = 0
        connected = False
        
        if self.roon:
            connected = self.roon.is_connected()
            try:
                zones_count = len(self.roon.get_zones()) if connected else 0
            except Exception as e:
                logger.debug(f"Unable to get zones: {e}")
        
        if self.is_running:
            try:
                job = self.scheduler.get_job('roon_tracker')
                if job and job.next_run_time:
                    next_run_time = job.next_run_time.isoformat()
            except Exception as e:
                logger.debug(f"Unable to get next run time: {e}")
        
        return {
            "running": self.is_running,
            "connected": connected,
            "configured": self.roon is not None,
            "last_track": self.last_track_key,
            "interval_seconds": self.config.get('roon_tracker', {}).get('interval_seconds', 120),
            "last_poll_time": self.last_poll_time.isoformat() if self.last_poll_time else None,
            "next_run_time": next_run_time,
            "server": self.config.get('roon', {}).get('server'),
            "zones_count": zones_count
        }
    
    async def _recover_connection(self):
        """
        Attempt to recover connection after wake-up from sleep or network issues.
        
        Called when polling fails. Performs health checks and attempts to
        reinitialize the connection if the bridge appears to be stale.
        
        Recovery actions:
        - Check bridge health status
        - Log detailed diagnostics
        - May trigger bridge reconnection via health check endpoint
        
        Returns:
            bool: True if recovery appears successful, False if still disconnected
        """
        logger.warning("🔄 Attempting to recover Roon connection...")
        
        if not self.roon:
            logger.error("❌ Roon service not initialized")
            return False
        
        try:
            # Get detailed health info
            health = self.roon.get_bridge_health()
            logger.info(
                f"🏥 Bridge health: accessible={health['bridge_accessible']}, "
                f"connected={health['connected_to_core']}, "
                f"zones={health['zones_count']}, "
                f"health_failures={health['health_failures']}"
            )
            
            # If bridge is accessible but not connected, wait a moment for bridge to reconnect
            if health['bridge_accessible'] and not health['connected_to_core']:
                logger.info("⏳ Bridge accessible but disconnected from Core - waiting for bridge reconnection...")
                await asyncio.sleep(2)  # Wait for bridge's health check to trigger reconnection
                
                # Check again
                health = self.roon.get_bridge_health()
                if health['connected_to_core']:
                    logger.info("✅ Bridge reconnected to Core")
                    return True
                else:
                    logger.warning(f"❌ Still disconnected after wait. Health failures: {health['health_failures']}")
                    return False
            
            # If bridge not accessible, something is very wrong
            if not health['bridge_accessible']:
                logger.error("❌ Bridge not responding - may need to restart bridge service")
                return False
            
            # If connected but no zones, may be in process of initializing
            if health['connected_to_core'] and health['zones_count'] == 0:
                logger.info("⏳ Connected but no zones yet - waiting for zone initialization...")
                await asyncio.sleep(3)
                zones = self.roon.get_zones()
                if zones:
                    logger.info(f"✅ Zones now available: {len(zones)} zone(s)")
                    return True
            
            # Check if actually connected now
            is_connected = self.roon.is_connected()
            if is_connected:
                logger.info("✅ Connection recovered")
                return True
            else:
                logger.warning("❌ Connection still failing")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during connection recovery: {e}", exc_info=True)
            return False
    
    async def _poll_roon(self):
        """Interroger Roon et enregistrer les nouveaux tracks."""
        try:
            # Enregistrer l'heure du poll
            self.last_poll_time = datetime.now(timezone.utc)
            
            # Vérifier la connexion au serveur
            if not self.roon or not self.roon.is_connected():
                logger.warning("⚠️ Roon not connected, attempting recovery...")
                await self._recover_connection()
                return
            
            # Vérifier si nous sommes dans la plage horaire active
            current_hour = datetime.now().hour
            start_hour = self.config.get('roon_tracker', {}).get('listen_start_hour', 8)
            end_hour = self.config.get('roon_tracker', {}).get('listen_end_hour', 22)
            
            if not (start_hour <= current_hour < end_hour):
                logger.debug(f"Hors plage horaire d'écoute Roon ({start_hour}h-{end_hour}h), skip polling")
                return
            
            current_track = self.roon.get_now_playing()
            
            if not current_track:
                logger.debug("Aucun track en cours de lecture sur Roon")
                return
            
            # Créer clé unique pour éviter doublons
            track_key = f"{current_track['artist']}|{current_track['title']}|{current_track['album']}"
            
            # RÈGLE 1: Vérifier si on vient de détecter ce track (same track consecutively)
            if track_key == self.last_track_key:
                logger.debug("Même track qu'avant sur Roon, skip")
                return
            
            # RÈGLE 2: Vérifier la règle des 10 minutes - éviter les doublons immédiats
            now = int(datetime.now(timezone.utc).timestamp())
            ten_minutes_ago = now - 600  # 10 minutes en secondes
            
            if track_key in self.recent_detections:
                last_detection = self.recent_detections[track_key]
                time_diff = now - last_detection
                if time_diff < 600:  # Moins de 10 minutes
                    logger.info(f"🔄 DOUBLON 10min DÉTECTÉ (Roon tracker): {track_key} " +
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
            logger.info(f"🎵 Nouveau track Roon détecté: {track_key} (zone: {current_track['zone_name']})")
            
            # Enregistrer en base de données
            await self._save_track(current_track)
            
        except Exception as e:
            logger.error(f"Erreur polling Roon: {e}")
    
    def _check_duplicate(self, db: Session, artist_name: str, track_title: str, album_title: str, source: str) -> bool:
        """
        Check if a track was recently detected from Roon (10-minute window).

        Implements the "10-minute rule" to prevent duplicate recording. Also
        detects cross-source duplicates (same track from both Roon and Last.fm).

        Args:
            db: SQLAlchemy database session.
            artist_name: Artist name (case-insensitive).
            track_title: Track title (case-insensitive).
            album_title: Album title (case-insensitive).
            source: Detection source ('lastfm' or 'roon').

        Returns:
            bool: True if duplicate within 10 minutes, False otherwise.
        """
        # Timestamp il y a 10 minutes (RÈGLE DES 10 MINUTES)
        ten_minutes_ago = int(datetime.now(timezone.utc).timestamp()) - 600
        
        # Chercher le track et l'album correspondant
        # AMÉLIORATION: Utiliser LOWER() pour case-insensitive matching sur le nom d'artiste
        from sqlalchemy import func
        track = db.query(Track).join(Album).join(Album.artists).filter(
            func.lower(Track.title) == func.lower(track_title),
            func.lower(Album.title) == func.lower(album_title),
            func.lower(Artist.name) == func.lower(artist_name)
        ).first()
        
        if not track:
            return False  # Pas de doublon si le track n'existe pas
        
        # Vérifier si une entrée récente existe pour ce track
        recent_entries = db.query(ListeningHistory).filter(
            ListeningHistory.track_id == track.id,
            ListeningHistory.timestamp >= ten_minutes_ago
        ).all()
        
        if not recent_entries:
            return False  # Pas d'entrée récente
        
        # Vérifier les doublons par source
        for entry in recent_entries:
            time_diff = abs(datetime.now(timezone.utc).timestamp() - entry.timestamp)
            
            if entry.source == source:
                # Doublon de la même source
                logger.warning(f"⚠️ Doublon détecté ({source}): {artist_name} - {track_title} " +
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
        Save a newly detected Roon track with enrichment.

        Performs the complete enrichment pipeline for tracks detected from Roon,
        creating or updating artist, album, track, and metadata records.

        Args:
            track_data: Dictionary with track information:
                - artist (str): Artist name
                - title (str): Track title
                - album (str): Album name
                - zone_name (str): Roon zone where track is playing

        Side Effects:
            - Creates/updates database records
            - Fetches Spotify metadata
            - Generates AI descriptions
            - Records listening history

        Error Handling:
            - Catches and logs errors without stopping process
            - Rolls back transaction on failure
            - Graceful fallback if Spotify/AI unavailable
        """
        db = SessionLocal()
        try:
            artist_name = track_data['artist']
            track_title = track_data['title']
            album_title = track_data['album']
            
            # Vérifier les doublons avant d'enregistrer
            if self._check_duplicate(db, artist_name, track_title, album_title, 'roon'):
                logger.debug(f"Skip enregistrement doublon Roon: {artist_name} - {track_title}")
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
                album = Album(title=album_title, source='roon', support='Roon')
                if artist not in album.artists:
                    album.artists.append(artist)
                db.add(album)
                db.flush()
                
                # Récupérer détails Spotify (URL + année + image)
                spotify_details = await self.spotify.search_album_details(artist_name, album_title)
                if spotify_details:
                    if spotify_details.get("spotify_url"):
                        album.spotify_url = spotify_details["spotify_url"]
                    if spotify_details.get("year"):
                        album.year = spotify_details["year"]
                    if spotify_details.get("image_url"):
                        img = Image(
                            url=spotify_details["image_url"],
                            image_type='album',
                            source='spotify',
                            album_id=album.id
                        )
                        db.add(img)
                
                # Enrichir avec l'IA
                try:
                    ai_info = await self.ai.generate_album_info(artist_name, album_title)
                    if ai_info:
                        metadata = Metadata(album_id=album.id, ai_info=ai_info)
                        db.add(metadata)
                except Exception as e:
                    logger.warning(f"⚠️ Erreur enrichissement IA pour {album_title}: {e}")
            else:
                # Album existant : enrichir si manquant (URL Spotify, année, images)
                needs_update = False
                
                if not album.spotify_url or not album.year:
                    spotify_details = await self.spotify.search_album_details(artist_name, album_title)
                    if spotify_details:
                        if not album.spotify_url and spotify_details.get("spotify_url"):
                            album.spotify_url = spotify_details["spotify_url"]
                            logger.info(f"🎵 URL Spotify ajoutée pour album existant: {album_title}")
                            needs_update = True
                        if not album.year and spotify_details.get("year"):
                            album.year = spotify_details["year"]
                            logger.info(f"📅 Année ajoutée pour album existant: {album_title}")
                            needs_update = True
                        
                        # Vérifier si l'image Spotify manque
                        if spotify_details.get("image_url"):
                            has_album_image = db.query(Image).filter_by(
                                album_id=album.id,
                                image_type='album',
                                source='spotify'
                            ).first() is not None
                            
                            if not has_album_image:
                                img = Image(
                                    url=spotify_details["image_url"],
                                    image_type='album',
                                    source='spotify',
                                    album_id=album.id
                                )
                                db.add(img)
                                logger.info(f"🖼️ Image album ajoutée pour album existant: {album_title}")
                                needs_update = True
                else:
                    # Vérifier uniquement l'image si URL et année existent
                    has_album_image = db.query(Image).filter_by(
                        album_id=album.id,
                        image_type='album',
                        source='spotify'
                    ).first() is not None
                    
                    if not has_album_image:
                        album_image = await self.spotify.search_album_image(artist_name, album_title)
                        if album_image:
                            img = Image(
                                url=album_image,
                                image_type='album',
                                source='spotify',
                                album_id=album.id
                            )
                            db.add(img)
                            logger.info(f"🖼️ Image album ajoutée pour album existant: {album_title}")
                            needs_update = True
                
                # Vérifier info IA pour les albums existants (IMPORTANT: enrichissement IA)
                has_ai_info = db.query(Metadata).filter_by(album_id=album.id).first() is not None
                
                if not has_ai_info:
                    try:
                        ai_info = await self.ai.generate_album_info(artist_name, album_title)
                        if ai_info:
                            metadata = Metadata(album_id=album.id, ai_info=ai_info)
                            db.add(metadata)
                            logger.info(f"🤖 Info IA ajoutée pour album existant: {album_title}")
                            needs_update = True
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur enrichissement IA pour album existant {album_title}: {e}")
            
            # Créer/récupérer track
            track = db.query(Track).filter_by(
                title=track_title,
                album_id=album.id
            ).first()
            
            if not track:
                # Extraire la durée depuis track_data
                duration_seconds = track_data.get('duration_seconds')
                
                track = Track(
                    title=track_title,
                    album_id=album.id,
                    duration_seconds=duration_seconds
                )
                db.add(track)
                db.flush()
            elif track_data.get('duration_seconds') and not track.duration_seconds:
                # Mettre à jour la durée si elle n'existe pas encore
                track.duration_seconds = track_data.get('duration_seconds')
                db.flush()
            
            # Enregistrer l'écoute avec source Roon
            now = datetime.now(timezone.utc)
            history = ListeningHistory(
                track_id=track.id,
                timestamp=int(now.timestamp()),
                date=now.strftime("%Y-%m-%d %H:%M"),
                source='roon',  # Identifier la source
                loved=False
            )
            db.add(history)
            
            db.commit()
            logger.info(f"✅ Track Roon enregistré: {track_title} - {artist_name}")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde track Roon: {e}")
            db.rollback()
        finally:
            db.close()
