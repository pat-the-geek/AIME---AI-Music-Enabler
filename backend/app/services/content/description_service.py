"""Service pour générer des descriptions pour albums et tracks."""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import Album, Track, Artist
from app.services.external.ai_service import AIService

logger = logging.getLogger(__name__)


class DescriptionService:
    """Service pour générer des descriptions IA pour albums et tracks."""
    
    @staticmethod
    async def generate_album_description(
        db: Session,
        ai_service: AIService,
        album_id: int
    ) -> Dict[str, Any]:
        """
        Générer une description IA pour un album.
        
        Args:
            db: Session base de données
            ai_service: Service IA
            album_id: ID de l'album
            
        Returns:
            Dict avec description générée
        """
        album = db.query(Album).filter(Album.id == album_id).first()
        if not album:
            raise ValueError(f"Album {album_id} non trouvé")
        
        artists = ', '.join([a.name for a in album.artists]) if album.artists else 'Unknown'
        
        album_info = {
            'album': album.title,
            'artist': artists,
            'year': album.year,
            'genre': album.genre,
            'description': album.ai_description or ''
        }
        
        description = await ai_service.generate_album_description(album_info)
        
        return {
            "album_id": album_id,
            "album": album.title,
            "artist": artists,
            "description": description,
            "generated_at": __import__('datetime').datetime.now().isoformat()
        }
    
    @staticmethod
    async def generate_track_description(
        db: Session,
        ai_service: AIService,
        track_id: int
    ) -> Dict[str, Any]:
        """
        Générer une description IA pour un track.
        
        Args:
            db: Session base de données
            ai_service: Service IA
            track_id: ID du track
            
        Returns:
            Dict avec description générée
        """
        track = db.query(Track).filter(Track.id == track_id).first()
        if not track:
            raise ValueError(f"Track {track_id} non trouvé")
        
        album = track.album
        artists = ', '.join([a.name for a in album.artists]) if album and album.artists else 'Unknown'
        
        track_info = {
            'track': track.title,
            'artist': artists,
            'album': album.title if album else 'Unknown',
            'year': album.year if album else None,
            'genre': album.genre if album else None
        }
        
        description = await ai_service.generate_album_description(track_info)
        
        return {
            "track_id": track_id,
            "track": track.title,
            "artist": artists,
            "album": album.title if album else 'Unknown',
            "description": description,
            "generated_at": __import__('datetime').datetime.now().isoformat()
        }
    
    @staticmethod
    async def generate_collection_name(
        db: Session,
        ai_service: AIService,
        album_ids: Optional[list] = None
    ) -> str:
        """
        Générer un nom pour une collection d'albums.
        
        Args:
            db: Session base de données
            ai_service: Service IA
            album_ids: IDs des albums (si None, utilise tous)
            
        Returns:
            Nom généré pour la collection
        """
        if album_ids:
            albums = db.query(Album).filter(Album.id.in_(album_ids)).all()
        else:
            albums = db.query(Album).limit(50).all()
        
        if not albums:
            raise ValueError("Aucun album trouvé")
        
        # Créer un contexte avec les top albums
        top_albums = [
            f"- {a.title} by {', '.join([art.name for art in a.artists])}"
            for a in albums[:10]
        ]
        
        collection_info = {
            'albums': top_albums,
            'count': len(albums),
            'description': 'Collection personnelle de musique'
        }
        
        name = await ai_service.generate_collection_name(collection_info)
        
        return name.strip()
