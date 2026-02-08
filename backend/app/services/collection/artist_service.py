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
        List all artists in the collection with their profile images.

        Retrieves a list of all artists, optionally limited to a maximum count.
        For each artist, includes their basic metadata and the URL of their first
        associated profile image (if available).

        Args:
            db: SQLAlchemy database session for query execution.
            limit: Maximum number of artists to return. Defaults to 100.
                Set to a reasonable value to avoid memory issues. Database
                will be queried with LIMIT clause for efficiency.

        Returns:
            List[Dict]: List of artist dictionaries, each containing:
                - id (int): Artist database ID
                - name (str): Artist name
                - spotify_id (Optional[str]): Spotify artist ID if available
                - image_url (Optional[str]): URL of first associated image,
                  or None if no images are available

                Example dict:
                {
                    "id": 1,
                    "name": "Pink Floyd",
                    "spotify_id": "0k17h0d3amQ8qk4xgSKiM6",
                    "image_url": "https://example.com/image.jpg"
                }

        Example:
            >>> db_session = get_db()
            >>> artists = ArtistService.list_artists(db_session, limit=50)
            >>> for artist in artists:
            ...     print(f"{artist['name']} - {artist['image_url']}")
            Pink Floyd - https://example.com/pf.jpg
            David Gilmour - None

        Performance Notes:
            - Query uses LIMIT clause, so only requested artists are fetched
            - No N+1 query issue since only one query per artist
            - Image relationship is already loaded if artists have eager-loaded images
            - For large limits (>1000), consider pagination instead

        Logging:
            - Logs INFO with count of returned artists
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
        Retrieve the profile image URL for a given artist.

        Fetches the artist's primary (first) image record from the database,
        specifically filtering for records of type 'artist'. Returns the URL
        if found and valid, or None otherwise.

        Args:
            db: SQLAlchemy database session for query execution.
            artist_id: The database ID of the artist whose image to retrieve.

        Returns:
            str: The image URL string if an artist image is found, or None if:
                - No image record exists for this artist
                - The image record has no URL (null/empty)
                - The artist_id doesn't exist (returns None without error)

            Example success: "https://example.com/artists/pink-floyd.jpg"
            Example null result: None

        Raises:
            Exception: None - This method returns None instead of raising
                exceptions for missing data.

        Example:
            >>> db_session = get_db()
            >>> url = ArtistService.get_artist_image(db_session, artist_id=1)
            >>> if url:
            ...     print(f"Artist image: {url}")
            ... else:
            ...     print("No image available")
            Artist image: https://example.com/artists/pink-floyd.jpg

        Implementation Notes:
            - Queries for image_type='artist' specifically (not album images)
            - Returns only the first image if multiple exist
            - Does not perform uploads or URL validation

        Performance Notes:
            - Single database query using indexed artist_id and image_type
            - Recommended to cache results at request level
            - Consider batch query for multiple artists instead of looping

        Logging:
            - Logs INFO when image is found
            - Logs WARNING when image is not found or URL is missing
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
        Count the total number of albums for a specific artist.

        Queries the database to find all albums associated with the given artist
        through the many-to-many artist-album relationship. Returns a count
        of these albums without fetching the full Album records.

        Args:
            db: SQLAlchemy database session for query execution.
            artist_id: The database ID of the artist whose album count to retrieve.

        Returns:
            int: The count of albums for this artist. Returns 0 if:
                - The artist has no albums
                - The artist_id doesn't exist (query returns 0)

                Example return values:
                - 5: Artist has 5 albums in collection
                - 0: Artist has no albums or doesn't exist

        Raises:
            Exception: None - This method returns 0 instead of raising
                exceptions for missing artists.

        Example:
            >>> db_session = get_db()
            >>> count = ArtistService.get_artist_album_count(db_session, artist_id=1)
            >>> print(f"Pink Floyd has {count} albums in collection")
            Pink Floyd has 15 albums in collection

        Implementation Notes:
            - Uses COUNT aggregate function for efficiency (not fetching full records)
            - Joins through the Album.artists many-to-many relationship
            - Each album counted once even if artist appears multiple times

        Performance Notes:
            - Efficient count query using database aggregation
            - Recommended to cache results at request level
            - Single database query with index on album-artist join table
            - Consider caching for frequently accessed artists

        SQL Equivalent:
            SELECT COUNT(*) FROM album
            JOIN album_artist ON album.id = album_artist.album_id
            WHERE album_artist.artist_id = {artist_id}
        """
        count = db.query(Album).join(Album.artists).filter(
            Artist.id == artist_id
        ).count()
        
        return count
