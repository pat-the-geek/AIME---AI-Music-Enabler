"""Service d'export markdown pour la collection Discogs."""
from sqlalchemy.orm import Session
from app.models import Album, Artist
from app.database import SessionLocal
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MarkdownExportService:
    """Service pour exporter la collection en markdown avec formatage enrichi."""
    
    @staticmethod
    def get_collection_markdown(db: Session) -> str:
        """
        Générer un markdown complet de la collection Discogs.
        Trié par artiste et album avec formatage enrichi.
        """
        # Récupérer tous les albums Discogs
        albums = db.query(Album).filter(
            Album.source == 'discogs'
        ).all()
        
        # Grouper par artiste principal
        albums_by_artist = {}
        for album in albums:
            if album.artists:
                artist_name = album.artists[0].name
                if artist_name not in albums_by_artist:
                    albums_by_artist[artist_name] = []
                albums_by_artist[artist_name].append(album)
        
        # Trier les albums de chaque artiste par année puis titre
        for artist in albums_by_artist:
            albums_by_artist[artist].sort(key=lambda a: (a.year or 9999, a.title))
        
        # Générer le markdown
        markdown = ""
        markdown += "# 🎵 Collection Discogs\n\n"
        markdown += f"**Exportée le:** {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
        markdown += f"**Total:** {len(albums)} albums\n\n"
        markdown += "---\n\n"
        
        # Table des matières
        markdown += "## Table des matières\n\n"
        for artist_name in sorted(albums_by_artist.keys()):
            count = len(albums_by_artist[artist_name])
            markdown += f"- [{artist_name}](#{artist_name.replace(' ', '-').lower()}) ({count})\n"
        
        markdown += "\n---\n\n"
        
        # Pour chaque artiste
        for artist_name in sorted(albums_by_artist.keys()):
            markdown += f"# {artist_name}\n\n"
            markdown += f"*{len(albums_by_artist[artist_name])} albums*\n\n"
            
            # Pour chaque album de cet artiste
            for album in albums_by_artist[artist_name]:
                markdown += MarkdownExportService._format_album_markdown(album)
                markdown += "\n---\n\n"
        
        return markdown
    
    @staticmethod
    def _format_album_markdown(album: Album) -> str:
        """
        Formater un album en markdown enrichi.
        Reprend le style de l'exemple fourni.
        """
        md = ""
        
        # Titre album (h2)
        md += f"## {album.title}\n\n"
        
        # Artistes (bold)
        if album.artists:
            artists_list = ", ".join([a.name for a in album.artists])
            md += f"**Artiste{'s' if len(album.artists) > 1 else ''}:** {artists_list}\n"
        
        # Infos compactes
        md += "\n"
        if album.year:
            md += f"- **Année:** {album.year}\n"
        
        if album.album_metadata and album.album_metadata.labels:
            labels = album.album_metadata.labels
            md += f"- **Labels:** {labels}\n"
        
        if album.support:
            md += f"- **Support:** {album.support}\n"
        
        if album.discogs_id:
            md += f"- **Discogs ID:** {album.discogs_id}\n"
        
        # Résumé IA (si disponible)
        if album.album_metadata and album.album_metadata.ai_info:
            md += f"\n**Résumé:**\n\n"
            md += f"{album.album_metadata.ai_info}\n"
        
        # Section liens (sur une ligne)
        md += "\n"
        links = []
        if album.spotify_url:
            links.append(f"[Spotify]({album.spotify_url})")
        if album.discogs_url:
            links.append(f"[Discogs]({album.discogs_url})")
        
        if links:
            md += "**Liens:** " + " | ".join(links) + "\n"
        
        # Image de couverture
        if album.images:
            image_url = album.images[0].url
            md += f"\n![{album.title}]({image_url})\n"
        
        return md
    
    @staticmethod
    def get_artist_markdown(db: Session, artist_id: int) -> str:
        """Générer un markdown pour un artiste spécifique."""
        artist = db.query(Artist).filter(Artist.id == artist_id).first()
        
        if not artist:
            return ""
        
        # Récupérer les albums de cet artiste (Discogs uniquement)
        albums = db.query(Album).filter(
            Album.source == 'discogs'
        ).join(Album.artists).filter(
            Artist.id == artist_id
        ).order_by(Album.year, Album.title).all()
        
        if not albums:
            return ""
        
        markdown = f"# 🎵 {artist.name}\n\n"
        markdown += f"**Discographie Discogs:** {len(albums)} albums\n"
        markdown += f"**Exportée le:** {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n\n"
        markdown += "---\n\n"
        
        for album in albums:
            markdown += MarkdownExportService._format_album_markdown(album)
            markdown += "\n---\n\n"
        
        return markdown
    
    @staticmethod
    def get_support_markdown(db: Session, support: str) -> str:
        """Générer un markdown pour un support spécifique (Vinyle, CD, Digital)."""
        # Récupérer les albums par support
        albums = db.query(Album).filter(
            Album.source == 'discogs',
            Album.support == support
        ).all()
        
        if not albums:
            return ""
        
        # Trier par artiste puis album
        albums.sort(key=lambda a: (
            a.artists[0].name if a.artists else "Zzz",
            a.year or 9999,
            a.title
        ))
        
        markdown = f"# 🎵 Collection Discogs - {support}\n\n"
        markdown += f"**Total:** {len(albums)} albums en {support}\n"
        markdown += f"**Exportée le:** {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n\n"
        markdown += "---\n\n"
        
        # Grouper par artiste
        albums_by_artist = {}
        for album in albums:
            if album.artists:
                artist_name = album.artists[0].name
                if artist_name not in albums_by_artist:
                    albums_by_artist[artist_name] = []
                albums_by_artist[artist_name].append(album)
        
        # Afficher par artiste
        for artist_name in sorted(albums_by_artist.keys()):
            markdown += f"## {artist_name}\n\n"
            markdown += f"*{len(albums_by_artist[artist_name])} albums*\n\n"
            
            for album in albums_by_artist[artist_name]:
                markdown += MarkdownExportService._format_album_markdown(album)
                markdown += "\n---\n\n"
        
        return markdown

