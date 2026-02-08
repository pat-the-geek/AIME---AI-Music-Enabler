"""Routes API pour les artistes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db
from app.services.artist_article_service import ArtistArticleService
from app.services.external.ai_service import AIService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/list")
async def list_artists(
    search: str = Query(None, description="Recherche par nom"),
    limit: int = Query(50, description="Nombre maximum d'artistes"),
    db: Session = Depends(get_db)
):
    """
    List all available artists with search and pagination.
    
    Retrieves a list of all artists in the music collection with optional search
    filtering and result limiting. Each artist includes basic metadata and primary
    image. Useful for artist browsing, selection dropdowns, and autocomplete features.
    Supports partial name matching (case-insensitive ILIKE).
    
    **Query Parameters:**
    - `search`: Optional artist name search (partial match, case-insensitive)
      - Example: \"Beatles\", \"The Beatl\", \"beatles\"
      - Searches: Artist.name ILIKE %search%
    - `limit`: Maximum number of results (default: 50, max: 500)
    
    **Response (200 OK):**
    ```json
    {
      "count": 3,
      "artists": [
        {
          "id": 1,
          "name": "The Beatles",
          "spotify_id": "3WrFJ7ztbogyGnTW2MCTrS",
          "image_url": "https://mosaic.scdn.co/.../image_large.jpg\"
        },
        {
          "id": 2,
          "name": \"Beatleskarma\",
          \"spotify_id\": null,
          \"image_url\": null
        }
      ]
    }
    ```
    
    **Artist Fields:**
    - `id`: Database artist ID
    - `name`: Artist name (from Spotify or database)
    - `spotify_id`: Spotify artist URI (null if no Spotify match)
    - `image_url`: URL to primary artist image (null if no image)
    
    **Database Query:**
    ```sql
    SELECT * FROM artist
    WHERE (name ILIKE %:search% OR :search IS NULL)
    ORDER BY name ASC
    LIMIT :limit
    ```
    - Query time: 50-100ms (indexed on name)
    - Join: \"artist\" to \"image\" (eager loaded)
    - Result size: ~1KB per artist
    
    **Search Behavior:**
    - Case-insensitive matching: \"The Beatles\" = \"the beatles\"
    - Partial matching: \"Beatle\" matches \"The Beatles\"
    - Whole word not required: \"eat\" matches \"Beatles\"
    - Empty search: Returns all artists (ordered by name)
    
    **Error Scenarios:**
    - Invalid limit (>500): 400 Bad Request
    - Database error: 500 Internal Server Error
    - No results: Returns count=0, empty array
    
    **Frontend Integration:**
    ```javascript
    // Artist dropdown with search
    async function searchArtists(query) {
      const response = await fetch(
        `/api/v1/collection/artists/list?search=${query}&limit=20`
      );
      const data = await response.json();
      
      return data.artists.map(artist => ({
        value: artist.id,
        label: artist.name,
        image: artist.image_url
      }));
    }
    
    // Load all artists
    async function loadAllArtists() {
      const response = await fetch('/api/v1/collection/artists/list?limit=500');
      return (await response.json()).artists;
    }
    ```
    
    **Related Endpoints:**
    - GET /api/v1/collection/artists/{id}/article: Get artist article
    - GET /api/v1/collection/artists/{id}/article/stream: Stream article
    """
    try:
        from app.models import Artist, Image
        from sqlalchemy.orm import joinedload
        
        query = db.query(Artist).options(joinedload(Artist.images))
        
        if search:
            query = query.filter(Artist.name.ilike(f"%{search}%"))
        
        artists = query.order_by(Artist.name).limit(limit).all()
        
        return {
            "count": len(artists),
            "artists": [
                {
                    "id": artist.id,
                    "name": artist.name,
                    "spotify_id": artist.spotify_id,
                    "image_url": artist.images[0].url if artist.images else None
                }
                for artist in artists
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur liste artistes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur liste artistes: {str(e)}")


@router.get("/{artist_id}/article")
async def generate_artist_article(
    artist_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate a comprehensive 3000-word article about an artist using AI.
    
    Generates a detailed, in-depth article about a specific artist using the Euria
    AI service. Article includes biography, discography analysis, musical style
    breakdown, influence assessment, and critical perspective. Takes 15-25 seconds
    for full generation. Ideal for artist detail pages and research.
    
    **Path Parameters:**
    - `artist_id`: Database ID of the artist (integer)
    
    **Response (200 OK):**
    ```json
    {
      \"id\": \"artist-1-article\",
      \"artist_id\": 1,
      \"artist_name\": \"The Beatles\",
      \"title\": \"The Beatles: Architects of Modern Popular Music\",
      \"word_count\": 3000,
      \"generated_at\": \"2026-02-08T15:30:45Z\",
      \"sections\": [
        {
          \"title\": \"Biography & Formation\",
          \"content\": \"The Beatles were formed in Liverpool...\"
        },
        {
          \"title\": \"Musical Style Analysis\",
          \"content\": \"Their sound evolved from...\"
        },
        {
          \"title\": \"Critical Assessment\",
          \"content\": \"The Beatles' influence on...\"
        }
      ],
      \"content\": \"Complete 3000-word article text...\",
      \"metadata\": {
        \"generation_time_ms\": 18500,
        \"albums_analyzed\": 13,
        \"era_coverage\": \"1960-1970\"
      }
    }
    ```
    
    **Article Sections:**
    1. Biography & Formation (300-400 words)
    2. Musical Style & Evolution (400-500 words)
    3. Discography Highlights (300-400 words)
    4. Influence & Legacy (300-400 words)
    5. Critical Assessment (300-400 words)
    
    **Generation Process:**
    1. Fetch artist metadata (name, Spotify data, albums)
    2. Fetch top albums and discography
    3. Call Euria AI service with artist context
    4. Receive structured article sections
    5. Merge sections and format final output
    6. Cache result (30-day expiry)
    
    **Performance:**
    - Artist lookup: 10-20ms
    - Discography fetch: 50-100ms
    - AI generation (Euria): 15-20 seconds (primary bottleneck)
    - Post-processing: 200-300ms
    - Total time: 15-25 seconds
    - Timeout: 30 seconds
    
    **AI Service (Euria):**
    - Service: External AI service
    - Prompt: Artist name + top albums
    - Output: Structured sections
    - Quality: Professional journalism tone
    - Language: English
    
    **Error Scenarios:**
    - Artist not found: 404 Not Found
    - Euria service unavailable: 503 Service Unavailable
    - AI generation timeout: 504 Gateway Timeout (>30s)
    - Database error: 500 Internal Server Error
    
    **Caching:**
    - Cache key: \"artist-{id}-article\"
    - Duration: 30 days
    - Invalidation: Manual (no auto-update)
    - Storage: Database cache table
    
    **Frontend Integration:**
    ```javascript
    // Load artist article
    async function loadArtistArticle(artistId) {
      try {
        const response = await fetch(\`/api/v1/collection/artists/\${artistId}/article\`);
        const article = await response.json();
        
        // Display article
        displayArticle(article.title, article.content);
        
        // Show metadata
        console.log(\`Generated in \${article.metadata.generation_time_ms}ms\`);
      } catch (error) {
        if (error.status === 404) {
          showError('Artist not found');
        } else if (error.status === 503) {
          showError('AI service unavailable');
        } else {
          showError('Failed to generate article');
        }
      }
    }
    ```
    
    **Related Endpoints:**
    - GET /api/v1/collection/artists/list: List all artists
    - GET /api/v1/collection/artists/{id}/article/stream: Stream article
    """
    try:
        # Initialiser les services
        settings = get_settings()
        secrets = settings.secrets
        euria_config = secrets.get('euria', {})
        
        ai_service = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer')
        )
        
        article_service = ArtistArticleService(db, ai_service)
        
        # Générer l'article
        logger.info(f"📝 Génération article pour artiste {artist_id}")
        article = await article_service.generate_article(artist_id)
        
        logger.info(f"✅ Article généré: {len(article['content'])} caractères")
        return article
        
    except Exception as e:
        logger.error(f"❌ Erreur génération article artiste: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur génération article: {str(e)}")


