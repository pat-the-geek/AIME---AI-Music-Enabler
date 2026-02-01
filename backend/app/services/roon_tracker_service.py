"""Service de tracking Roon en arrière-plan."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import logging

from app.database import SessionLocal
from app.services.roon_service import RoonService
from app.services.spotify_service import SpotifyService
from app.services.ai_service import AIService
from app.models import Track, ListeningHistory, Artist, Album, Image, Metadata

logger = logging.getLogger(__name__)


class RoonTrackerService:
    """Service de tracking Roon en arrière-plan."""
    
    def __init__(self, config: dict, roon_service: 'RoonService' = None):
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.last_track_key = None
        self.last_poll_time = None  # Dernière fois où le tracker a vérifié Roon
        
        # Initialiser les services
        roon_config = config.get('roon', {})
        spotify_config = config.get('spotify', {})
        euria_config = config.get('euria', {})
        
        # Utiliser l'instance Roon passée en paramètre (singleton partagé)
        # ou en créer une nouvelle si nécessaire
        if roon_service is not None:
            self.roon = roon_service
        else:
            # Récupérer l'adresse du serveur (priorité à roon_server pour compatibilité)
            roon_server = config.get('roon_server') or roon_config.get('server')
            
            # N'initialiser RoonService que si serveur est configuré
            self.roon = None
            if roon_server:
                try:
                    self.roon = RoonService(
                        server=roon_server,
                        token=roon_config.get('token')
                    )
                except Exception as e:
                    logger.error(f"❌ Erreur initialisation RoonService: {e}")
                    self.roon = None
        
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
            logger.info("🎵 Tracker Roon déjà en cours d'exécution")
            return
        
        if not self.roon or not self.roon.is_connected():
            logger.error("❌ Impossible de démarrer le tracker Roon: non connecté au serveur")
            return
        
        # Vérifier que les zones sont disponibles
        zones = self.roon.get_zones()
        if not zones:
            logger.warning("⚠️ Aucune zone Roon disponible - attente de la mise à jour des zones...")
            # Attendre un peu que les zones soient chargées (jusqu'à 5 secondes)
            import asyncio
            for i in range(5):
                await asyncio.sleep(1)
                zones = self.roon.get_zones()
                if zones:
                    logger.info(f"✅ Zones Roon disponibles: {list(zones.keys())}")
                    break
            
            if not zones:
                logger.error("❌ Impossible de démarrer le tracker Roon: aucune zone disponible après 5s")
                return
        
        interval = self.config.get('roon_tracker', {}).get('interval_seconds', 120)
        
        self.scheduler.add_job(
            self._poll_roon,
            trigger=IntervalTrigger(seconds=interval),
            id='roon_tracker',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info(f"🎵 Tracker Roon démarré (intervalle: {interval}s)")
    
    async def stop(self):
        """Arrêter le tracker."""
        if not self.is_running:
            logger.info("🎵 Tracker Roon n'est pas en cours d'exécution")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("🎵 Tracker Roon arrêté")
    
    def get_status(self) -> dict:
        """Obtenir le statut du tracker."""
        next_run_time = None
        if self.is_running:
            try:
                job = self.scheduler.get_job('roon_tracker')
                if job and job.next_run_time:
                    next_run_time = job.next_run_time.isoformat()
            except Exception as e:
                logger.warning(f"⚠️ Erreur obtention next_run_time: {e}")
        
        # Obtenir les zones de manière sécurisée
        zones_count = 0
        try:
            if self.roon.is_connected():
                zones = self.roon.get_zones()
                zones_count = len(zones) if zones else 0
        except Exception as e:
            logger.warning(f"⚠️ Erreur obtention zones Roon: {e}")
        
        return {
            "running": self.is_running,
            "connected": self.roon.is_connected() if self.roon else False,
            "configured": self.config.get('roon_server') is not None,
            "last_track": self.last_track_key,
            "interval_seconds": self.config.get('roon_tracker', {}).get('interval_seconds', 120),
            "last_poll_time": self.last_poll_time.isoformat() if self.last_poll_time else None,
            "next_run_time": next_run_time,
            "server": self.config.get('roon_server') or self.config.get('roon', {}).get('server'),
            "zones_count": zones_count
        }
    
    async def _poll_roon(self):
        """Interroger Roon et enregistrer les nouveaux tracks."""
        try:
            # Enregistrer l'heure du poll
            self.last_poll_time = datetime.now(timezone.utc)
            
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
            
            if track_key == self.last_track_key:
                logger.debug("Même track qu'avant sur Roon, skip")
                return
            
            self.last_track_key = track_key
            logger.info(f"🎵 Nouveau track Roon détecté: {track_key} (zone: {current_track['zone_name']})")
            
            # Enregistrer en base de données
            await self._save_track(current_track)
            
        except Exception as e:
            logger.error(f"Erreur polling Roon: {e}")
    
    def _check_duplicate(self, db: Session, artist_name: str, track_title: str, album_title: str, source: str) -> bool:
        """Vérifier si le track existe déjà récemment (dans les 5 dernières minutes).
        
        Args:
            db: Session de base de données
            artist_name: Nom de l'artiste
            track_title: Titre du morceau
            album_title: Titre de l'album
            source: Source du tracker ('lastfm' ou 'roon')
            
        Returns:
            True si c'est un doublon, False sinon
        """
        # Timestamp il y a 5 minutes
        five_minutes_ago = int(datetime.now(timezone.utc).timestamp()) - 300
        
        # Chercher le track et l'album correspondant
        track = db.query(Track).join(Album).join(Album.artists).filter(
            Track.title == track_title,
            Album.title == album_title,
            Artist.name == artist_name
        ).first()
        
        if not track:
            return False  # Pas de doublon si le track n'existe pas
        
        # Vérifier si une entrée récente existe pour ce track
        recent_entries = db.query(ListeningHistory).filter(
            ListeningHistory.track_id == track.id,
            ListeningHistory.timestamp >= five_minutes_ago
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
        """Sauvegarder un track en base de données."""
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
            
            # Créer/récupérer album
            album = db.query(Album).filter_by(title=album_title).first()
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
