"""Service de gestion de queue de playlist avec enchaînement automatique."""
import logging
import threading
import time
from typing import Optional, List, Dict, Callable
from app.services.roon_service import RoonService

logger = logging.getLogger(__name__)


class PlaylistQueueManager:
    """Gère l'enchaînement automatique des morceaux d'une playlist."""
    
    def __init__(self, roon_service: RoonService):
        """Initialiser le gestionnaire de queue.
        
        Args:
            roon_service: Instance du service Roon
        """
        self.roon_service = roon_service
        self.active_queues: Dict[str, 'PlaylistQueue'] = {}  # zone_id -> PlaylistQueue
        self.lock = threading.Lock()
    
    def start_playlist_queue(self, 
                           zone_id: str, 
                           tracks: List[Dict],
                           on_track_started: Optional[Callable[[Dict], None]] = None,
                           on_queue_complete: Optional[Callable[[], None]] = None) -> 'PlaylistQueue':
        """Démarrer une queue de playlist avec enchaînement automatique.
        
        Args:
            zone_id: ID de la zone Roon
            tracks: Liste des tracks avec structure:
                [
                    {
                        'title': 'Track Title',
                        'artist': 'Artist Name',
                        'album': 'Album Name',
                        'duration_seconds': 180  # optionnel
                    },
                    ...
                ]
            on_track_started: Callback appelé quand un nouveau track démarre
            on_queue_complete: Callback appelé quand la queue est complète
        
        Returns:
            Instance de PlaylistQueue pour contrôle/monitoring
        """
        with self.lock:
            # Arrêter la queue existante pour cette zone
            if zone_id in self.active_queues:
                old_queue = self.active_queues[zone_id]
                old_queue.stop()
            
            # Créer et démarrer une nouvelle queue
            queue = PlaylistQueue(
                zone_id=zone_id,
                tracks=tracks,
                roon_service=self.roon_service,
                on_track_started=on_track_started,
                on_queue_complete=on_queue_complete
            )
            
            self.active_queues[zone_id] = queue
            queue.start()
            
            return queue
    
    def stop_queue(self, zone_id: str):
        """Arrêter la queue pour une zone.
        
        Args:
            zone_id: ID de la zone
        """
        with self.lock:
            if zone_id in self.active_queues:
                queue = self.active_queues[zone_id]
                queue.stop()
                del self.active_queues[zone_id]
    
    def get_queue_status(self, zone_id: str) -> Optional[Dict]:
        """Récupérer le statut de la queue pour une zone.
        
        Args:
            zone_id: ID de la zone
        
        Returns:
            Dictionnaire avec statut ou None
        """
        with self.lock:
            if zone_id in self.active_queues:
                return self.active_queues[zone_id].get_status()
        return None


