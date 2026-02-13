"""Service pour la gestion des albums de la collection."""
import logging
import math
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload

from app.models import Album, Artist, Image, Metadata
from app.schemas import AlbumCreate, AlbumUpdate, AlbumResponse, AlbumDetail
from app.core.exceptions import ResourceNotFoundException, ValidationException

logger = logging.getLogger(__name__)


class AlbumService:
    """Service pour les opérations CRUD sur les albums."""
    
    @staticmethod
    def list_albums(
        db: Session,
        page: int = 1,
        page_size: int = 30,
        search: Optional[str] = None,
        support: Optional[str] = None,
        year: Optional[int] = None,
        is_soundtrack: Optional[bool] = None,
        source: Optional[str] = None
    ) -> tuple[List[AlbumResponse], int, int]:
        """
        List albums with pagination, filtering, and search capabilities.

        Retrieves a paginated list of albums from the collection with optional
        filters for media type, year, soundtrack status, and source. Supports
        full-text search across album titles and artist names.

        Args:
            db: SQLAlchemy database session for query execution.
            page: Page number (1-indexed). Defaults to 1.
            page_size: Number of albums per page. Defaults to 30. Max recommended: 100.
            search: Optional search string to filter by album title or artist name.
                Case-insensitive substring match.
            support: Optional media type filter (e.g., 'Vinyle', 'CD', 'Digital').
                Must match exactly one of the defined album supports.
            year: Optional release year filter. Matches exact year value.
            is_soundtrack: Optional filter for soundtrack status. If True, returns only
                albums with associated film metadata. If False, excludes soundtracks.
            source: Optional data source filter. Defaults to 'discogs' if not specified.
                Valid values: 'discogs', 'lastfm', 'spotify', 'manual'.

        Returns:
            A tuple containing:
                - items (List[AlbumResponse]): Formatted album list for the requested page.
                - total (int): Total number of albums matching all filters.
                - pages (int): Total number of pages available.

        Raises:
            Exception: If database query fails or session is invalid.

        Example:
            >>> db_session = get_db()
            >>> albums, total, pages = AlbumService.list_albums(
            ...     db=db_session,
            ...     page=1,
            ...     page_size=20,
            ...     search="Pink Floyd",
            ...     year=1973,
            ...     support="Vinyle"
            ... )
            >>> print(f"Found {total} albums, page 1 of {pages}")
            Found 3 albums, page 1 of 1
            >>> for album in albums:
            ...     print(f"{album.title} ({album.year}) - {', '.join(album.artists)}")
            The Dark Side of the Moon (1973) - Pink Floyd

        Performance Notes:
            - Index on Album.source, Album.year, and Album.title recommended for
              queries with filters.
            - Search queries using ilike() may be slow on large datasets. Consider
              full-text search indexes for production deployments.
            - Results are limited to page_size items; use pagination for large
              result sets to minimize memory usage.
        """
        # Requête de base
        query = db.query(Album)
        
        # Filtre source par défaut si pas spécifié
        if source is None:
            query = query.filter(Album.source == 'discogs')
        elif source:
            query = query.filter(Album.source == source)
        
        # Recherche
        if search:
            query = query.join(Album.artists).filter(
                (Album.title.ilike(f"%{search}%")) | (Artist.name.ilike(f"%{search}%"))
            )
        
        # Filtres
        if support:
            query = query.filter(Album.support == support)
        
        if year:
            query = query.filter(Album.year == year)
        
        if is_soundtrack is not None:
            query = query.outerjoin(Album.album_metadata).filter(
                Metadata.film_title.isnot(None) if is_soundtrack else Metadata.film_title.is_(None)
            )
        
        # Total
        total = query.count()
        pages = math.ceil(total / page_size) if total > 0 else 0
        
        # Pagination
        offset = (page - 1) * page_size
        albums = query.offset(offset).limit(page_size).all()
        
        # Formater la réponse
        items = AlbumService._format_album_list(albums)
        
        return items, total, pages
    
    @staticmethod
    def get_album(db: Session, album_id: int) -> AlbumDetail:
        """
        Retrieve a single album with complete details and metadata.

        Fetches a complete album record including all associated images, artists,
        metadata, and AI-generated descriptions. Performs eager loading of related
        entities to minimize database queries. Also retrieves artist profile images
        associated with each artist.

        Args:
            db: SQLAlchemy database session for query execution.
            album_id: The unique database ID of the album to retrieve.

        Returns:
            AlbumDetail: A complete album object with:
                - Basic metadata: id, title, year, support
                - External URLs: discogs_url, spotify_url, discogs_id
                - Related data: artists list, album images, artist_images dict
                - AI metadata: ai_info description, labels, resume
                - Film data (if soundtrack): film_title, film_year, film_director
                - Timestamps: created_at, updated_at

        Raises:
            Exception: If album_id does not exist in the database.
                Message format: "Album {album_id} non trouvé"

        Example:
            >>> db_session = get_db()
            >>> album = AlbumService.get_album(db_session, album_id=42)
            >>> print(f"{album.title} by {', '.join(album.artists)}")
            The Dark Side of the Moon by Pink Floyd
            >>> print(f"AI Description: {album.ai_info}")
            >>> if album.film_title:
            ...     print(f"Soundtrack for: {album.film_title}")

        Performance Notes:
            - Uses eager loading (joinedload) to fetch images and artists in single
              query, avoiding N+1 query problem.
            - Artist images are fetched separately and may result in one query per
              artist. Consider caching for large artist lists.
            - Recommended to cache results at request level for repeated access.

        Logging:
            - Logs INFO when artist image is found
            - Logs WARNING when artist image is missing
            - Logs INFO when album is successfully retrieved
        """
        album = db.query(Album).options(
            joinedload(Album.images),
            joinedload(Album.artists)
        ).filter(Album.id == album_id).first()
        
        if not album:
            return None
        
        # Récupérer les images d'artiste
        artist_images = {}
        for artist in album.artists:
            artist_image = db.query(Image).filter(
                Image.artist_id == artist.id,
                Image.image_type == 'artist'
            ).first()
            
            if artist_image and artist_image.url:
                artist_images[artist.name] = artist_image.url
                logger.info(f"✅ Image trouvée pour {artist.name}: {artist_image.url[:60]}...")
            else:
                logger.warning(f"⚠️ Pas d'image artiste trouvée pour '{artist.name}' (ID: {artist.id})")
        
        # Récupérer les métadonnées
        ai_info = album.ai_description  # Colonne principale
        resume = None
        labels = None
        film_title = None
        film_year = None
        film_director = None
        
        if album.album_metadata:
            if not ai_info:
                ai_info = album.album_metadata.ai_info
            resume = album.album_metadata.resume
            labels = album.album_metadata.labels.split(',') if album.album_metadata.labels else None
            film_title = album.album_metadata.film_title
            film_year = album.album_metadata.film_year
            film_director = album.album_metadata.film_director
        
        logger.info(f"📤 Retour pour album {album_id}: {album.title}")
        
        return AlbumDetail(
            id=album.id,
            title=album.title,
            year=album.year,
            support=album.support,
            discogs_id=album.discogs_id,
            spotify_url=album.spotify_url,
            discogs_url=album.discogs_url,
            artists=[a.name for a in album.artists],
            images=[img.url for img in album.images],
            ai_info=ai_info,
            resume=resume,
            labels=labels,
            film_title=film_title,
            film_year=film_year,
            film_director=film_director,
            artist_images=artist_images,
            created_at=album.created_at,
            updated_at=album.updated_at
        )
    
    @staticmethod
    def create_album(db: Session, album_data: AlbumCreate) -> AlbumResponse:
        """
        Create a new album in the collection.

        Creates a new Album record with the provided metadata and associates it
        with the specified artists. All referenced artists must exist in the
        database before album creation. The created album may not have images
        or AI metadata yet; these are added via separate services.

        Args:
            db: SQLAlchemy database session for transaction management.
            album_data: AlbumCreate schema with:
                - title (str): Album name
                - year (int): Release year
                - support (str): Media type (Vinyle, CD, Digital, etc.)
                - artist_ids (List[int]): IDs of artists for this album
                - discogs_id (Optional[str]): Discogs catalog ID
                - spotify_url (Optional[str]): Spotify album URL
                - discogs_url (Optional[str]): Discogs album URL

        Returns:
            AlbumResponse: The newly created album with:
                - id: Auto-generated database ID
                - All provided metadata
                - Empty images list (added later)
                - Null ai_info (added by AI service)
                - Timestamps set to current time

        Raises:
            Exception: If one or more artist_ids do not exist in the database.
                Message: "Un ou plusieurs artistes non trouvés"

        Example:
            >>> db_session = get_db()
            >>> album_create = AlbumCreate(
            ...     title="The Dark Side of the Moon",
            ...     year=1973,
            ...     support="Vinyle",
            ...     artist_ids=[1],  # Pink Floyd
            ...     discogs_id="353504",
            ...     spotify_url="https://open.spotify.com/album/..."
            ... )
            >>> new_album = AlbumService.create_album(db_session, album_create)
            >>> print(f"Created album ID: {new_album.id}")
            Created album ID: 101

        Raises:
            Exception: If any referenced artist does not exist.

        Performance Notes:
            - Validates all artist IDs with a single database query
            - Performs single INSERT on success (atomic operation)
            - Recommended to commit transaction immediately after creation

        Logging:
            - Logs INFO with album title and ID on successful creation
        """
        # Vérifier que les artistes existent
        artists = db.query(Artist).filter(Artist.id.in_(album_data.artist_ids)).all()
        
        if len(artists) != len(album_data.artist_ids):
            raise ValueError("Un ou plusieurs artistes non trouvés")
        
        # Créer l'album
        album = Album(
            title=album_data.title,
            year=album_data.year,
            support=album_data.support,
            discogs_id=album_data.discogs_id,
            spotify_url=album_data.spotify_url,
            discogs_url=album_data.discogs_url
        )
        album.artists = artists
        
        db.add(album)
        db.commit()
        db.refresh(album)
        
        logger.info(f"✅ Album créé: {album.title} (ID: {album.id})")
        
        return AlbumResponse(
            id=album.id,
            title=album.title,
            year=album.year,
            support=album.support,
            discogs_id=album.discogs_id,
            spotify_url=album.spotify_url,
            discogs_url=album.discogs_url,
            genre=album.genre,
            artists=[a.name for a in album.artists],
            images=[],
            ai_info=None,
            created_at=album.created_at,
            updated_at=album.updated_at
        )
    
    @staticmethod
    def update_album(db: Session, album_id: int, album_data: AlbumUpdate) -> AlbumResponse:
        """
        Update all or multiple fields of an existing album (full replacement).

        Performs a full update operation where each field in album_data replaces
        the corresponding database field (if provided). Only non-None values are
        updated. To modify associated artists, provide all artist IDs you want
        (this replaces the entire artist association list).

        Args:
            db: SQLAlchemy database session for transaction management.
            album_id: Database ID of the album to update.
            album_data: AlbumUpdate schema with fields to update:
                - title (Optional[str]): New album name
                - year (Optional[int]): New release year
                - support (Optional[str]): New media type
                - artist_ids (Optional[List[int]]): Replace artist associations
                - discogs_id (Optional[str]): New Discogs ID
                - spotify_url (Optional[str]): New Spotify URL
                - discogs_url (Optional[str]): New Discogs URL

        Returns:
            AlbumResponse: The updated album with new values and updated_at timestamp.

        Raises:
            Exception: If album_id does not exist.
                Message: "Album {album_id} non trouvé"
            Exception: If any referenced artist_id does not exist.
                Message: "Un ou plusieurs artistes non trouvés"

        Example:
            >>> db_session = get_db()
            >>> update_data = AlbumUpdate(
            ...     year=1973,
            ...     spotify_url="https://open.spotify.com/album/..."
            ... )
            >>> updated = AlbumService.update_album(db_session, 42, update_data)
            >>> print(f"Album updated at: {updated.updated_at}")

        Important Notes:
            - Providing artist_ids replaces ALL associations; no merge occurs
            - Use patch_album() for partial updates to avoid overwriting unintended fields
            - None values are ignored; omit fields to leave them unchanged

        Logging:
            - Logs INFO with album title and ID on successful update
        """
        album = db.query(Album).filter(Album.id == album_id).first()
        
        if not album:
            raise ValueError(f"Album {album_id} non trouvé")
        
        # Mettre à jour les champs
        if album_data.title is not None:
            album.title = album_data.title
        if album_data.year is not None:
            album.year = album_data.year
        if album_data.support is not None:
            album.support = album_data.support
        if album_data.discogs_id is not None:
            album.discogs_id = album_data.discogs_id
        if album_data.spotify_url is not None:
            album.spotify_url = album_data.spotify_url
        if album_data.discogs_url is not None:
            album.discogs_url = album_data.discogs_url
        if album_data.genre is not None:
            album.genre = album_data.genre
        
        if album_data.artist_ids is not None:
            artists = db.query(Artist).filter(Artist.id.in_(album_data.artist_ids)).all()
            if len(artists) != len(album_data.artist_ids):
                raise ValueError("Un ou plusieurs artistes non trouvés")
            album.artists = artists
        
        db.commit()
        db.refresh(album)
        
        logger.info(f"✅ Album mis à jour: {album.title} (ID: {album.id})")
        
        return AlbumResponse(
            id=album.id,
            title=album.title,
            year=album.year,
            support=album.support,
            discogs_id=album.discogs_id,
            spotify_url=album.spotify_url,
            discogs_url=album.discogs_url,
            genre=album.genre,
            artists=[a.name for a in album.artists],
            images=[img.url for img in album.images],
            ai_info=album.album_metadata.ai_info if album.album_metadata else None,
            created_at=album.created_at,
            updated_at=album.updated_at
        )
    
    @staticmethod
    def patch_album(db: Session, album_id: int, patch_data: dict) -> dict:
        """
        Apply a partial/selective update to an existing album (PATCH semantics).

        Applies JSON Patch (RFC 6902) semantics where only the fields present in
        patch_data are modified. This is useful for updating single fields without
        requiring all other fields. Currently supports spotify_url; extend this
        method to support additional fields as needed.

        Args:
            db: SQLAlchemy database session for transaction management.
            album_id: Database ID of the album to patch.
            patch_data: Dictionary containing only the fields to update.
                Example: {"spotify_url": "https://..."}
                Only fields present in this dict will be modified.

        Returns:
            Dictionary response containing:
                - id (int): The album ID
                - spotify_url (str): The new Spotify URL value
                - message (str): Confirmation message

        Raises:
            Exception: If album_id does not exist in the database.
                Message: "Album {album_id} non trouvé"

        Example:
            >>> db_session = get_db()
            >>> result = AlbumService.patch_album(
            ...     db_session,
            ...     album_id=42,
            ...     patch_data={"spotify_url": "https://open.spotify.com/album/..."}
            ... )
            >>> print(result["message"])
            Album mis à jour

        Differences from update_album():
            - Supports partial updates (only specified fields changed)
            - Does not require full AlbumUpdate schema
            - Returns minimal response dict instead of full AlbumResponse
            - More efficient for single-field updates

        Supported Fields:
            - spotify_url: Spotify album URL

        To-Do:
            - Extend to support additional fields (title, year, support, etc.)
            - Add validation rules per field
            - Consider generic field-based implementation

        Logging:
            - Logs INFO with album title and ID on successful patch
        """
        album = db.query(Album).filter(Album.id == album_id).first()
        
        if not album:
            raise ResourceNotFoundException(resource="Album", resource_id=str(album_id))
        
        # Mettre à jour uniquement les champs fournis
        if 'spotify_url' in patch_data:
            album.spotify_url = patch_data['spotify_url']
        
        db.commit()
        db.refresh(album)
        
        logger.info(f"✅ Album patché: {album.title} (ID: {album.id})")
        
        return {
            "id": album.id,
            "spotify_url": album.spotify_url,
            "message": "Album mis à jour"
        }
    
    @staticmethod
    def delete_album(db: Session, album_id: int) -> None:
        """
        Permanently delete an album from the collection.

        Removes the album record from the database along with all associated
        relationships (images, metadata associations). This is a destructive
        operation that cannot be undone without restoring from backups.
        Associated images and artist records are NOT deleted, only the
        Album record itself.

        Args:
            db: SQLAlchemy database session for transaction management.
            album_id: Database ID of the album to delete.

        Returns:
            None: Operation completes silently on success.

        Raises:
            Exception: If album_id does not exist in the database.
                Message: "Album {album_id} non trouvé"

        Example:
            >>> db_session = get_db()
            >>> try:
            ...     AlbumService.delete_album(db_session, album_id=999)
            ... except Exception as e:
            ...     print(f"Error: {e}")
            ... else:
            ...     print("Album deleted successfully")

        Important Notes:
            - This operation is not reversible
            - Cascade delete rules defined in Album model determine what else
              is deleted (typically only the Album record itself)
            - Images and metadata records may remain orphaned if cascades
              are not properly configured
            - Consider soft deletes (marking is_deleted=True) for data integrity

        What is NOT deleted:
            - Associated Artist records (remain in database)
            - Associated Image records (unless cascade delete configured)
            - Album metadata records (unless cascade delete configured)

        Logging:
            - Logs INFO with album title and ID on successful deletion
        """
        album = db.query(Album).filter(Album.id == album_id).first()
        
        if not album:
            return False
        
        album_title = album.title
        db.delete(album)
        db.commit()
        
        logger.info(f"✅ Album supprimé: {album_title} (ID: {album_id})")
        return True
    
    @staticmethod
    def bulk_update(db: Session, album_ids: List[int], update_data: dict) -> int:
        """
        Update multiple albums at once.
        
        Args:
            db: Database session
            album_ids: List of album IDs to update
            update_data: Dictionary of fields to update (e.g., {"genre": "Rock"})
        
        Returns:
            int: Number of albums successfully updated
        """
        if not album_ids:
            return 0
        
        updated_count = 0
        for album_id in album_ids:
            album = db.query(Album).filter(Album.id == album_id).first()
            if album:
                # Update each field in update_data
                for key, value in update_data.items():
                    if hasattr(album, key) and value is not None:
                        setattr(album, key, value)
                updated_count += 1
        
        db.commit()
        logger.info(f"✅ {updated_count} albums mis à jour")
        return updated_count
    
    @staticmethod
    def bulk_delete(db: Session, album_ids: List[int]) -> int:
        """
        Delete multiple albums at once.
        
        Args:
            db: Database session
            album_ids: List of album IDs to delete
        
        Returns:
            int: Number of albums successfully deleted
        """
        if not album_ids:
            return 0
        
        # Find all albums to delete
        albums = db.query(Album).filter(Album.id.in_(album_ids)).all()
        deleted_count = len(albums)
        
        for album in albums:
            db.delete(album)
        
        db.commit()
        logger.info(f"✅ {deleted_count} albums supprimés")
        return deleted_count
    
    @staticmethod
    def _format_album_list(albums: List[Album]) -> List[AlbumResponse]:
        """
        Format a list of Album ORM objects into AlbumResponse schemas.

        Converts raw SQLAlchemy Album model instances into AlbumResponse DTO
        objects suitable for API responses. Handles missing relationships
        gracefully by providing empty defaults. Logs individual formatting
        errors without failing the entire operation.

        Args:
            albums: List of Album ORM model instances to format.

        Returns:
            List[AlbumResponse]: Formatted albums ready for JSON serialization.
                Albums that fail formatting are silently skipped.

        Implementation Notes:
            - Handles missing artists list (empty default)
            - Handles missing images list (empty default)
            - Extracts AI info from album_metadata if available
            - Gracefully handles formatting errors per-album

        Performance:
            - O(n) operation where n = number of albums
            - Assumes relationships are already loaded (no additional DB queries)
            - Consider eager loading before calling this method
        """
        items = []
        for album in albums:
            try:
                artists = [a.name for a in album.artists] if album.artists else []
                images = [img.url for img in album.images] if album.images else []
                ai_info = None
                if album.album_metadata:
                    ai_info = album.album_metadata.ai_info
                
                items.append(AlbumResponse(
                    id=album.id,
                    title=album.title,
                    year=album.year,
                    support=album.support,
                    discogs_id=album.discogs_id,
                    spotify_url=album.spotify_url,
                    discogs_url=album.discogs_url,
                    genre=album.genre,
                    artists=artists,
                    images=images,
                    ai_info=ai_info,
                    created_at=album.created_at,
                    updated_at=album.updated_at
                ))
            except Exception as e:
                logger.error(f"Erreur formatage album {album.id}: {e}")
                continue
        
        return items
