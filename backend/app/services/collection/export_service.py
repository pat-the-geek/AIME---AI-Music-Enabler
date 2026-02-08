"""Service pour l'export de la collection (markdown, json)."""
import logging
import json
import asyncio
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.models import Album, Artist
from app.services.markdown_export_service import MarkdownExportService
from app.services.external.ai_service import AIService
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ExportService:
    """Service pour l'export de la collection en différents formats."""
    
    @staticmethod
    def export_markdown_full(db: Session) -> str:
        """
        Export the entire collection in Markdown format.

        Generates a comprehensive markdown document of all albums in the collection.
        The output includes artist discographies, album details, links, and metadata.
        Uses MarkdownExportService for formatting.

        Args:
            db: SQLAlchemy database session for query execution.

        Returns:
            str: Complete markdown content of the collection as a single string.
                Format includes multiple sections with album metadata and links.
                Ready to write to .md file or display in web interface.

        Example:
            >>> db_session = get_db()
            >>> markdown_content = ExportService.export_markdown_full(db_session)
            >>> with open("collection.md", "w") as f:
            ...     f.write(markdown_content)
            >>> print(f"Exported {len(markdown_content)} characters")

        Logging:
            - Logs INFO when export starts

        Performance Notes:
            - Fetches entire collection from database
            - May be slow for collections >10,000 albums
            - Consider pagination or filtering for large exports
        """
        logger.info("📝 Export markdown collection complète")
        markdown_content = MarkdownExportService.get_collection_markdown(db)
        return markdown_content
    
    @staticmethod
    def export_markdown_artist(db: Session, artist_id: int) -> str:
        """
        Export an artist's complete discography in Markdown format.

        Generates a markdown document containing all albums by a specific artist
        in the collection. The output includes album titles, years, links to
        Spotify and Discogs, and descriptions.

        Args:
            db: SQLAlchemy database session for query execution.
            artist_id: The database ID of the artist whose discography to export.

        Returns:
            str: Markdown content of the artist's discography.
                Includes album list with metadata and external links.

        Raises:
            Exception: If artist_id does not exist.
                Message: "Artiste {artist_id} non trouvé"
            Exception: If artist has no albums in the collection.
                Message: "Aucun album trouvé pour l'artiste {name}"

        Example:
            >>> db_session = get_db()
            >>> try:
            ...     markdown = ExportService.export_markdown_artist(db_session, artist_id=1)
            ...     print(f"Generated {len(markdown)} characters")
            ... except Exception as e:
            ...     print(f"Error: {e}")

        Logging:
            - Logs INFO with artist name when export intiates
        """
        # Vérifier que l'artiste existe
        artist = db.query(Artist).filter(Artist.id == artist_id).first()
        if not artist:
            raise Exception(f"Artiste {artist_id} non trouvé")
        
        logger.info(f"📝 Export markdown pour artiste: {artist.name}")
        markdown_content = MarkdownExportService.get_artist_markdown(db, artist_id)
        
        if not markdown_content:
            raise Exception(f"Aucun album trouvé pour l'artiste {artist.name}")
        
        return markdown_content
    
    @staticmethod
    def export_markdown_support(db: Session, support: str) -> str:
        """
        Export all albums of a specific media type/support in Markdown format.

        Generates a markdown document containing all albums in the collection
        with a specific media support type (e.g., Vinyl, CD, Digital).

        Args:
            db: SQLAlchemy database session for query execution.
            support: Media type/support to export. Valid values:
                - 'Vinyle': Vinyl records
                - 'CD': Compact discs
                - 'Digital': Digital downloads/streaming
                - 'Cassette': Cassette tapes
                Case-sensitive. Must match exactly.

        Returns:
            str: Markdown content of all albums for the specified support type.
                Includes metadata and links for each album.

        Raises:
            Exception: If support parameter is invalid.
                Message: "Support invalide. Supports valides: Vinyle, CD, Digital, Cassette"

        Example:
            >>> db_session = get_db()
            >>> vinyl_markdown = ExportService.export_markdown_support(db_session, "Vinyle")
            >>> print(f"Exported {len(vinyl_markdown)} characters")
            >>> with open("vinyl_collection.md", "w") as f:
            ...     f.write(vinyl_markdown)

        Valid Support Types:
            - 'Vinyle': Popular for collectors, includes LP/EP information
            - 'CD': Standard compact disc format
            - 'Digital': Streaming/digital purchases
            - 'Cassette': Vintage tape format

        Logging:
            - Logs INFO with support type when export starts
        """
        valid_supports = ['Vinyle', 'CD', 'Digital', 'Cassette']
        if support not in valid_supports:
            raise Exception(f"Support invalide. Supports valides: {', '.join(valid_supports)}")
        
        logger.info(f"📝 Export markdown pour support: {support}")
        markdown_content = MarkdownExportService.get_support_markdown(db, support)
        return markdown_content
    
    @staticmethod
    def export_json_full(db: Session) -> str:
        """
        Export the entire collection in JSON format.

        Generates a complete JSON export of all albums from 'discogs' source,
        including all metadata, images, and relationships. Output is formatted
        with 2-space indentation and supports UTF-8 characters.

        Args:
            db: SQLAlchemy database session for query execution.

        Returns:
            str: JSON-formatted string containing:
                - export_date: ISO 8601 timestamp of export time
                - total_albums: Count of albums in export
                - albums: Array of album objects with full metadata

                Example structure:
                {
                    "export_date": "2024-02-15T10:30:45.123456",
                    "total_albums": 42,
                    "albums": [
                        {
                            "id": 1,
                            "title": "Album Name",
                            "artists": ["Artist1", "Artist2"],
                            ...
                        }
                    ]
                }

        Example:
            >>> db_session = get_db()
            >>> json_export = ExportService.export_json_full(db_session)
            >>> data = json.loads(json_export)  # Parse JSON
            >>> print(f"Exported {data['total_albums']} albums")
            Exported 42 albums
            >>> with open("collection.json", "w") as f:
            ...     f.write(json_export)

        Logging:
            - Logs INFO when export starts

        Performance Notes:
            - Fetches all albums with source='discogs'
            - Large collections (>5000 albums) may consume significant memory
            - JSON serialization adds ~20-30% overhead vs database size
        """
        logger.info("📊 Export JSON collection complète")
        
        # Récupérer tous les albums de collection avec eager loading
        albums = db.query(Album).filter(Album.source == 'discogs').options(
            joinedload(Album.artists),
            joinedload(Album.images),
            joinedload(Album.album_metadata)
        ).order_by(Album.title).all()
        
        # Construire les données JSON
        data = {
            "export_date": datetime.now().isoformat(),
            "total_albums": len(albums),
            "albums": []
        }
        
        for album in albums:
            album_data = ExportService._format_album_json(album)
            data["albums"].append(album_data)
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def export_json_support(db: Session, support: str) -> str:
        """
        Export all albums of a specific media type in JSON format.

        Generates a JSON document containing all albums with the specified
        media support type from the 'discogs' source. Includes complete
        metadata, images, and relationships for each album.

        Args:
            db: SQLAlchemy database session for query execution.
            support: Media type/support to export. Valid values:
                - 'Vinyle': Vinyl records
                - 'CD': Compact discs
                - 'Digital': Digital downloads/streaming
                - 'Cassette': Cassette tapes
                Case-sensitive. Must match exactly.

        Returns:
            str: JSON-formatted string containing:
                - export_date: ISO 8601 timestamp of export
                - support: The media type that was exported
                - total_albums: Count of albums with this support
                - albums: Array of album objects

                Example structure:
                {
                    "export_date": "2024-02-15T10:30:45.123456",
                    "support": "Vinyle",
                    "total_albums": 15,
                    "albums": [...]
                }

        Raises:
            Exception: If support parameter is invalid.
                Message: "Support invalide. Supports valides: Vinyle, CD, Digital, Cassette"

        Example:
            >>> db_session = get_db()
            >>> json_vinyl = ExportService.export_json_support(db_session, "Vinyle")
            >>> vinyl_data = json.loads(json_vinyl)
            >>> print(f"Exported {vinyl_data['total_albums']} vinyl albums")
            Exported 25 vinyl albums

        Logging:
            - Logs INFO with support type when export starts
        """
        valid_supports = ['Vinyle', 'CD', 'Digital', 'Cassette']
        if support not in valid_supports:
            raise Exception(f"Support invalide. Supports valides: {', '.join(valid_supports)}")
        
        logger.info(f"📊 Export JSON pour support: {support}")
        
        # Récupérer les albums du support avec eager loading
        albums = db.query(Album).filter(
            Album.source == 'discogs',
            Album.support == support
        ).options(
            joinedload(Album.artists),
            joinedload(Album.images),
            joinedload(Album.album_metadata)
        ).order_by(Album.title).all()
        
        # Construire les données JSON
        data = {
            "export_date": datetime.now().isoformat(),
            "support": support,
            "total_albums": len(albums),
            "albums": []
        }
        
        for album in albums:
            album_data = ExportService._format_album_json(album)
            data["albums"].append(album_data)
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @staticmethod
    async def generate_presentation_markdown(db: Session, album_ids: List[int], include_haiku: bool = True) -> str:
        """
        Generate a formatted presentation markdown with selected albums and AI descriptions.

        Creates a curated markdown presentation of specific albums with AI-generated
        descriptions and optional haiku. Fetches albums from 'discogs' source and
        uses EurIA AI service to generate content. Includes fallback descriptions
        if AI service fails.

        Args:
            db: SQLAlchemy database session for query execution.
            album_ids: List of album database IDs to include in presentation.
                Must not be empty.
            include_haiku: Whether to generate a haiku at the beginning.
                Defaults to True. AI service is used if enabled and may fail gracefully
                with fallback haiku.

        Returns:
            str: Formatted markdown suitable for presentation or web display.
                Includes:
                - Optional haiku header
                - Album date and count
                - For each album:
                  - Artist name as heading
                  - Album title with year
                  - Spotify and Discogs links
                  - Media support type
                  - AI-generated description (35 words max)
                  - Album cover image (if available)
                - Footer with generation credits

        Raises:
            Exception: If album_ids list is empty.
                Message: "Aucun album sélectionné"
            Exception: If no albums found matching the provided IDs.
                Message: "Aucun album trouvé"

        Example:
            >>> db_session = get_db()
            >>> presentation = await ExportService.generate_presentation_markdown(
            ...     db_session,
            ...     album_ids=[1, 2, 3],
            ...     include_haiku=True
            ... )
            >>> print(presentation[:500])
            # Album Haïku
            #### The 15 of February, 2024
                3 albums from Discogs collection

        AI Integration:
            - Uses EurIA AI service if configured (from app.json)
            - Generates haiku in French if include_haiku=True
            - Generates 35-word max descriptions per album in French
            - Falls back to default descriptions if AI request fails
            - Logs warnings if AI service errors occur

        Performance Notes:
            - Async method must be awaited
            - One AI request per haiku (if enabled)
            - One AI request per album for description (N albums = N requests)
            - Consider caching AI responses for frequently used albums
            - May take 5-30 seconds depending on AI service latency

        Logging:
            - Logs INFO when generation starts
            - Logs WARNING if haiku generation fails (uses fallback)
            - Logs WARNING if description generation fails per album
            - Logs INFO on successful generation with character count
        """
        if not album_ids:
            raise Exception("Aucun album sélectionné")
        
        # Récupérer les albums
        albums = db.query(Album).filter(
            Album.id.in_(album_ids),
            Album.source == 'discogs'
        ).all()
        
        if not albums:
            raise Exception("Aucun album trouvé")
        
        logger.info(f"📝 Génération présentation markdown pour {len(albums)} albums")
        
        # Charger la config pour l'IA
        settings = get_settings()
        euria_config = settings.app_config.get('euria', {})
        
        # Initialiser le service IA
        ai = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer'),
            max_attempts=euria_config.get('max_attempts', 3),
            default_error_message=euria_config.get('default_error_message', 'Aucune information disponible')
        )
        
        # Générer le markdown
        markdown = "# Album Haïku\n"
        
        # Date du jour
        now = datetime.now()
        date_str = now.strftime("#### The %d of %B, %Y").replace(" 0", " ")
        markdown += f"{date_str}\n"
        markdown += f"\t\t{len(albums)} albums from Discogs collection\n"
        
        # Ajouter un haïku si demandé
        if include_haiku:
            try:
                haiku_prompt = "Génère un haïku court sur la musique et les albums. Réponds uniquement avec le haïku en 3 lignes, sans numérotation."
                haiku_text = await ai.ask_for_ia(haiku_prompt, max_tokens=100)
                for line in haiku_text.strip().split('\n'):
                    markdown += f"\t\t{line}\n"
            except Exception as e:
                logger.warning(f"⚠️ Erreur génération haïku: {e}")
                # Haïku par défaut
                markdown += "\t\tMusique qui danse,\n"
                markdown += "\t\talbunis en harmonie,\n"
                markdown += "\t\tcœur qui s'envole.\n"
        
        markdown += "---\n"
        
        # Générer une section pour chaque album
        for album in albums:
            # Artiste en titre
            if album.artists:
                artist_name = album.artists[0].name
                markdown += f"# {artist_name}\n"
            
            # Titre, année et infos
            title_line = f"#### {album.title}"
            if album.year:
                title_line += f" ({album.year})"
            markdown += f"{title_line}\n"
            
            # Liens Spotify et Discogs
            markdown += "\t###### 🎧"
            if album.spotify_url:
                markdown += f" [Listen with Spotify]({album.spotify_url})"
            markdown += "  👥"
            if album.discogs_url:
                markdown += f" [Read on Discogs]({album.discogs_url})"
            markdown += "\n\t###### 💿 "
            markdown += f"{album.support if album.support else 'Digital'}\n"
            
            # Description générée par l'IA
            description = ""
            try:
                album_lower = album.title.lower()
                artist_lower = (album.artists[0].name.lower() if album.artists else "artiste inconnu")
                description_prompt = f"""Présente moi l'album {album_lower} de {artist_lower}. 
N'ajoute pas de questions ou de commentaires. 
Limite ta réponse à 35 mots maximum.
Réponds uniquement en français."""
                description = await ai.ask_for_ia(description_prompt, max_tokens=100)
                
                # Vérifier si le service retourne le message d'erreur par défaut
                if description == euria_config.get('default_error_message', 'Aucune information disponible'):
                    description = f"Album {album.title} sorti en {album.year if album.year else '?'}. Œuvre musicale enrichissante, à découvrir absolument."
            except Exception as e:
                logger.warning(f"⚠️ Erreur génération description pour {album.title}: {e}")
                description = f"Album {album.title} sorti en {album.year if album.year else '?'}. Œuvre musicale enrichissante, à découvrir absolument."
            
            # Ajouter la description avec indentation
            description = description.strip()
            for line in description.split('\n'):
                markdown += f"\t\t{line}\n"
            
            # Image HTML
            if album.images and album.images[0].url:
                image_url = album.images[0].url
                markdown += f"\n\n<img src='{image_url}' />\n"
            
            markdown += "---\n"
        
        # Footer
        markdown += "\t\tPython generated with love, for iA Presenter using EurIA AI from Infomaniak\n"
        
        logger.info(f"✅ Présentation markdown générée ({len(markdown)} caractères)")
        
        return markdown
    
    @staticmethod
    def _format_album_json(album: Album) -> dict:
        """
        Format a single Album ORM object into a JSON-serializable dictionary.

        Converts SQLAlchemy Album model to a plain dictionary suitable for
        JSON export. Handles all relationships and metadata, providing sensible
        defaults for missing data.

        Args:
            album: SQLAlchemy Album ORM instance to format.

        Returns:
            dict: Album data formatted as:
                {
                    "id": int,
                    "title": str,
                    "artists": [str],  # List of artist names
                    "year": int,
                    "support": str,
                    "discogs_id": str,
                    "spotify_url": str|null,
                    "discogs_url": str|null,
                    "images": [
                        {"url": str, "type": str, "source": str},
                        ...
                    ],
                    "created_at": datetime (ISO 8601 string)|null,
                    "metadata": {
                        "ai_info": str|null,
                        "resume": str|null,
                        "labels": str|null,  # Comma-separated
                        "film_title": str|null,  # Soundtrack info
                        "film_year": int|null,
                        "film_director": str|null
                    }
                }

        Implementation Notes:
            - Safely accesses all relationships (handles null/missing)
            - Timestamps converted to ISO 8601 format
            - Empty lists for missing images/artists (no null lists)
            - Metadata always present even if all fields are null
            - Image objects include type and source information

        Performance Notes:
            - O(1) operation assuming relationships are loaded
            - No additional database queries
        """
        # Traiter les images
        images = []
        if album.images:
            for img in album.images:
                images.append({
                    "url": img.url,
                    "type": img.image_type,
                    "source": img.source
                })
        
        # Traiter les métadonnées
        metadata = {}
        if album.album_metadata:
            meta = album.album_metadata
            metadata = {
                "ai_info": meta.ai_info,
                "resume": meta.resume,
                "labels": meta.labels,
                "film_title": meta.film_title,
                "film_year": meta.film_year,
                "film_director": meta.film_director
            }
        
        return {
            "id": album.id,
            "title": album.title,
            "artists": [artist.name for artist in album.artists],
            "year": album.year,
            "support": album.support,
            "discogs_id": album.discogs_id,
            "spotify_url": album.spotify_url,
            "discogs_url": album.discogs_url,
            "images": images,
            "created_at": album.created_at.isoformat() if album.created_at else None,
            "ai_description": album.ai_description,
            "metadata": metadata
        }
