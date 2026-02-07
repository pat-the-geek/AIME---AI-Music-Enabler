"""Service pour l'export de la collection (markdown, json)."""
import logging
import json
import asyncio
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

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
        Exporter la collection complète en markdown.
        
        Args:
            db: Session de base de données
            
        Returns:
            Contenu markdown
        """
        logger.info("📝 Export markdown collection complète")
        markdown_content = MarkdownExportService.get_collection_markdown(db)
        return markdown_content
    
    @staticmethod
    def export_markdown_artist(db: Session, artist_id: int) -> str:
        """
        Exporter la discographie d'un artiste en markdown.
        
        Args:
            db: Session de base de données
            artist_id: ID de l'artiste
            
        Returns:
            Contenu markdown
            
        Raises:
            Exception: Si l'artiste n'existe pas ou sans albums
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
        Exporter tous les albums d'un support en markdown.
        
        Args:
            db: Session de base de données
            support: Support (Vinyle, CD, Digital, Cassette)
            
        Returns:
            Contenu markdown
            
        Raises:
            Exception: Si le support est invalide
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
        Exporter la collection complète en JSON.
        
        Args:
            db: Session de base de données
            
        Returns:
            Contenu JSON
        """
        logger.info("📊 Export JSON collection complète")
        
        # Récupérer tous les albums de collection
        albums = db.query(Album).filter(Album.source == 'discogs').order_by(Album.title).all()
        
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
        Exporter tous les albums d'un support en JSON.
        
        Args:
            db: Session de base de données
            support: Support (Vinyle, CD, Digital, Cassette)
            
        Returns:
            Contenu JSON
            
        Raises:
            Exception: Si le support est invalide
        """
        valid_supports = ['Vinyle', 'CD', 'Digital', 'Cassette']
        if support not in valid_supports:
            raise Exception(f"Support invalide. Supports valides: {', '.join(valid_supports)}")
        
        logger.info(f"📊 Export JSON pour support: {support}")
        
        # Récupérer les albums du support
        albums = db.query(Album).filter(
            Album.source == 'discogs',
            Album.support == support
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
        Générer une présentation markdown avec les albums sélectionnés.
        
        Args:
            db: Session de base de données
            album_ids: Liste d'IDs d'albums
            include_haiku: Inclure un haïku généré
            
        Returns:
            Contenu markdown avec présentation
            
        Raises:
            Exception: Si aucun album trouvé ou paramètres invalides
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
        """Formater un album pour l'export JSON."""
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
            "metadata": metadata
        }
