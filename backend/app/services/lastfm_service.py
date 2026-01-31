"""Service Last.fm pour le tracking d'écoute."""
import pylast
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LastFMService:
    """Client pour l'API Last.fm."""
    
    def __init__(self, api_key: str, api_secret: str, username: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.username = username
        self.network = pylast.LastFMNetwork(
            api_key=api_key,
            api_secret=api_secret,
            username=username
        )
    
    def get_now_playing(self) -> Optional[Dict[str, Any]]:
        """Obtenir le track en cours de lecture."""
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
        """Récupérer les tracks récents."""
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
        """Récupérer l'image d'un album depuis Last.fm."""
        try:
            album = pylast.Album(artist_name, album_title, self.network)
            image_url = album.get_cover_image()
            return image_url if image_url else None
            
        except Exception as e:
            logger.error(f"Erreur récupération image album Last.fm: {e}")
            return None
    
    def get_user_history(self, limit: int = 200, from_timestamp: Optional[int] = None, to_timestamp: Optional[int] = None) -> list:
        """Récupérer l'historique complet d'écoute d'un utilisateur.
        
        Args:
            limit: Nombre maximum de tracks à récupérer par page (max 200)
            from_timestamp: Timestamp Unix de début (optionnel)
            to_timestamp: Timestamp Unix de fin (optionnel)
            
        Returns:
            Liste de tracks avec timestamps
        """
        try:
            user = pylast.User(self.username, self.network)
            
            # Utiliser la méthode get_recent_tracks avec time_from et time_to
            kwargs = {'limit': min(limit, 200)}  # Last.fm limite à 200 par page
            if from_timestamp:
                kwargs['time_from'] = from_timestamp
            if to_timestamp:
                kwargs['time_to'] = to_timestamp
            
            recent_tracks = user.get_recent_tracks(**kwargs)
            
            tracks = []
            for played_track in recent_tracks:
                # Vérifier si le track a un timestamp (n'est pas "now playing")
                if not hasattr(played_track, 'timestamp') or not played_track.timestamp:
                    continue
                
                track_info = {
                    "artist": str(played_track.track.artist),
                    "title": str(played_track.track.title),
                    "album": str(played_track.album) if hasattr(played_track, 'album') and played_track.album else "Unknown",
                    "timestamp": int(played_track.timestamp),
                    "playback_date": played_track.playback_date
                }
                tracks.append(track_info)
            
            logger.info(f"✅ Récupéré {len(tracks)} tracks depuis Last.fm")
            return tracks
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération historique Last.fm: {e}")
            return []
    
    def get_total_scrobbles(self) -> int:
        """Obtenir le nombre total de scrobbles de l'utilisateur."""
        try:
            user = pylast.User(self.username, self.network)
            return int(user.get_playcount())
        except Exception as e:
            logger.error(f"Erreur récupération nombre de scrobbles: {e}")
            return 0
