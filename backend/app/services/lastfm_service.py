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
    
    async def get_album_artists(self, artist_name: str, album_title: str) -> list:
        """Récupérer les vrais artistes d'un album depuis Last.fm.
        
        Certains albums sont des compilations ou des collaborations.
        Last.fm peut retourner des artistes collaboratifs.
        
        Args:
            artist_name: Artiste principal du track
            album_title: Titre de l'album
            
        Returns:
            Liste des artistes de l'album (peut contenir plusieurs)
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
        """Récupérer l'historique d'écoute d'un utilisateur avec pagination via requête HTTP.
        
        Args:
            limit: Nombre maximum de tracks à récupérer par page (max 200)
            page: Numéro de page (1-based, défaut 1)
            from_timestamp: Timestamp Unix de début (optionnel)
            to_timestamp: Timestamp Unix de fin (optionnel)
            
        Returns:
            Liste de tracks avec timestamps de la page spécifiée
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
        """Obtenir le nombre total de scrobbles de l'utilisateur."""
        try:
            user = pylast.User(self.username, self.network)
            return int(user.get_playcount())
        except Exception as e:
            logger.error(f"Erreur récupération nombre de scrobbles: {e}")
            return 0
