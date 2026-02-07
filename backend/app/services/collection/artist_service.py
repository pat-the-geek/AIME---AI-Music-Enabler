"""Service pour la gestion des artistes de la collection."""
import logging
from typing import List, Dict
from sqlalchemy.orm import Session

from app.models import Artist, Image, Album

logger = logging.getLogger(__name__)


class ArtistService:
    """Service pour les opérations sur les artistes."""
    
    @staticmethod
    def list_artists(db: Session, limit: int = 100) -> List[Dict]:
        """
        Lister les artistes avec leurs images.
        
        Args:
            db: Session de base de données
            limit: Nombre maximal d'artistes à retourner
            
        Returns:
            Liste de dictionnaires artiste
        """
        artists = db.query(Artist).limit(limit).all()
        
        result = []
        for artist in artists:
            # Récupérer l'image
            image_url = None
            if artist.images:
                image_url = artist.images[0].url
            
            result.append({
                "id": artist.id,
                "name": artist.name,
                "spotify_id": artist.spotify_id,
                "image_url": image_url
            })
        
        logger.info(f"✅ {len(result)} artistes retournés")
        
        return result
    
    @staticmethod
    def get_artist_image(db: Session, artist_id: int) -> str:
        """
        Récupérer l'image d'un artiste.
        
        Args:
            db: Session de base de données
            artist_id: ID de l'artiste
            
        Returns:
            URL de l'image ou None
        """
        image = db.query(Image).filter(
            Image.artist_id == artist_id,
            Image.image_type == 'artist'
        ).first()
        
        if image and image.url:
            logger.info(f"✅ Image trouvée pour artiste {artist_id}")
            return image.url
        
        logger.warning(f"⚠️ Pas d'image trouvée pour artiste {artist_id}")
        return None
    
    @staticmethod
    def get_artist_album_count(db: Session, artist_id: int) -> int:
        """
        Compter le nombre d'albums d'un artiste.
        
        Args:
            db: Session de base de données
            artist_id: ID de l'artiste
            
        Returns:
            Nombre d'albums
        """
        count = db.query(Album).join(Album.artists).filter(
            Artist.id == artist_id
        ).count()
        
        return count
