"""Service pour les opérations de playback Roon."""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models import Playlist, PlaylistTrack, Album
from app.api.v1.tracking.services import get_roon_service

logger = logging.getLogger(__name__)


class RoonPlaybackService:
    """Service pour les opérations de playback sur Roon."""
    
    @staticmethod
    def play_playlist_on_roon(
        db: Session,
        playlist_id: int,
        zone_name: str
    ) -> Dict[str, Any]:
        """Jouer une playlist sur une zone Roon.
        
        Args:
            db: Session base de données
            playlist_id: ID de la playlist
            zone_name: Nom de la zone Roon
            
        Returns:
            Dict avec statut de la lecture
        """
        try:
            # Récupérer la playlist
            playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
            if not playlist:
                raise ValueError("Playlist non trouvée")
            
            # Récupérer les tracks
            playlist_tracks = db.query(PlaylistTrack).filter(
                PlaylistTrack.playlist_id == playlist_id
            ).order_by(PlaylistTrack.position).all()
            
            if not playlist_tracks:
                raise ValueError("Playlist vide")
            
            # Initialiser Roon
            roon_service = get_roon_service()
            if roon_service is None:
                raise ValueError("Roon non configuré")
            
            if not roon_service.is_connected():
                raise ValueError("Impossible de se connecter à Roon")
            
            # Récupérer l'ID de la zone
            zone_id = roon_service.get_zone_by_name(zone_name)
            if not zone_id:
                available_zones = roon_service.get_zones()
                zone_names = [z.get('display_name', 'Unknown') for z in available_zones.values()]
                raise ValueError(f"Zone '{zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}")
            
            # Jouer le premier track
            first_pt = playlist_tracks[0]
            first_track = first_pt.track
            album = first_track.album
            
            if not album:
                raise ValueError("Album non trouvé pour le premier track")
            
            artists = [a.name for a in album.artists] if album.artists else ["Unknown"]
            artist_name = ", ".join(artists)
            
            success = roon_service.play_track(
                zone_or_output_id=zone_id,
                track_title=first_track.title,
                artist=artist_name,
                album=album.title
            )
            
            if not success:
                raise ValueError("Erreur démarrage lecture sur Roon")
            
            return {
                "message": f"Playlist '{playlist.name}' en lecture sur {zone_name}",
                "playlist_id": playlist_id,
                "track_count": len(playlist_tracks),
                "first_track": first_track.title,
                "zone": zone_name
            }
            
        except ValueError as e:
            logger.error(f"Erreur playback Roon: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur Roon: {e}")
            raise ValueError(f"Erreur Roon: {str(e)}")
    
    @staticmethod
    def play_album_on_roon(
        db: Session,
        album_id: int,
        zone_name: str
    ) -> Dict[str, Any]:
        """Jouer un album sur une zone Roon.
        
        Args:
            db: Session base de données
            album_id: ID de l'album
            zone_name: Nom de la zone Roon
            
        Returns:
            Dict avec statut de la lecture
        """
        try:
            album = db.query(Album).filter(Album.id == album_id).first()
            if not album:
                raise ValueError("Album non trouvé")
            
            roon_service = get_roon_service()
            if roon_service is None:
                raise ValueError("Roon non configuré")
            
            if not roon_service.is_connected():
                raise ValueError("Impossible de se connecter à Roon")
            
            zone_id = roon_service.get_zone_by_name(zone_name)
            if not zone_id:
                available_zones = roon_service.get_zones()
                zone_names = [z.get('display_name', 'Unknown') for z in available_zones.values()]
                raise ValueError(f"Zone '{zone_name}' non trouvée. Zones: {', '.join(zone_names)}")
            
            artists = [a.name for a in album.artists] if album.artists else ["Unknown"]
            artist_name = ", ".join(artists)
            
            success = roon_service.play_track(
                zone_or_output_id=zone_id,
                track_title="",  # Pas de track spécifique, joue l'album entier
                artist=artist_name,
                album=album.title
            )
            
            if not success:
                raise ValueError("Erreur démarrage lecture album")
            
            return {
                "message": f"Album '{album.title}' en lecture sur {zone_name}",
                "album_id": album_id,
                "album": album.title,
                "artist": artist_name,
                "zone": zone_name
            }
            
        except ValueError as e:
            logger.error(f"Erreur playback album: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur Roon album: {e}")
            raise ValueError(f"Erreur Roon: {str(e)}")
    
    @staticmethod
    def get_roon_zones() -> Dict[str, Any]:
        """Récupérer les zones Roon disponibles.
        
        Returns:
            Dict avec zones disponibles
        """
        try:
            roon_service = get_roon_service()
            if roon_service is None:
                raise ValueError("Roon non configuré")
            
            if not roon_service.is_connected():
                raise ValueError("Impossible de se connecter à Roon")
            
            zones = roon_service.get_zones()
            zone_list = [
                {
                    "id": zone_id,
                    "name": zone.get('display_name', 'Unknown'),
                    "is_primary": zone.get('is_primary', False)
                }
                for zone_id, zone in zones.items()
            ]
            
            return {
                "zones": zone_list,
                "total": len(zone_list)
            }
            
        except ValueError as e:
            logger.error(f"Erreur zones Roon: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur Roon zones: {e}")
            raise ValueError(f"Erreur Roon: {str(e)}")
    
    @staticmethod
    def get_now_playing(zone_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Récupérer le morceau en cours de lecture.
        
        Args:
            zone_name: Nom de la zone (optionnel, utilise la zone primaire sinon)
            
        Returns:
            Dict avec infos du morceau ou None
        """
        try:
            roon_service = get_roon_service()
            if roon_service is None:
                return None
            
            if not roon_service.is_connected():
                return None
            
            zones = roon_service.get_zones()
            if not zones:
                return None
            
            if zone_name:
                zone_id = roon_service.get_zone_by_name(zone_name)
                if not zone_id:
                    return None
            else:
                # Utiliser la zone primaire
                zone_id = None
                for zid, z in zones.items():
                    if z.get('is_primary'):
                        zone_id = zid
                        break
                
                if not zone_id:
                    zone_id = list(zones.keys())[0]
            
            zone = zones.get(zone_id)
            if not zone or not zone.get('now_playing'):
                return None
            
            now_playing = zone.get('now_playing', {})
            
            return {
                "zone": zone.get('display_name'),
                "artist": now_playing.get('three_line', {}).get('line1', ''),
                "album": now_playing.get('three_line', {}).get('line2', ''),
                "track": now_playing.get('three_line', {}).get('line3', ''),
                "seek_position": zone.get('seek_position', 0),
                "length": zone.get('length', 0)
            }
            
        except Exception as e:
            logger.error(f"Erreur now_playing: {e}")
            return None
