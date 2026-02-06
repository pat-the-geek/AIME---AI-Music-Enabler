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
            from datetime import datetime
            current_date = datetime.now().strftime("%B %Y")  # e.g., "February 2026"
            
            prompt = f"""Tu es un journaliste musical expert spécialisé dans les biographies d'artistes.

⚠️ DATE ACTUELLE: {current_date}

🔍 INSTRUCTIONS CRITIQUES - INFORMATIONS ACTUALISÉES:
=====================================================
- NON NÉGOCIABLE: Utilise les informations les PLUS RÉCENTES et actualisées (jusqu'à {current_date})
- Si tu connais les albums, tournées ou projets sortis APRÈS 2024, INCLUS-LES absolument
- Focalise sur les 2-3 dernières années particulièrement pour la section "Actualité"
- Mentionner les dernières tournées Si tu les connais après 2023
- Si de nouvelles collaborations sont sorties récemment, c'est CRITIQUE de les inclure
- Recherche mentalement dans tes connaissances les PLUS RÉCENTES POSSIBLES sur cet artiste
- La section sur les Actualités doit être la PLUS À JOUR possible (concert récents, albums 2024-2026, etc.)

📝 INSTRUCTIONS CRITIQUES DE FORMATAGE MARKDOWN:
============================================
- UTILISE ABSOLUMENT du markdown riche à chaque paragraphe
- Les titres DOIVENT utiliser # ## ou ### (Markdown headings)
- Le **gras** doit entourer les mots ou concepts importants
- L'*italique* doit être utilisé pour les emphases et citations
- Les listes à puces (-) et les listes numérotées (1.) doivent être utilisées
- Les citations blockquote doivent utiliser le symbole (> citation)
- Les accents musicaux *doivent* utiliser des *expressions en italique*
- Utilise **gras** pour les titres d'albums, noms d'artistes
- Utilise _underscores_ ou *astérisques_ pour l'emphase
- CHAQUE paragraphe doit contenir au minimum UN élément markdown

Écris un article journalistique complet et approfondi de **3000 mots** sur l'artiste **{artist.name}**.

**Informations disponibles PROVENANT DE LA COLLECTION LOCALE:**
- Nombre d'albums dans la collection: {len(albums)}
- Nombre d'écoutes enregistrées: {listen_count}
- Albums disponibles:
{albums_text}

⚠️ IMPORTANT: Ces albums ci-dessus sont LOCAL à la collection. Tu DOIS complémenter avec tes connaissances actualisées jusqu'à {current_date}!

**STRUCTURE OBLIGATOIRE - Chaque section doit avoir du formatage markdown:**

# {artist.name} : Portrait d'artiste

## Introduction (300 mots)
Présentation captivante avec **gras** et *italique*, analyse de son importance dans l'histoire de la musique, son influence culturelle.
Utilise des listes à puces pour les points clés.

## Biographie et Débuts (500 mots)
- **Origines**: [avec contexte en gras]
- *Premières influences* musicales en italique
- Débuts de carrière avec **dates importantes**
- Moments clés marqués par du formatage markdown

## Discographie et Évolution Artistique (800 mots)
Structure avec:
- **Albums majeurs** en gras avec analyse
- *Évolution artistique* en italique 
- > Blockquote inspirée si pertinent
- Collaborations **importantes** marquées
- 1. Albums les plus **influents** en liste numérotée

## Actualité et Dernières Sorties (600 mots)
- Derniers **albums ou projets** importants
- *Tournées et performances* récentes
- Nouveaux **singles** avec collaborations en gras
- Projets futurs en *italic avec emphase*

## Impact et Héritage (500 mots)
- Influence sur **d'autres artistes** majeurs
- Contribution au **genre musical**
- Reconnaissance *critique* et **commerciale**
- Place dans l'**histoire de la musique**

## Anecdotes et Moments Marquants (300 mots)
- **Histoires intéressantes** en gras
- *Moments iconiques* en concert en italique
- Faits **marquants** de sa carrière

**ÉNORME IMPORTANCE - FORMATAGE MARKDOWN OBLIGATOIRE:**
- L'article DOIT avoir un **formatage markdown RICHE et ÉLÉGANT**
- Sépare les sections avec du padding
- Utilise les listes pour structurer
- Les noms d'artistes DOIVENT être en **gras**
- Les concepts clés DOIVENT être en *italique*
- Pas de texte plat sans formatage - CHAQUE phrase doit avoir du markdown
- Sois précis et factuel quand tu as des informations
- Reste crédible et cohérent
- N'invente pas de fausses dates spécifiques
- Concentre-toi sur l'analyse artistique

Commence maintenant l'article - ATTENTION: Le markdown est CRITIQUEMENT OBLIGATOIRE:"""
            
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
            from datetime import datetime
            current_date = datetime.now().strftime("%B %Y")  # e.g., "February 2026"
            
            prompt = f"""Tu es un journaliste musical expert spécialisé dans les biographies d'artistes.

⚠️ DATE ACTUELLE: {current_date}

🔍 INSTRUCTIONS CRITIQUES - INFORMATIONS ACTUALISÉES:
=====================================================
- NON NÉGOCIABLE: Utilise les informations les PLUS RÉCENTES et actualisées (jusqu'à {current_date})
- Si tu connais les albums, tournées ou projets sortis APRÈS 2024, INCLUS-LES absolument
- Focalise sur les 2-3 dernières années particulièrement pour la section "Actualité"
- Mentionner les dernières tournées Si tu les connais après 2023
- Si de nouvelles collaborations sont sorties récemment, c'est CRITIQUE de les inclure
- Recherche mentalement dans tes connaissances les PLUS RÉCENTES POSSIBLES sur cet artiste
- La section sur les Actualités doit être la PLUS À JOUR possible (concert récents, albums 2024-2026, etc.)

📝 INSTRUCTIONS CRITIQUES DE FORMATAGE MARKDOWN:
============================================
- UTILISE ABSOLUMENT du markdown riche à chaque paragraphe
- Les titres DOIVENT utiliser # ## ou ### (Markdown headings)
- Le **gras** doit entourer les mots ou concepts importants
- L'*italique* doit être utilisé pour les emphases et citations
- Les listes à puces (-) et les listes numérotées (1.) doivent être utilisées
- Les citations blockquote doivent utiliser le symbole (> citation)
- Les accents musicaux *doivent* utiliser des *expressions en italique*
- Utilise **gras** pour les titres d'albums, noms d'artistes
- Utilise _underscores_ ou *astérisques_ pour l'emphase
- CHAQUE paragraphe doit contenir au minimum UN élément markdown

Écris un article journalistique complet et approfondi de **3000 mots** sur l'artiste **{artist.name}**.

**Informations disponibles PROVENANT DE LA COLLECTION LOCALE:**
- Nombre d'albums dans la collection: {len(albums)}
- Nombre d'écoutes enregistrées: {listen_count}
- Albums disponibles:
{albums_text}

⚠️ IMPORTANT: Ces albums ci-dessus sont LOCAL à la collection. Tu DOIS complémenter avec tes connaissances actualisées jusqu'à {current_date}!

**STRUCTURE OBLIGATOIRE - Chaque section doit avoir du formatage markdown:**

# {artist.name} : Portrait d'artiste

## Introduction (300 mots)
Présentation captivante avec **gras** et *italique*, analyse de son importance dans l'histoire de la musique, son influence culturelle.
Utilise des listes à puces pour les points clés.

## Biographie et Débuts (500 mots)
- **Origines**: [avec contexte en gras]
- *Premières influences* musicales en italique
- Débuts de carrière avec **dates importantes**
- Moments clés marqués par du formatage markdown

## Discographie et Évolution Artistique (800 mots)
Structure avec:
- **Albums majeurs** en gras avec analyse
- *Évolution artistique* en italique 
- > Blockquote inspirée si pertinent
- Collaborations **importantes** marquées
- 1. Albums les plus **influents** en liste numérotée

## Actualité et Dernières Sorties (600 mots)
- Derniers **albums ou projets** importants
- *Tournées et performances* récentes
- Nouveaux **singles** avec collaborations en gras
- Projets futurs en *italic avec emphase*

## Impact et Héritage (500 mots)
- Influence sur **d'autres artistes** majeurs
- Contribution au **genre musical**
- Reconnaissance *critique* et **commerciale**
- Place dans l'**histoire de la musique**

## Anecdotes et Moments Marquants (300 mots)
- **Histoires intéressantes** en gras
- *Moments iconiques* en concert en italique
- Faits **marquants** de sa carrière

**ÉNORME IMPORTANCE - FORMATAGE MARKDOWN OBLIGATOIRE:**
- L'article DOIT avoir un **formatage markdown RICHE et ÉLÉGANT**
- Sépare les sections avec du padding
- Utilise les listes pour structurer
- Les noms d'artistes DOIVENT être en **gras**
- Les concepts clés DOIVENT être en *italique*
- Pas de texte plat sans formatage - CHAQUE phrase doit avoir du markdown
- Sois précis et factuel quand tu as des informations
- Reste crédible et cohérent
- N'invente pas de fausses dates spécifiques
- Concentre-toi sur l'analyse artistique

Commence maintenant l'article - ATTENTION: Le markdown est CRITIQUEMENT OBLIGATOIRE:"""
            
            logger.info(f"📝 Streaming article IA pour {artist.name} (3000 mots)...")
            
            # Streamer la réponse de l'IA
            async for chunk in self.ai_service.ask_for_ia_stream(prompt, max_tokens=4000):
                yield chunk
                
        except Exception as e:
            logger.error(f"❌ Erreur streaming article: {e}")
            import json
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