class PlaylistQueue:
    """Gère l'enchaînement des tracks d'une playlist avec synchronisation temporelle."""
    
    def __init__(self,
                 zone_id: str,
                 tracks: List[Dict],
                 roon_service: RoonService,
                 on_track_started: Optional[Callable[[Dict], None]] = None,
                 on_queue_complete: Optional[Callable[[], None]] = None):
        """Initialiser une queue de playlist.
        
        Args:
            zone_id: ID de la zone Roon
            tracks: Liste des tracks à jouer
            roon_service: Service Roon
            on_track_started: Callback quand un track démarre
            on_queue_complete: Callback quand la queue est terminée
        """
        self.zone_id = zone_id
        self.tracks = tracks
        self.roon_service = roon_service
        self.on_track_started = on_track_started
        self.on_queue_complete = on_queue_complete
        
        self.current_track_index = 0
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.start_time: Optional[float] = None
    
    def start(self):
        """Démarrer le gestionnaire de queue."""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_queue, daemon=True)
        self.thread.start()
        
        logger.info(f"🎵 Queue de playlist démarrée pour la zone {self.zone_id}")
        logger.info(f"   {len(self.tracks)} tracks en attente")
    
    def stop(self):
        """Arrêter le gestionnaire de queue."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info(f"🛑 Queue de playlist arrêtée pour la zone {self.zone_id}")
    
    def _run_queue(self):
        """Boucle principale de gestion de la queue."""
        try:
            for idx, track in enumerate(self.tracks):
                if not self.is_running:
                    break
                
                self.current_track_index = idx
                
                # Jouer le track
                logger.info(f"🎵 Lecture track {idx + 1}/{len(self.tracks)}: {track.get('title', 'Unknown')}")
                
                success = self.roon_service.play_track(
                    zone_or_output_id=self.zone_id,
                    track_title=track.get('title', ''),
                    artist=track.get('artist', ''),
                    album=track.get('album', '')
                )
                
                if success:
                    # Callback quand le track démarre
                    if self.on_track_started:
                        try:
                            self.on_track_started(track)
                        except Exception as e:
                            logger.error(f"Erreur callback on_track_started: {e}")
                    
                    # Attendre la fin du track
                    self._wait_for_track_end(track, idx)
                else:
                    logger.warning(f"⚠️ Impossible de jouer le track: {track.get('title', 'Unknown')}")
                    # Attendre un peu avant le suivant
                    time.sleep(2)
            
            # Queue terminée
            logger.info(f"✅ Queue de playlist terminée (zone: {self.zone_id})")
            if self.on_queue_complete:
                try:
                    self.on_queue_complete()
                except Exception as e:
                    logger.error(f"Erreur callback on_queue_complete: {e}")
        
        except Exception as e:
            logger.error(f"❌ Erreur gestion queue: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        finally:
            self.is_running = False
    
    def _wait_for_track_end(self, track: Dict, track_index: int):
        """Attendre la fin du track avant de lancer le suivant.
        
        Utilise la durée du track si disponible, sinon scrute Roon toutes les 5 secondes.
        
        Args:
            track: Données du track
            track_index: Index du track dans la playlist
        """
        duration = track.get('duration_seconds')
        
        if duration and duration > 0:
            # Cas idéal: on connaît la durée exacte
            logger.info(f"   ⏱️  Durée: {duration}s")
            
            # Attendre la durée avec possibilité d'interruption
            start_time = time.time()
            while self.is_running and (time.time() - start_time) < duration:
                time.sleep(1)
        else:
            # Cas fallback: scruter Roon toutes les 5 secondes
            logger.info(f"   ⏱️  Durée inconnue, scrutation toutes les 5s...")
            
            # Attendre un minimum de 2 secondes
            time.sleep(2)
            
            # Scruter le now_playing pour voir si le track a changé
            max_wait = 300  # Maximum 5 minutes si pas de durée
            start_time = time.time()
            
            while self.is_running and (time.time() - start_time) < max_wait:
                try:
                    now_playing = self.roon_service.get_now_playing()
                    
                    if now_playing:
                        current_title = now_playing.get('title', '')
                        current_artist = now_playing.get('artist', '')
                        
                        # Vérifier si on a changé de track
                        expected_title = track.get('title', '').lower()
                        current_title_lower = current_title.lower()
                        
                        if expected_title and current_title_lower != expected_title:
                            # Le track a changé ou est terminé
                            logger.info(f"   ✅ Track terminé, prochain en attente...")
                            break
                    
                    # Scruter tous les 5 secondes
                    time.sleep(5)
                
                except Exception as e:
                    logger.debug(f"Erreur vérification now_playing: {e}")
                    time.sleep(5)
    
    def get_status(self) -> Dict:
        """Récupérer le statut actuel de la queue.
        
        Returns:
            Dictionnaire avec statut de la queue
        """
        return {
            'zone_id': self.zone_id,
            'is_running': self.is_running,
            'current_track_index': self.current_track_index,
            'total_tracks': len(self.tracks),
            'current_track': self.tracks[self.current_track_index] if self.current_track_index < len(self.tracks) else None,
            'tracks_remaining': len(self.tracks) - self.current_track_index - 1
        }
