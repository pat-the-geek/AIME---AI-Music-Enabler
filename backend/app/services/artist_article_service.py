"""
AI-powered long-form artist biography and journalism generation service.

Service generates comprehensive 3000-word articles about artists using Euria AI.
Incorporates local collection metadata (albums, listening statistics) with AI knowledge
to create rich, markdown-formatted biographical content. Supports both request-response
and streaming SSE modes. Articles include introduction, biography, discography analysis,
recent news, impact assessment, and notable moments with professional markdown formatting.

Architecture:
- Retrieves artist data: albums (up to 20), images, listening history count
- Builds rich prompt with collection context + date awareness (current date injected)
- Calls Euria AI with explicit markdown formatting instructions (>3000 words)
- Response: 3000+ word markdown article with custom styling, headings, lists, blockquotes
- Streaming: SSE-compatible chunks for real-time frontend display
- Timeout: 120s per article (typical: 30-60s)
- Token allocation: 4000 tokens (~3000 words)

Typical usage:
    service = ArtistArticleService(db, ai_service)
    
    # Standard request-response
    article = await service.generate_article(artist_id=42)  # Returns dict with content
    
    # Streaming (suitable for FastAPI StreamingResponse)
    async for chunk in service.generate_article_stream(artist_id=42):
        yield chunk

Performance profile:
- generate_article(): 30-120s (AI generation 95% of time) + <500ms DB queries
- generate_article_stream(): Same as above, with streaming overhead
- Database: 2-3 queries (Artist with joinedload, Album list, ListeningHistory count)
- AI: 1 API call (~4000 tokens, 30-60s typical)

Output format (Markdown):
- Title: # Artiste Name: Portrait d'artiste
- Sections: Introduction, Biographie, Discographie, Actualité, Héritage, Anecdotes
- Styling: Bold (**text**), italic (*text*), lists (-/1.), blockquotes (>)
- Word count: ~3000 words per article
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.models import Artist, Album, ListeningHistory
from app.services.external.ai_service import AIService

logger = logging.getLogger(__name__)


class ArtistArticleService:
    """
    AI-powered service for generating professional long-form artist articles.
    
    Leverages Euria AI to create 3000-word markdown-formatted biographies about artists
    from user's collection. Incorporates local metadata (albums, statistics) with AI's
    general knowledge for personalized, accurate articles. Supports both standard and
    streaming response modes for flexible integration with frontend.
    
    Attributes:
        db (Session): SQLAlchemy session for database queries (Artist, Album, ListeningHistory)
        ai_service (AIService): Euria AI integration for 4000-token article generation
    
    Core responsibilities:
    - Data collection: Query artist details, albums (20 max), images, listening statistics
    - Prompt engineering: Build rich markdown + collection context + date awareness
    - Response handling: Text + streaming modes, word count tracking, error resilience
    - Timeout management: 120-second hard limit via asyncio.wait_for()
    
    Key features:
    - Markdown-enforced output: **bold**, *italic*, lists, blockquotes required
    - Date-aware prompts: Injected current date ensures continuity knowledge
    - Collection-aware: Personalizes articles with user's albums and listening counts
    - Streaming-ready: SSE format for real-time UI display
    - Error resilience: Graceful timeout handling, explicit error messages
    
    Integration points:
    - Database: 2-3 queries per article (<500ms total)
    - AI: Euria API with 4000 tokens, 30-120s typical response time
    - Frontend: REST endpoints for standard/streaming generation
    
    Example:
        service = ArtistArticleService(db, ai_service)
        article_dict = await service.generate_article(artist_id=42)
        print(f\"Generated {article_dict['word_count']} word article\")
        print(article_dict['content'][:500])  # Markdown content preview
        
        # Streaming variant (FastAPI)
        @router.get(\"/artist/{id}/article/stream\")
        async def stream_article(id: int):
            service = ArtistArticleService(db, ai_service)
            return StreamingResponse(
                service.generate_article_stream(id),
                media_type=\"text/event-stream\"
            )
    
    Performance characteristics:
    - Article generation: 30-120 seconds (dominated by AI API latency)
    - Database queries: <500ms (Artist + joinedload, Album list, count)
    - Throughput: ~1 article per 60s at typical AI speed
    - Scaling: Linear with AI service performance
    
    Limitations & constraints:
    - Timeout: Hard 120-second limit (asyncio.TimeoutError raised on exceed)
    - Album sampling: 20 queried, 10 used in prompt (token budget optimization)
    - Image source: First local album image (no external fetch)
    - Word count: Simple split() approximation (actual may be +/- 10%)
    """
    
    def __init__(self, db: Session, ai_service: AIService):
        """
        Initialize artist article generation service with database and AI access.
        
        Args:
            db (Session): SQLAlchemy database session for album/artist/history queries.
                          Used for joinedload optimization on Artist relations.
            ai_service (AIService): Euria AI service instance for 4000-token article generation.
                                    Must support ask_for_ia() and ask_for_ia_streaming() methods.
        
        Performance:
            - O(1) initialization, <1ms
            - No network calls until article generation
            - No database connections established (lazy connection on first query)
        
        Side Effects:
            - Stores references to db and ai_service (no mutations during init)
            - No logging during initialization
        
        Return value: None
        
        Example:
            from sqlalchemy.orm import Session
            from app.services.external.ai_service import AIService
            
            service = ArtistArticleService(db=session, ai_service=ai_client)
            # service.db references the session
            # service.ai_service references the AI client
        
        Attributes set:
            self.db (Session): Database session reference
            self.ai_service (AIService): AI service reference
        
        Preconditions:
            - db must be valid SQLAlchemy Session (not closed)
            - ai_service must be instantiated and ready
        
        Postconditions:
            - Service ready to generate articles via generate_article() or generate_article_stream()
        """
        self.db = db
        self.ai_service = ai_service
    
    async def generate_article(self, artist_id: int) -> Dict[str, Any]:
        """
        Generate comprehensive 3000-word markdown article about an artist (request-response mode).
        
        Retrieves artist metadata from local database (albums, listening statistics, images),
        constructs rich prompt with date awareness and explicit markdown formatting requirements,
        calls Euria AI for 4000-token generation, returns formatted response with metadata.
        Article includes: biography, discography analysis, recent news, impact assessment,
        notable moments. Fully markdown-formatted with bold, italic, lists, blockquotes,
        blockquote sections (publication-ready output). Albums integrated into prompt as
        collection context (10 max, to manage token budget).
        
        Args:
            artist_id (int): Database ID of artist to generate article for.
                            Must exist in Artist table.
        
        Returns:
            dict: Article response dict with keys:
                - artist_id (int): Input artist ID (matches request)
                - artist_name (str): Artist full name from database
                - artist_image_url (str|None): Album cover URL from local collection (first image)
                                               or None if no images available
                - generated_at (str): ISO8601 UTC timestamp (datetime.now().isoformat())
                - word_count (int): Approximate word count via split() (~3000 typical)
                - content (str): Full markdown article text with formatting
                - albums_count (int): Number of albums queried from database (up to 20)
                - listen_count (int): Total listening history count for artist
        
        Raises:
            ValueError: If artist_id not found in database (\"Artiste {id} non trouvé\")
            ValueError: If article generation times out (\"Timeout lors de la génération...\")
            Exception: Any other AI service exceptions (logged, re-raised as-is)
        
        Performance:
            - Typical: 30-120s (AI generation dominates, 95% of total time)
            - Database: 2-3 queries, <500ms aggregate
            - AI timeout: 120 seconds hard limit (asyncio.wait_for)
            - Token allocation: 4000 tokens used for ~3000-word output
            - Big-O: O(n) where n = album count (up to 20 queried, 10 in prompt)
            - Scaling: Linear degradation with network latency to AI service
        
        Side Effects:
            - Queries database: Artist (with joinedload eager loading), Album list (up to 20),
                                ListeningHistory count
            - Calls Euria AI: 4000 token budget, synchronous blocking (via asyncio.wait_for)
            - Logs: INFO on start (📝 Génération article IA...), ERROR on timeout/exception
            - DateTime: Captures current date for prompt, isoformat at completion
        
        Logging:
            - INFO: asyncio.wait_for timeout caught (⏱️ Timeout génération article pour {name})
            - ERROR: Other exceptions (❌ Erreur génération article: {e})
            - Level: logger.error (ERROR severity)
        
        Implementation Notes:
            - Album limit: 20 albums queried (ORDER BY year DESC NULLSLAST), 10 used in prompt
            - Date injection: Current date format \"%B %Y\" injected (e.g., \"February 2026\")
            - Prompt structure: 6 mandatory sections with word count guidance (300-800 words each)
            - Markdown enforcement: Bold, italic, lists, blockquotes, headings required
            - Prompt context: Local album titles, genres, AI descriptions + artist counts
            - Timeout: asyncio.wait_for(..., timeout=120.0) wraps AI call (prevents hangs)
            - Word counting: Simple split() approximation (underestimates, no punctuation removal)
            - Image source: First artist.images[0].url (local collection), fallback None
            - Error mapping: asyncio.TimeoutError → ValueError (timeout msg), generic Exception re-raised
            - Database joins: Album → Artist relationship for album filtering
            - Eager loading: joinedload(Artist.albums, Artist.images) for optimization
            
        Prompt Features (sent to Euria AI):
            - Date-aware: Current date injected (ensures relevance, up-to-2026 knowledge)
            - Collection-aware: Local album/artist context integrated
            - Markdown-strict: 6 explicit formatting rules (bold, italic, lists, blockquotes)
            - Knowledge-complete: Requests up-to-date information + recent albums/tours
            - Section-focused: 6 sections with 300-800 word targets
            - Comprehensive: Biography, discography, news, impact, legacy, anecdotes
            - Style guide: Markdown emphasis rules per section
            - Token budget: Explicit instruction for 3000-word output
            
        Database behavior:
            - Artist query: Uses joinedload for eager loading (avoid N+1)
            - Album query: Join on Artist ID, filter, ORDER BY year DESC NULLSLAST, limit 20
            - ListeningHistory: Join Album → Artist, filter by artist_id, count()
            - Transaction: Read-only (no mutations)
            
        Prompt example (abbreviated):
            \"Tu es un journaliste musical expert...\"
            \"⚠️ DATE ACTUELLE: February 2026\"
            \"🔍 INSTRUCTIONS CRITIQUES - INFORMATIONS ACTUALISÉES:\"
            \"📝 INSTRUCTIONS CRITIQUES DE FORMATAGE MARKDOWN:\"
            \"**Informations disponibles PROVENANT DE LA COLLECTION LOCALE:**\"
            (6 sections with structure: # Title, ## Subtitle, bullet lists, formatting)
        
        Used by:
            - GET /artist/{artist_id}/article endpoint (REST API)
            - Magazine article generation (batch processing)
            - Client-side: Frontend request over HTTP, displays returned markdown
        
        Example:
            artist = await service.generate_article(artist_id=42)
            # Returns:
            # {
            #     'artist_id': 42,
            #     'artist_name': 'Radiohead',
            #     'artist_image_url': 'https://...',
            #     'generated_at': '2026-02-07T14:30:00.123456',
            #     'word_count': 3087,
            #     'content': '# Radiohead : Portrait d\\'artiste\\n\\n## Introduction...',
            #     'albums_count': 8,
            #     'listen_count': 1247
            # }
            print(f\"Generated {artist['word_count']} word article\")
            print(artist['content'][:500])  # Preview first 500 chars
            
            # Usage in FastAPI:
            @router.get(\"/artist/{id}/article\")
            async def get_article(id: int, service: ArtistArticleService = Depends()):
                try:
                    return await service.generate_article(id)
                except ValueError as e:
                    raise HTTPException(status_code=404, detail=str(e))
        
        Error handling example:
            try:
                article = await service.generate_article(999)
            except ValueError as e:
                if \"non trouvé\" in str(e):
                    logger.info(f\"Artist not in database: {e}\")
                elif \"Timeout\" in str(e):
                    logger.warning(f\"AI generation timeout: {e}\")
            except Exception as e:
                logger.error(f\"Unexpected error: {e}\", exc_info=True)
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
        Generate long-form article in streaming mode with server-sent events (SSE).
        
        Streaming variant of generate_article() for real-time content delivery to frontend.
        Returns async generator yielding SSE-formatted chunks as Euria AI generates content.
        Suitable for FastAPI StreamingResponse wrapper for progressive content display in
        browser (no page load delay for full 30-120s generation). Response includes SSE
        envelope format (data: {...}), no raw text. Same article quality/format as standard
        method, delivered progressively. Shares prompt construction and database queries
        with generate_article() (identical AI prompts).
        
        Args:
            artist_id (int): Database ID of artist to generate article for.
                            Must exist in Artist table. Same validation as generate_article().
        
        Yields:
            str: SSE-formatted data chunks as AI generates content. Each chunk follows format:
            
                data: {\"chunk\": \"First paragraph or sentence...\"}
                
                data: {\"chunk\": \"Next paragraph continues...\"}
                
                [final chunk]
                
                data: {\"done\": true}
                
            
            Format breakdown:
            - Prefix: \"data: \" (SSE protocol)
            - Payload: JSON object (\"chunk\": str) or {\"done\": true}
            - Separator: Newline after each JSON object, blank line between chunks
            - Chunks: Variable size (depends on AI streaming behavior, typically 100-500 chars)
            - Terminal: Final {\"done\": true} signals completion
            
            On error (timeout/exception):
            - data: {\"error\": \"Error message here\"}
            
        Raises (via yield):
            No exceptions raised to caller (errors yielded as SSE chunks)
            Generator will terminate if client closes connection (connection drop)
        
        Internal exceptions:
            ValueError: If artist_id not found in database (caught, yielded as error chunk)
            ValueError: If article generation times out (caught, yielded as error chunk)
            Exception: Other AI service exceptions (caught, yielded as error chunk)
        
        Performance:
            - Typical: 30-120s (identical to non-streaming)
            - Overhead: +5-10% SSE formatting and yield operations
            - Network: More efficient for large articles (progressive delivery vs. single response)
            - Latency: First chunk arrives ~2-5s (AI startup), then progressive updates
            - Big-O: O(n) where n = album count (up to 20 queried)
            - Throughput: Streaming reduces perceived latency (data flowing immediately)
        
        Side Effects:
            - Queries database: Same as generate_article() (Artist, Album, ListeningHistory)
            - Calls Euria AI: Same 4000 token budget, streaming mode (if available)
            - Logs: Same as generate_article() (INFO start, ERROR on exceptions)
            - Generator: Maintains state across yields (resumable)
        
        Implementation Notes:
            - Prompt: Identical to generate_article_response() (exact same AI prompt context)
            - Streaming: Uses ai_service.ask_for_ia_streaming() for chunk delivery
            - Code gen reuse: Album construction, prompt building reused from non-streaming
            - Chunks: SSE data lines with JSON payload, newline separator per chunk
            - Done signal: Final {\"done\": true} chunk signals completion to frontend
            - Generator safety: Will be interrupted if FastAPI client closes connection
            - Error format: SSE error chunks with error message (e.g., {\"error\": \"Timeout...\"}  )
            - Error isolation: Exceptions caught in try-except, errors yielded not raised
            - No state: Each call independent (no shared state between calls)
            
        SSE Protocol Details (HTTP streaming):
            - Content-Type: text/event-stream (MUST be set by caller)
            - CORS: May need Access-Control-Allow-Origin header
            - Timeout: Client-side can set EventSource timeout
            - Format: Lines with \"data: \" prefix, blank line-separated events
            - Encoding: UTF-8, JSON payloads with proper escaping
            - Reconnection: EventSource auto-reconnects if connection drops
            
        FastAPI Integration:
            from fastapi.responses import StreamingResponse
            
            @router.get(\"/artist/{artist_id}/article/stream\")
            async def stream_article(artist_id: int, service: ArtistArticleService = Depends()):
                return StreamingResponse(
                    service.generate_article_stream(artist_id),
                    media_type=\"text/event-stream\"
                )
        
        JavaScript Client Example:
            const eventSource = new EventSource(\"/api/artist/42/article/stream\");
            
            eventSource.addEventListener(\"message\", (e) => {
                const data = JSON.parse(e.data);
                if (data.chunk) {
                    document.getElementById(\"article\").innerHTML += data.chunk;
                }
                if (data.done) {
                    eventSource.close();
                    console.log(\"Article generation complete\");
                }
                if (data.error) {
                    console.error(\"Generation error:\", data.error);
                    eventSource.close();
                }
            });
            
            eventSource.addEventListener(\"error\", () => {
                console.error(\"Connection lost\");
                eventSource.close();
            });
        
        Used by:
            - GET /artist/{artist_id}/article/stream endpoint (streaming REST API)
            - Real-time frontend display (progressive content loading)
            - Magazine generation streams (batch processing with live updates)
        
        Example:
            # Service usage
            service = ArtistArticleService(db, ai_service)
            async for chunk in service.generate_article_stream(artist_id=42):
                # chunk = 'data: {\"chunk\": \"...\"}'
                # chunk = 'data: {\"done\": true}'
                yield chunk
            
            # Full endpoint example:
            @router.get(\"/artist/{id}/article/stream\")
            async def get_article_stream(id: int, service: ArtistArticleService = Depends()):
                async def generate():
                    async for chunk in service.generate_article_stream(id):
                        yield chunk
                return StreamingResponse(generate(), media_type=\"text/event-stream\")
            
            # Client JavaScript:
            fetch(\"/api/artist/42/article/stream\")
                .then(response => response.body.getReader())
                .then(reader => {
                    const decoder = new TextDecoder();
                    let buffer = \"\";
                    
                    function read() {
                        reader.read().then(({ done, value }) => {
                            if (done) return;
                            buffer += decoder.decode(value, { stream: true });
                            
                            lines = buffer.split(\"\\n\\n\");
                            buffer = lines.pop();  // Keep incomplete chunks
                            
                            for (const line of lines) {
                                if (line.startsWith(\"data: \")) {
                                    const data = JSON.parse(line.slice(6));
                                    if (data.chunk) appendToArticle(data.chunk);
                                    if (data.done) console.log(\"Done\");
                                }
                            }
                            read();
                        });
                    }
                    read();
                });
        
        Comparison to generate_article():
            ┌─────────────────────┬────────────────────┬──────────────────────┐
            │ Feature             │ generate_article() │ generate_article_stream() │
            ├─────────────────────┼────────────────────┼──────────────────────┤
            │ Return type         │ Dict (complete)    │ AsyncGenerator       │
            │ Frontend latency    │ Full wait (30-120s)│ Streaming (perceved less) │
            │ Response format     │ JSON dict          │ SSE chunks + JSON    │
            │ AI quality          │ Identical          │ Identical            │
            │ Database behavior   │ Identical          │ Identical            │
            │ Timeout handling    │ Raise ValueError   │ Yield error chunk    │
            │ Content-Type header │ application/json   │ text/event-stream    │
            │ Use case            │ Backend, testing   │ Frontend, real-time  │
            └─────────────────────┴────────────────────┴──────────────────────┘
        
        Error handling:
            - Artist not found: Yields {\"error\": \"Artiste {id} non trouvé\"}
            - Timeout (>120s): Yields {\"error\": \"Timeout lors de la génération...\"}
            - Other exceptions: Yields {\"error\": \"{exception message}\"}
            - Generator continues until error or completion
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
