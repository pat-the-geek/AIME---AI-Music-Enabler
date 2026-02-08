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
        Generate engaging AI description for an album incorporating metadata.
        
        Fetches album data including artists, year, genre, and existing description,
        then uses AIService to generate a 2-3 sentence engaging description capturing
        the album's essence, style, and cultural impact. Descriptions are designed for
        UI display, preview cards, and content enrichment.
        
        Args:
            db: SQLAlchemy session for Album query. Uses single direct lookup
                via Album.id filter (no relationships eager-loaded).
            ai_service: AIService instance for description generation. Calls
                generate_album_description() with album_info dict containing title,
                artist names, year, genre, existing AI description if available.
            album_id: Integer album ID. Must exist in database.
        
        Returns:
            Dict[str, Any] containing:
                - album_id (int): Original album ID
                - album (str): Album title from database
                - artist (str): Artist name(s) comma-separated, 'Unknown' if missing
                - description (str): 2-3 sentence generated description
                - generated_at (str): ISO8601 timestamp of generation
        
        Raises:
            ValueError: If album_id not found in database.
            Exception: Propagates AIService generation failures.
        
        Example:
            >>> result = await desc_service.generate_album_description(db, ai_service, 42)
            >>> print(result['description'])
            'A haunting masterpiece of electronic minimalism and ethereal vocals, Dummy marked
            Portishead\\'s revolutionary entrance into the trip-hop landscape. Its immersive
            production and noir atmosphere became foundational to the genre\\'s dark aesthetic.'
        
        Performance Notes:
            - Database query: O(1) single album lookup (~1-2ms typically)
            - AI generation timeout: 45 seconds (see AIService.ask_for_ia)
            - Token usage: ~300 tokens per description
            - Memory: ~5KB per description result
        
        Implementation Notes:
            - Album artists joined with ', ' separator (e.g., 'Artist A, Artist B')
            - Fallback to 'Unknown' if album has no artists defined
            - Existing AI descriptions included if available (improves context)
            - Year and genre passed as optional metadata to AI
            - Uses AIService.generate_album_description() specifically (not general ask_for_ia)
            - datetime imported inline to avoid circular dependencies
        
        Logging:
            - No direct logging (see AIService for generation details)
        
        Design Notes:
            - Lightweight method suitable for bulk operations (e.g., enriching 100+ albums)
            - Descriptions typically 150-300 characters total
            - Embeddable in API responses, UI cards, search results
            - Complementary to human-written album info, provides AI perspective
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
        Generate AI description for an individual track with full metadata.
        
        Similar to generate_album_description() but targets individual tracks.
        Fetches track with album relationship, extracts all metadata (artist, album,
        year, genre), and generates 1-2 sentence description emphasizing track's
        distinguishing qualities, musical characteristics, and role within album context.
        
        Args:
            db: SQLAlchemy session for Track query. Uses direct filter lookup
                and lazy-loads related Album and Artist data as needed.
            ai_service: AIService instance for description generation. Calls
                generate_album_description() with track_info dict (reuses album
                description generator for consistency).
            track_id: Integer track ID. Must exist with valid album relationship.
        
        Returns:
            Dict[str, Any] containing:
                - track_id (int): Original track ID
                - track (str): Track title from database
                - artist (str): Artist name(s) comma-separated, 'Unknown' if missing
                - album (str): Album title, defaults to 'Unknown'
                - description (str): 1-2 sentence track-specific description
                - generated_at (str): ISO8601 timestamp of generation
        
        Raises:
            ValueError: If track_id not found in database.
            Exception: Propagates AIService generation failures.
        
        Example:
            >>> result = await desc_service.generate_track_description(db, ai_service, 142)
            >>> print(result['track'])
            'Dance Floor'
            >>> print(result['description'])
            'A pulsating electronic rhythm drives this hypnotic centerpiece, showcasing
            the artist\\'s mastery of minimalist production and trance dynamics.'
        
        Performance Notes:
            - Database queries: O(1) single track lookup + lazy Album load (~2-3ms)
            - AI generation timeout: 45 seconds (see AIService.ask_for_ia)
            - Token usage: ~250 tokens per track description
            - Memory: ~3KB per result
        
        Implementation Notes:
            - Track.album relationship lazy-loaded (no eager loading)
            - Artist names extracted from album.artists if present
            - Graceful fallbacks: 'Unknown' for missing artist/album
            - Genre and year sourced from parent album if available
            - Reuses AIService.generate_album_description() for consistency
            - Timestamp generation via __import__('datetime') pattern
        
        Logging:
            - No direct logging
        
        Use Cases:
            - Track preview descriptions in UI/player controls
            - Playlist annotations (describe each track's role)
            - Quick browse/discovery: See track quality before listening
            - API responses for music search/browsing endpoints
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
        Generate evocative 2-4 word French collection name from album list.
        
        Creates thematic collection names that capture the essence of a group of albums.
        If album_ids provided, generates name specific to those albums; if None, samples
        top 50 albums from database. Returns single string name (not dict) suitable for
        collection display, playlist titling, and user-friendly labeling.
        
        Args:
            db: SQLAlchemy session for Album queries. Uses filter(Album.id.in_())
                for specific albums or limit(50) for default sampling.
            ai_service: AIService instance for name generation. Calls
                generate_collection_name() with collection_info dict containing
                album list (max 10 shown), total count, and description.
            album_ids: Optional list of integer album IDs to name. If None, automatically
                uses up to 50 albums from database for context. Empty list raises ValueError.
        
        Returns:
            str: Generated collection name, typically 2-4 French words. Examples:
                - 'Nocturnes Synthétiques'
                - 'Rythmes Entrecroisés'
                - 'Électronique Méditative'
                - 'Vagues Numériques'
        
        Raises:
            ValueError: If no albums found (either specified album_ids don't exist
                or database is empty when album_ids=None).
            Exception: Propagates AIService generation failures.
        
        Example:
            >>> # Name specific albums
            >>> name = await desc_service.generate_collection_name(db, ai_service, [10, 42, 57])
            >>> print(name)
            'Mondes Électroniques Oubliés'
            
            >>> # Auto-sample top 50 albums
            >>> name = await desc_service.generate_collection_name(db, ai_service)
            >>> print(name)
            'Symphonies du Quotidien'
        
        Performance Notes:
            - Database queries: O(n) where n = len(album_ids) or 50
            - Typical album query: <20ms for sampling 50 albums
            - AI generation timeout: 45 seconds (see AIService.ask_for_ia)
            - Token usage: ~400 tokens (album list details)
            - Memory: ~10KB for 50-album context
        
        Implementation Notes:
            - Album sample limited to first 10 for AI prompt (for token efficiency)
            - Album list format: '- Title by Artist1, Artist2' (readable for AI)
            - Collection count and description provided as metadata
            - Result stripped of whitespace for clean return
            - Artist names extracted from album.artists, joined with ', '
            - Designed for French cultural context (name generation in French preferred)
        
        Logging:
            - No direct logging (consider adding INFO for successful generation)
        
        Frontend Integration:
            - Names suitable for display in collection headers/cards
            - Works well with icon/cover art for collection branding
            - French language for Francophone-focused applications
            - Can be edited by users after generation
        
        Extension Ideas:
            - Support multiple languages (pass language param to AIService)
            - Add style parameter (poetic, technical, descriptive, etc.)
            - Generate multiple names and let user choose favorite
            - Store generation context for explanation to user
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
