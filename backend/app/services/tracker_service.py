"""Service de tracking Last.fm en arrière-plan."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import logging

from app.database import SessionLocal
from app.services.spotify_service import SpotifyService
from app.services.lastfm_service import LastFMService
from app.services.ai_service import AIService
from app.models import Track, ListeningHistory, Artist, Album, Image, Metadata

logger = logging.getLogger(__name__)


class TrackerService:
    """Service de tracking Last.fm en arrière-plan."""
    
    def __init__(self, config: dict):
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.last_track_key = None
        self.last_poll_time = None  # Dernière fois où le tracker a vérifié Last.fm
        self.recent_detections = {}  # Tracking des détections récentes (track_key -> timestamp) pour la règle 10min
        
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
        """Démarrer le tracker."""
        if self.is_running:
            logger.info("Tracker déjà en cours d'exécution")
            return
        
        interval = self.config.get('tracker', {}).get('interval_seconds', 120)
        
        self.scheduler.add_job(
            self._poll_lastfm,
            trigger=IntervalTrigger(seconds=interval),
            id='lastfm_tracker',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info(f"Tracker démarré (intervalle: {interval}s)")
    
    async def stop(self):
        """Arrêter le tracker."""
        if not self.is_running:
            logger.info("Tracker n'est pas en cours d'exécution")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Tracker arrêté")
    
    def get_status(self) -> dict:
        """Obtenir le statut du tracker."""
        next_run_time = None
        if self.is_running:
            try:
                job = self.scheduler.get_job('lastfm_tracker')
                if job and job.next_run_time:
                    next_run_time = job.next_run_time.isoformat()
            except Exception as e:
                logger.warning(f"⚠️ Erreur obtention statut tracker: {e}")
        
        return {
            "running": self.is_running,
            "last_track": self.last_track_key,
            "interval_seconds": self.config.get('tracker', {}).get('interval_seconds', 120),
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
        """Vérifier si le track existe déjà récemment (dans les 10 dernières minutes) - RÈGLE DES 10 MINUTES.
        
        Args:
            db: Session de base de données
            artist_name: Nom de l'artiste
            track_title: Titre du morceau
            album_title: Titre de l'album
            source: Source du tracker ('lastfm' ou 'roon')
            
        Returns:
            True si c'est un doublon, False sinon
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
        """Sauvegarder un track en base de données."""
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
