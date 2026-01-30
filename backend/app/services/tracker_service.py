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
        return {
            "running": self.is_running,
            "last_track": self.last_track_key,
            "interval_seconds": self.config.get('tracker', {}).get('interval_seconds', 120)
        }
    
    async def _poll_lastfm(self):
        """Interroger Last.fm et enregistrer les nouveaux tracks."""
        try:
            current_track = self.lastfm.get_now_playing()
            
            if not current_track:
                logger.debug("Aucun track en cours de lecture")
                return
            
            # Créer clé unique pour éviter doublons
            track_key = f"{current_track['artist']}|{current_track['title']}|{current_track['album']}"
            
            if track_key == self.last_track_key:
                logger.debug("Même track qu'avant, skip")
                return
            
            self.last_track_key = track_key
            logger.info(f"Nouveau track détecté: {track_key}")
            
            # Enregistrer en base de données
            await self._save_track(current_track)
            
        except Exception as e:
            logger.error(f"Erreur polling Last.fm: {e}")
    
    async def _save_track(self, track_data: dict):
        """Sauvegarder un track en base de données."""
        db = SessionLocal()
        try:
            artist_name = track_data['artist']
            track_title = track_data['title']
            album_title = track_data['album']
            
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
            
            # Créer/récupérer album
            album = db.query(Album).filter_by(title=album_title).first()
            if not album:
                album = Album(title=album_title)
                if artist not in album.artists:
                    album.artists.append(artist)
                db.add(album)
                db.flush()
                
                # Récupérer images album
                album_image_spotify = await self.spotify.search_album_image(artist_name, album_title)
                if album_image_spotify:
                    img_spotify = Image(
                        url=album_image_spotify,
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
            
            # Créer entrée historique
            now = datetime.now(timezone.utc)
            history = ListeningHistory(
                track_id=track.id,
                timestamp=int(now.timestamp()),
                date=now.strftime("%Y-%m-%d %H:%M"),
                source='lastfm',
                loved=False
            )
            db.add(history)
            
            db.commit()
            logger.info(f"✅ Track enregistré: {artist_name} - {track_title}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erreur sauvegarde track: {e}")
        finally:
            db.close()