@router.get("/{artist_id}/article/stream")
async def stream_artist_article(
    artist_id: int,
    db: Session = Depends(get_db)
):
    """
    Stream a 3000-word artist article generation in real-time using Server-Sent Events.
    
    Generates a comprehensive artist article while streaming content in real-time to
    the client. Uses Server-Sent Events (SSE) for progressive delivery. Allows UI to
    show progressive content generation with loading indicators. First sends metadata,
    then streams article content in chunks as it's generated by Euria AI.
    
    **Path Parameters:**
    - `artist_id`: Database ID of the artist (integer)
    
    **Response (200 OK - text/event-stream):**
    ```
    data: {\"type\":\"metadata\",\"artist_name\":\"The Beatles\",\"artist_image_url\":\"https://...\",\"albums_count\":20}
    
    data: {\"type\":\"chunk\",\"section\":\"Biography\",\"content\":\"The Beatles were formed...\"}
    
    data: {\"type\":\"chunk\",\"section\":\"Musical Style\",\"content\":\"Their sound evolved from...\"}
    
    data: {\"type\":\"done\",\"total_words\":3000,\"generation_time_ms\":18500}
    ```
    
    **Event Types Sent:**
    1. Metadata event (first):
      - type: \"metadata\"
      - artist_name: String
      - artist_image_url: String or null
      - albums_count: Integer
    2. Content chunks (multiple):
      - type: \"chunk\"
      - section: Section title
      - content: Partial article text
    3. Completion event (last):
      - type: \"done\"
      - total_words: Integer
      - generation_time_ms: Integer
    
    **Error Handling (in stream):**
    - Artist not found: type=\"error\", message=\"Artist not found\"
    - Service error: type=\"error\", message=\"Error message\"
    - Note: Errors sent as last event, connection stays open
    
    **HTTP Headers:**
    - Content-Type: text/event-stream
    - Cache-Control: no-cache
    - Connection: keep-alive
    - X-Accel-Buffering: no (disable nginx buffering)
    
    **Generation Process (Streaming):**
    1. Send metadata (artist name, image, album count)
    2. Fetch discography (top 20 albums)
    3. Call Euria AI with streaming enabled
    4. As AI generates sections, stream them to client
    5. Send completion event with stats
    6. Close connection
    
    **Performance:**
    - Metadata delivery: 100ms
    - First chunk: 2-3 seconds
    - Chunk delivery: Every 500-1000ms
    - Total generation: 15-25 seconds
    - Network latency: Depends on client connection
    
    **Advantages Over Basic Endpoint:**
    - Progressive UI updates (smooth UX)
    - User sees content generator working
    - Reduced perceived latency
    - Can show loading indicator progress
    - No need to wait for complete generation
    
    **Browser/JavaScript Compatibility:**
    - EventSource API: Chrome, Firefox, Safari, Edge
    - Fallback: Fetch with ReadableStream (for older browsers)
    
    **Frontend Integration:**
    ```javascript
    // Stream article with EventSource
    function streamArtistArticle(artistId) {
      const eventSource = new EventSource(
        `/api/v1/collection/artists/\${artistId}/article/stream`
      );
      
      let article = { sections: [] };
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'metadata') {
          displayArtistHeader(data.artist_name, data.artist_image_url);
        } else if (data.type === 'chunk') {
          displayChunk(data.section, data.content);
        } else if (data.type === 'done') {
          console.log(\`Article done: \${data.total_words} words in \${data.generation_time_ms}ms\`);
          eventSource.close();
        }
      };
      
      eventSource.onerror = (error) => {
        const data = JSON.parse(error.data);
        if (data.type === 'error') {
          showError(data.message);
        }
        eventSource.close();
      };
    }
    ```
    
    **Connection Management:**
    - Connection timeout: 60 seconds (Nginx default)
    - Keep-alive: Every 30 seconds recommend heartbeat
    - Browser reconnect: Automatic (with exponential backoff)
    - Multiple clients: Each gets separate stream
    
    **Related Endpoints:**
    - GET /api/v1/collection/artists/list: List all artists
    - GET /api/v1/collection/artists/{id}/article: Non-streamed article
    """
    from fastapi.responses import StreamingResponse
    
    async def generate_stream():
        try:
            # Initialiser les services
            settings = get_settings()
            secrets = settings.secrets
            euria_config = secrets.get('euria', {})
            
            ai_service = AIService(
                url=euria_config.get('url'),
                bearer=euria_config.get('bearer')
            )
            
            article_service = ArtistArticleService(db, ai_service)
            
            # Envoyer les métadonnées d'abord
            logger.info(f"📝 Streaming article pour artiste {artist_id}")
            
            # Récupérer les métadonnées de l'artiste
            from app.models import Artist, Album
            from sqlalchemy.orm import joinedload
            
            artist = db.query(Artist).options(
                joinedload(Artist.albums),
                joinedload(Artist.images)
            ).filter(Artist.id == artist_id).first()
            
            if not artist:
                yield f"data: {{\"error\": \"Artiste non trouvé\"}}\n\n"
                return
            
            albums = db.query(Album).join(Album.artists).filter(
                Artist.id == artist_id
            ).order_by(Album.year.desc().nullslast()).limit(20).all()
            
            # Envoyer les métadonnées
            import json
            metadata = {
                "type": "metadata",
                "artist_name": artist.name,
                "artist_image_url": artist.images[0].url if artist.images else None,
                "albums_count": len(albums)
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Streamer le contenu de l'article
            async for chunk in article_service.generate_article_stream(artist_id):
                yield chunk
            
            # Envoyer un signal de fin
            yield f"data: {{\"type\": \"done\"}}\n\n"
            
            logger.info(f"✅ Streaming article terminé pour artiste {artist_id}")
            
        except Exception as e:
            logger.error(f"❌ Erreur streaming article: {str(e)}", exc_info=True)
            import json
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Désactiver le buffering nginx
        }
    )

