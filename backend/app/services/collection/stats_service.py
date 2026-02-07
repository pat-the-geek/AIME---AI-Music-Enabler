"""Service pour les statistiques de la collection."""
import logging
from typing import Dict
from sqlalchemy.orm import Session

from app.models import Album, Artist, Metadata

logger = logging.getLogger(__name__)


class CollectionStatsService:
    """Service pour les statistiques de la collection."""
    
    @staticmethod
    def get_stats(db: Session) -> Dict:
        """
        Récupérer les statistiques de la collection Discogs.
        
        Args:
            db: Session de base de données
            
        Returns:
            Dictionnaire avec les statistiques
        """
        # Stats sur les albums Discogs uniquement
        total_albums = db.query(Album).filter(Album.source == 'discogs').count()
        total_artists = db.query(Artist).distinct(Artist.id).join(Album.artists).filter(
            Album.source == 'discogs'
        ).count()
        
        # Par support (Discogs uniquement)
        supports = db.query(Album.support, db.func.count(Album.id)).filter(
            Album.source == 'discogs'
        ).group_by(Album.support).all()
        
        # Soundtracks
        soundtracks = db.query(Metadata).filter(
            Metadata.film_title.isnot(None)
        ).join(Album).filter(Album.source == 'discogs').count()
        
        logger.info(f"✅ Stats: {total_albums} albums, {total_artists} artistes")
        
        return {
            "collection": "discogs",
            "total_albums": total_albums,
            "total_artists": total_artists,
            "by_support": {s[0] or "Unknown": s[1] for s in supports},
            "soundtracks": soundtracks
        }
    
    @staticmethod
    def get_source_stats(db: Session) -> Dict:
        """
        Récupérer les statistiques par source d'albums.
        
        Args:
            db: Session de base de données
            
        Returns:
            Dictionnaire avec les statistiques par source
        """
        # Stats par source
        stats = db.query(Album.source, db.func.count(Album.id)).group_by(Album.source).all()
        
        result = {}
        for source, count in stats:
            result[source or 'unknown'] = count
        
        # Stats supplémentaires pour les supports
        discogs_supports = db.query(Album.support, db.func.count(Album.id)).filter(
            Album.source == 'discogs'
        ).group_by(Album.support).all()
        
        listening_sources = {
            'lastfm': db.query(Album).filter(Album.source == 'lastfm').count(),
            'roon': db.query(Album).filter(Album.source == 'roon').count(),
            'spotify': db.query(Album).filter(Album.source == 'spotify').count(),
            'manual': db.query(Album).filter(Album.source == 'manual').count(),
        }
        
        logger.info(f"✅ Source stats: {len(result)} sources, total {sum(result.values())} albums")
        
        return {
            "by_source": result,
            "discogs_supports": {s[0] or "unknown": s[1] for s in discogs_supports},
            "listening_sources": listening_sources,
            "total_albums": db.query(Album).count()
        }
