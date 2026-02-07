"""Service pour générer des haikus basés sur l'historique d'écoute."""
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy.orm import Session

from app.models import ListeningHistory, Track, Album
from app.services.external.ai_service import AIService

logger = logging.getLogger(__name__)


class HaikuService:
    """Service pour générer des haikus à partir de l'historique d'écoute."""
    
    @staticmethod
    async def generate_haiku(db: Session, ai_service: AIService, days: int = 7) -> Dict[str, Any]:
        """
        Générer un haïku basé sur l'historique d'écoute récent.
        
        Args:
            db: Session base de données
            ai_service: Service IA pour génération
            days: Nombre de jours à analyser (1-365)
            
        Returns:
            Dict avec haïku et métadonnées
        """
        # Analyser l'historique récent
        cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
        recent_history = db.query(ListeningHistory).join(Track).join(Album).join(
            Album.artists
        ).filter(
            ListeningHistory.timestamp >= cutoff_timestamp
        ).all()
        
        if not recent_history:
            raise ValueError("Pas d'historique d'écoute récent")
        
        # Extraire top artistes et albums
        artists = Counter()
        albums = Counter()
        for entry in recent_history:
            track = entry.track
            album = track.album
            if album and album.artists:
                for artist in album.artists:
                    artists[artist.name] += 1
            if album:
                albums[album.title] += 1
        
        listening_data = {
            'top_artists': [name for name, _ in artists.most_common(5)],
            'top_albums': [title for title, _ in albums.most_common(5)],
            'total_tracks': len(recent_history),
            'days': days
        }
        
        # Générer haïku avec l'IA
        haiku = await ai_service.generate_haiku(listening_data)
        
        return {
            "haiku": haiku,
            "period_days": days,
            "total_tracks": len(recent_history),
            "top_artists": listening_data['top_artists'],
            "top_albums": listening_data['top_albums']
        }
    
    @staticmethod
    async def generate_multiple_haikus(
        db: Session, 
        ai_service: AIService,
        album_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Générer des haikus pour plusieurs albums.
        
        Args:
            db: Session base de données
            ai_service: Service IA
            album_ids: Liste des IDs d'albums
            
        Returns:
            Liste des haikus générés
        """
        haikus = []
        for album_id in album_ids:
            album = db.query(Album).filter(Album.id == album_id).first()
            if not album:
                continue
            
            album_data = {
                'album': album.title,
                'artist': ', '.join([a.name for a in album.artists]) if album.artists else 'Unknown',
                'year': album.year,
                'genre': album.genre
            }
            
            try:
                haiku = await ai_service.generate_haiku(album_data)
                haikus.append({
                    "album_id": album_id,
                    "album": album.title,
                    "haiku": haiku
                })
            except Exception as e:
                logger.error(f"Erreur génération haiku album {album_id}: {e}")
                continue
        
        return haikus
