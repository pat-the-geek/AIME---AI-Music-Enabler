"""Service pour générer des articles longs sur les artistes."""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.models import Artist, Album, ListeningHistory
from app.services.external.ai_service import AIService

logger = logging.getLogger(__name__)


class ArticleService:
    """Service pour générer des articles journalistiques sur les artistes."""
    
    @staticmethod
    async def generate_article(
        db: Session,
        ai_service: AIService,
        artist_id: int
    ) -> Dict[str, Any]:
        """
        Générer un article long (3000 mots) sur un artiste.
        
        Args:
            db: Session base de données
            ai_service: Service IA pour génération
            artist_id: ID de l'artiste
            
        Returns:
            Dict contenant l'article formaté en markdown
        """
        try:
            # Récupérer l'artiste et ses albums
            artist = db.query(Artist).options(
                joinedload(Artist.albums),
                joinedload(Artist.images)
            ).filter(Artist.id == artist_id).first()
            
            if not artist:
                raise ValueError(f"Artiste {artist_id} non trouvé")
            
            # Récupérer les albums de l'artiste
            albums = db.query(Album).join(Album.artists).filter(
                Artist.id == artist_id
            ).order_by(Album.year.desc().nullslast()).limit(20).all()
            
            # Récupérer les statistiques d'écoute
            listen_count = db.query(ListeningHistory).join(
                ListeningHistory.track
            ).join(
                Album, Album.id == ListeningHistory.track.property.mapper.class_.album_id
            ).join(
                Album.artists
            ).filter(Artist.id == artist_id).count()
            
            # Construire le contexte pour l'IA
            albums_info = []
            for album in albums[:10]:  # Limiter à 10 albums
                album_info = f"- **{album.title}**"
                if album.year:
                    album_info += f" ({album.year})"
                if album.genre:
                    album_info += f" - Genre: {album.genre}"
                if album.ai_description:
                    desc = album.ai_description[:200].strip()
                    album_info += f"\n  Description: {desc}..."
                albums_info.append(album_info)
            
            albums_text = "\n".join(albums_info) if albums_info else "Aucun album disponible"
            
            # Générer l'article avec l'IA
            current_date = datetime.now().strftime("%B %Y")
            
            prompt = f"""Tu es un journaliste musical expert spécialisé dans les biographies d'artistes.

⚠️ DATE ACTUELLE: {current_date}

Écris un article journalistique complet et approfondi de **3000 mots** sur l'artiste **{artist.name}**.

**Informations disponibles:**
- Nombre d'albums: {len(albums)}
- Nombre d'écoutes: {listen_count}
- Albums:
{albums_text}

**STRUCTURE OBLIGATOIRE:**

# {artist.name} : Portrait d'artiste

## Introduction (300 mots)
Présentation captivante avec analyse de son importance dans l'histoire de la musique.

## Biographie et Débuts (500 mots)
- **Origines** et contexte
- *Premières influences* musicales
- Débuts de carrière avec **dates importantes**

## Discographie et Évolution (800 mots)
- **Albums majeurs** avec année et analyse
- *Évolution artistique* et thèmes
- Collaborations **importantes**

## Actualité et Dernières Sorties (600 mots)
- Derniers **albums** et projets
- *Tournées et performances*
- Nouveaux **singles** avec collaborations

## Impact et Héritage (500 mots)
- Influence sur **d'autres artistes**
- Contribution au **genre musical**
- Reconnaissance *critique* et **commerciale**

## Anecdotes et Moments Marquants (300 mots)
- **Histoires intéressantes**
- *Moments iconiques*
- Faits **marquants**

**FORMATAGE MARKDOWN OBLIGATOIRE:**
- Utilise # ## pour les titres
- **gras** pour concepts importants
- *italique* pour emphase
- Listes à puces (-) et numérotées
- Blockquotes (>) pour citations

Commence l'article maintenant:"""
            
            logger.info(f"📝 Génération article IA pour {artist.name}...")
            
            content = await asyncio.wait_for(
                ai_service.ask_for_ia(prompt, max_tokens=4000),
                timeout=120.0
            )
            
            content = content.strip()
            word_count = len(content.split())
            
            return {
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_url": artist.images[0].url if artist.images else None,
                "generated_at": datetime.now().isoformat(),
                "word_count": word_count,
                "content": content,
                "albums_count": len(albums),
                "listen_count": listen_count
            }
            
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Timeout génération article pour {artist.name}")
            raise ValueError("Timeout lors de la génération de l'article")
        except Exception as e:
            logger.error(f"❌ Erreur génération article: {e}")
            raise
    
    @staticmethod
    async def generate_article_stream(
        db: Session,
        ai_service: AIService,
        artist_id: int
    ):
        """
        Générer un article en streaming SSE.
        
        Args:
            db: Session base de données
            ai_service: Service IA
            artist_id: ID de l'artiste
            
        Yields:
            str: Chunks SSE du contenu
        """
        try:
            artist = db.query(Artist).options(
                joinedload(Artist.albums),
                joinedload(Artist.images)
            ).filter(Artist.id == artist_id).first()
            
            if not artist:
                raise ValueError(f"Artiste {artist_id} non trouvé")
            
            albums = db.query(Album).join(Album.artists).filter(
                Artist.id == artist_id
            ).order_by(Album.year.desc().nullslast()).limit(20).all()
            
            listen_count = db.query(ListeningHistory).join(
                ListeningHistory.track
            ).join(
                Album, Album.id == ListeningHistory.track.property.mapper.class_.album_id
            ).join(
                Album.artists
            ).filter(Artist.id == artist_id).count()
            
            albums_info = []
            for album in albums[:10]:
                album_info = f"- **{album.title}**"
                if album.year:
                    album_info += f" ({album.year})"
                if album.genre:
                    album_info += f" - Genre: {album.genre}"
                if album.ai_description:
                    desc = album.ai_description[:200].strip()
                    album_info += f"\n  Description: {desc}..."
                albums_info.append(album_info)
            
            albums_text = "\n".join(albums_info) if albums_info else "Aucun album disponible"
            current_date = datetime.now().strftime("%B %Y")
            
            prompt = f"""Tu es un journaliste musical expert spécialisé dans les biographies d'artistes.

⚠️ DATE ACTUELLE: {current_date}

Écris un article journalistique complet de **3000 mots** sur **{artist.name}**.

Albums ({len(albums)}): {albums_text}

Utilise markdown riche (titres, gras, italique, listes). Format:
- Introduction, Biographie, Discographie, Actualité, Impact, Anecdotes."""
            
            logger.info(f"📝 Streaming article IA pour {artist.name}...")
            
            async for chunk in ai_service.ask_for_ia_stream(prompt, max_tokens=4000):
                yield chunk
                
        except Exception as e:
            logger.error(f"❌ Erreur streaming article: {e}")
            import json
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
