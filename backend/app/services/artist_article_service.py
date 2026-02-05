"""Service pour générer des articles longs sur les artistes."""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.models import Artist, Album, ListeningHistory
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


class ArtistArticleService:
    """Service pour générer des articles journalistiques sur les artistes."""
    
    def __init__(self, db: Session, ai_service: AIService):
        self.db = db
        self.ai_service = ai_service
    
    async def generate_article(self, artist_id: int) -> Dict[str, Any]:
        """
        Générer un article long (3000 mots) sur un artiste.
        
        Args:
            artist_id: ID de l'artiste
            
        Returns:
            Dict contenant l'article formaté en markdown
        """
        try:
            # Récupérer l'artiste et ses albums
            artist = self.db.query(Artist).options(
                joinedload(Artist.albums),
                joinedload(Artist.images)
            ).filter(Artist.id == artist_id).first()
            
            if not artist:
                raise ValueError(f"Artiste {artist_id} non trouvé")
            
            # Récupérer les albums de l'artiste
            albums = self.db.query(Album).join(Album.artists).filter(
                Artist.id == artist_id
            ).order_by(Album.year.desc().nullslast()).limit(20).all()
            
            # Récupérer les statistiques d'écoute
            listen_count = self.db.query(ListeningHistory).join(
                ListeningHistory.track
            ).join(
                Album, Album.id == ListeningHistory.track.property.mapper.class_.album_id
            ).join(
                Album.artists
            ).filter(Artist.id == artist_id).count()
            
            # Construire le contexte pour l'IA
            albums_info = []
            for album in albums[:10]:  # Limiter à 10 albums pour ne pas surcharger le prompt
                album_info = f"- **{album.title}**"
                if album.year:
                    album_info += f" ({album.year})"
                if album.genre:
                    album_info += f" - Genre: {album.genre}"
                if album.ai_description:
                    # Prendre les 200 premiers caractères de la description
                    desc = album.ai_description[:200].strip()
                    album_info += f"\n  Description: {desc}..."
                albums_info.append(album_info)
            
            albums_text = "\n".join(albums_info) if albums_info else "Aucun album disponible"
            
            # Générer l'article avec l'IA
            prompt = f"""Tu es un journaliste musical expert spécialisé dans les biographies d'artistes. 

Écris un article journalistique complet et approfondi de **3000 mots** sur l'artiste **{artist.name}**.

**Informations disponibles:**
- Nombre d'albums dans la collection: {len(albums)}
- Nombre d'écoutes enregistrées: {listen_count}
- Albums récents:
{albums_text}

**Structure obligatoire de l'article (3000 mots):**

# {artist.name} : Portrait d'artiste

## Introduction (300 mots)
Présentation captivante de l'artiste, son importance dans l'histoire de la musique, son influence culturelle.

## Biographie et Débuts (500 mots)
- Origines et formation musicale
- Premières influences
- Débuts de carrière
- Moments clés de son parcours

## Discographie et Évolution Artistique (800 mots)
- Analyse des albums majeurs (utilise les informations fournies)
- Évolution du style musical
- Collaborations marquantes
- Albums les plus influents

## Actualité et Dernières Sorties (600 mots)
- Derniers albums ou projets
- Tournées récentes ou à venir
- Nouveaux singles ou collaborations
- Projets futurs annoncés

## Impact et Héritage (500 mots)
- Influence sur d'autres artistes
- Contribution au genre musical
- Reconnaissance critique et commerciale
- Place dans l'histoire de la musique

## Anecdotes et Moments Marquants (300 mots)
- Histoires intéressantes
- Moments iconiques en concert
- Faits marquants de sa carrière

**Style d'écriture:**
- Ton journalistique professionnel mais accessible
- Phrases variées et fluides
- Citations imaginées si pertinent
- Références culturelles
- Analyse musicale approfondie
- Formatage Markdown riche (gras, italique, titres, listes)

**IMPORTANT:**
- L'article DOIT faire exactement 3000 mots
- Utilise un formatage Markdown élégant et lisible
- Sois précis et factuel quand tu as des informations
- Reste crédible et cohérent dans tes développements
- N'invente pas de fausses dates ou événements spécifiques
- Concentre-toi sur l'analyse artistique et l'impact culturel

Commence maintenant l'article:"""
            
            # Appeler l'IA avec un timeout de 2 minutes
            logger.info(f"📝 Génération article IA pour {artist.name} (3000 mots)...")
            
            content = await asyncio.wait_for(
                self.ai_service.ask_for_ia(
                    prompt, 
                    max_tokens=4000  # ~3000 mots nécessitent environ 4000 tokens
                ),
                timeout=120.0
            )
            
            # Nettoyer le contenu
            content = content.strip()
            
            # Compter les mots (approximation)
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
    
    async def generate_article_stream(self, artist_id: int):
        """
        Générer un article long (3000 mots) sur un artiste en streaming.
        
        Args:
            artist_id: ID de l'artiste
            
        Yields:
            str: Chunks SSE du contenu de l'article
        """
        try:
            # Récupérer l'artiste et ses albums
            artist = self.db.query(Artist).options(
                joinedload(Artist.albums),
                joinedload(Artist.images)
            ).filter(Artist.id == artist_id).first()
            
            if not artist:
                raise ValueError(f"Artiste {artist_id} non trouvé")
            
            # Récupérer les albums de l'artiste
            albums = self.db.query(Album).join(Album.artists).filter(
                Artist.id == artist_id
            ).order_by(Album.year.desc().nullslast()).limit(20).all()
            
            # Récupérer les statistiques d'écoute
            listen_count = self.db.query(ListeningHistory).join(
                ListeningHistory.track
            ).join(
                Album, Album.id == ListeningHistory.track.property.mapper.class_.album_id
            ).join(
                Album.artists
            ).filter(Artist.id == artist_id).count()
            
            # Construire le contexte pour l'IA
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
            
            # Générer le prompt (même que generate_article)
            prompt = f"""Tu es un journaliste musical expert spécialisé dans les biographies d'artistes. 

Écris un article journalistique complet et approfondi de **3000 mots** sur l'artiste **{artist.name}**.

**Informations disponibles:**
- Nombre d'albums dans la collection: {len(albums)}
- Nombre d'écoutes enregistrées: {listen_count}
- Albums récents:
{albums_text}

**Structure obligatoire de l'article (3000 mots):**

# {artist.name} : Portrait d'artiste

## Introduction (300 mots)
Présentation captivante de l'artiste, son importance dans l'histoire de la musique, son influence culturelle.

## Biographie et Débuts (500 mots)
- Origines et formation musicale
- Premières influences
- Débuts de carrière
- Moments clés de son parcours

## Discographie et Évolution Artistique (800 mots)
- Analyse des albums majeurs (utilise les informations fournies)
- Évolution du style musical
- Collaborations marquantes
- Albums les plus influents

## Actualité et Dernières Sorties (600 mots)
- Derniers albums ou projets
- Tournées récentes ou à venir
- Nouveaux singles ou collaborations
- Projets futurs annoncés

## Impact et Héritage (500 mots)
- Influence sur d'autres artistes
- Contribution au genre musical
- Reconnaissance critique et commerciale
- Place dans l'histoire de la musique

## Anecdotes et Moments Marquants (300 mots)
- Histoires intéressantes
- Moments iconiques en concert
- Faits marquants de sa carrière

**Style d'écriture:**
- Ton journalistique professionnel mais accessible
- Phrases variées et fluides
- Citations imaginées si pertinent
- Références culturelles
- Analyse musicale approfondie
- Formatage Markdown riche (gras, italique, titres, listes)

**IMPORTANT:**
- L'article DOIT faire exactement 3000 mots
- Utilise un formatage Markdown élégant et lisible
- Sois précis et factuel quand tu as des informations
- Reste crédible et cohérent dans tes développements
- N'invente pas de fausses dates ou événements spécifiques
- Concentre-toi sur l'analyse artistique et l'impact culturel

Commence maintenant l'article:"""
            
            logger.info(f"📝 Streaming article IA pour {artist.name} (3000 mots)...")
            
            # Streamer la réponse de l'IA
            async for chunk in self.ai_service.ask_for_ia_stream(prompt, max_tokens=4000):
                yield chunk
                
        except Exception as e:
            logger.error(f"❌ Erreur streaming article: {e}")
            import json
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
