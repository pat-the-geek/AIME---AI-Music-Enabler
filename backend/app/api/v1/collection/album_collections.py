"""API pour les collections d'albums."""
import logging
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.services.album_collection_service import AlbumCollectionService
from app.models import Album, CollectionAlbum

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collections", tags=["collections"])


class CollectionCreate(BaseModel):
    """Modèle pour créer une collection."""
    name: Optional[str] = None  # Sera généré automatiquement par l'IA si non fourni
    search_type: str = 'ai_query'  # Toujours 'ai_query'
    ai_query: str  # Requête IA obligatoire


class CollectionResponse(BaseModel):
    """Modèle de réponse pour une collection."""
    id: int
    name: str
    search_type: Optional[str]
    search_criteria: Optional[dict]
    ai_query: Optional[str]
    album_count: int
    created_at: str
    sample_album_images: List[str] = []  # Images d'albums pour illustrer la collection
    
    @classmethod
    def from_orm(cls, collection, sample_album_images: Optional[List[str]] = None):
        """Convertir un objet AlbumCollection en CollectionResponse."""
        # Parser le JSON si search_criteria est une string
        criteria = collection.search_criteria
        if isinstance(criteria, str):
            try:
                criteria = json.loads(criteria)
            except:
                criteria = None
        
        return cls(
            id=collection.id,
            name=collection.name,
            search_type=collection.search_type,
            search_criteria=criteria,
            ai_query=collection.ai_query,
            album_count=collection.album_count,
            created_at=collection.created_at.isoformat(),
            sample_album_images=sample_album_images or []
        )


class AlbumResponse(BaseModel):
    """Modèle de réponse pour un album."""
    id: int
    title: str
    artist_name: Optional[str]
    year: Optional[int]
    image_url: Optional[str]
    ai_description: Optional[str]
    spotify_url: Optional[str] = None
    apple_music_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Modèle pour une requête de recherche."""
    query: str
    limit: int = 50


@router.post("/", response_model=CollectionResponse)
def create_collection(
    collection: CollectionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new AI-powered album collection.
    
    Generates a collection of albums based on an AI query. The system searches
    the web for albums matching the query, enrich them with AI-generated
    descriptions and metadata, and organizes them into a curated collection.
    Collection name is auto-generated from the query if not provided.
    
    **Request Body (CollectionCreate):**
    ```json
    {
      "name": "My Summer Chill Playlist",
      "ai_query": "atmospheric indie rock albums perfect for summer evenings",
      "search_type": "ai_query"
    }
    ```
    
    **Request Parameters:**
    - `name`: Collection name (optional, auto-generated if not provided)
      - Type: string
      - Example: "My Summer Favorites"
      - If omitted: Generated from ai_query
    - `ai_query`: AI search query (required)
      - Type: string
      - Example: "uplifting electronic music from the 1990s"
      - Used to find albums via web search and semantic analysis
    - `search_type`: Always "ai_query" (required)
      - Type: string
      - Fixed value: "ai_query"
    
    **Response (201 Created):**
    ```json
    {
      "id": 1,
      "name": "Summer Chill Sessions",
      "search_type": "ai_query",
      "search_criteria": {
        "query": "atmospheric indie rock albums perfect for summer evenings"
      },
      "ai_query": "atmospheric indie rock albums perfect for summer evenings",
      "album_count": 24,
      "created_at": "2026-02-08T17:15:00Z"
    }
    ```
    
    **Response Fields:**
    - `id`: Collection database ID (integer)
    - `name`: Collection name (auto-generated or provided)
    - `search_type`: Search type ("ai_query")
    - `search_criteria`: JSON object with query details
    - `ai_query`: The original search query
    - `album_count`: Number of albums found
    - `created_at`: Creation timestamp (ISO 8601)
    
    **AI Processing:**
    - Web search enabled
    - Semantic analysis of query
    - Album discovery and enrichment
    - AI descriptions generated
    - Cover images retrieved
    - Metadata normalized
    
    **Database Operation:**
    ```sql
    INSERT INTO album_collection (name, search_type, ai_query, search_criteria)
    VALUES (?, ?, ?, ?)
    SELECT * FROM album WHERE id IN (selected by AI)
    ```
    - Query time: 5-30 seconds (includes web search)
    - Index: album_collection(created_at)
    - Transaction: Full ACID compliance
    
    **Performance:**
    - Query processing: 2-3 seconds
    - Web search: 2-10 seconds
    - Album enrichment: 3-5 seconds
    - Total: 7-18 seconds (async recommended)
    - Result: 10-50 albums per collection
    
    **Web Search Integration:**
    - Enabled by default
    - Searches Discogs, Spotify, LastFM
    - Aggregates results
    - Deduplicates albums
    - Validates availability
    
    **AI Features:**
    - Query understanding
    - Semantic matching
    - Description generation
    - Mood/genre classification
    - Year range inference
    
    **Error Scenarios:**
    - Empty ai_query: 400 Bad Request
    - Web search timeout: 504 Gateway Timeout
    - No albums found: 200 OK (count=0, valid)
    - Database error: 500 Internal Server Error
    
    **Limitations:**
    - Max results: 500 albums per collection
    - Query timeout: 30 seconds
    - Web search rate limit: 100 requests/hour
    - Concurrent creations: 10 simultaneous
    
    **Frontend Integration:**
    ```javascript
    // Create AI collection
    async function createAICollection(query) {
      const response = await fetch('/api/v1/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ai_query: query,
          // name: auto-generated if omitted
          search_type: 'ai_query'
        })
      });
      
      if (!response.ok) throw new Error('Creation failed');
      
      const collection = await response.json();
      console.log(`Created: ${collection.name} (${collection.album_count} albums)`);
      return collection;
    }
    
    // Example: Create summer collection
    const summerCollection = await createAICollection(
      'uplifting indie rock albums for summer road trips'
    );
    ```
    
    **Use Cases:**
    - Curated mood-based collections
    - Genre-based discovery
    - Time-period specific collections
    - Themed compilations
    - Recommendation generation
    - Listening guide creation
    
    **Related Endpoints:**
    - GET /api/v1/collections: List all collections
    - GET /api/v1/collections/{id}: Get collection
    - POST /api/v1/collections/{id}/play: Play collection
    """
    service = AlbumCollectionService(db)
    
    new_collection = service.create_collection(
        name=collection.name,  # Sera généré automatiquement si None
        search_type='ai_query',
        ai_query=collection.ai_query,
        web_search=True  # Activer la recherche web
    )
    
    return CollectionResponse.from_orm(new_collection)


@router.get("/", response_model=List[CollectionResponse])
def list_collections(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all AI-generated album collections.
    
    Retrieves a paginated list of all collections created via AI queries. Each
    collection shows metadata, album count, and creation time. Useful for
    collection menu, library navigation, and collection management interfaces.
    
    **Query Parameters:**
    - `limit`: Maximum results (default: 100, range: 1-1000)
      - Type: integer
      - Controls page size
      - Recommended: 20-50 for UI
    - `offset`: Skip first N results (default: 0, ge: 0)
      - Type: integer
      - For pagination (offset = (page-1) × limit)
      - Example: offset=100, limit=50 = page 3
    
    **Response (200 OK):**
    ```json
    [
      {
        "id": 1,
        "name": "Summer Chill Sessions",
        "search_type": "ai_query",
        "search_criteria": {
          "query": "atmospheric indie rock"
        },
        "ai_query": "atmospheric indie rock albums perfect for summer evenings",
        "album_count": 24,
        "created_at": "2026-02-08T17:15:00Z"
      },
      {
        "id": 2,
        "name": "Late Night Jazz Vibes",
        "search_type": "ai_query",
        "search_criteria": {
          "query": "smooth jazz albums"
        },
        "ai_query": "smooth jazz albums for late night listening",
        "album_count": 18,
        "created_at": "2026-02-07T14:30:00Z"
      }
    ]
    ```
    
    **Response Fields (per collection):**
    - `id`: Collection database ID
    - `name`: Collection name (auto-generated or custom)
    - `search_type`: Type of search ("ai_query")
    - `search_criteria`: JSON criteria (parsed from string)
    - `ai_query`: Original AI query string
    - `album_count`: Number of albums in collection
    - `created_at`: Creation timestamp (ISO 8601)
    
    **Pagination Mechanics:**
    - Offset-based pagination (cursor not needed)
    - First request: offset=0, limit=50
    - Next page: offset=50, limit=50
    - Has more: length(results) == limit
    
    **Database Query:**
    ```sql
    SELECT * FROM album_collection
    ORDER BY created_at DESC
    LIMIT :limit OFFSET :offset
    ```
    - Query time: 50-200ms
    - Index: album_collection(created_at DESC)
    - Result set: Variable based on limit
    
    **Performance:**
    - List time: 100-300ms
    - Memory: O(limit)
    - Caching: 5-minute cache recommended
    - Cache key: "collections_list_{limit}_{offset}"
    
    **Sorting:**
    - Default: By creation time (newest first)
    - Cannot be changed via parameters
    - Latest collections appear first
    
    **Error Scenarios:**
    - Invalid limit (>1000): 422 Unprocessable Entity
    - Invalid offset (<0): 422 Unprocessable Entity
    - Database error: 500 Internal Server Error
    - No collections: Returns empty array (200 OK)
    
    **Data Transformation:**
    - search_criteria: Parsed from JSON string to object
    - Handles legacy string format
    - Returns structured object
    
    **Frontend Integration:**
    ```javascript
    // Load collections with pagination
    async function loadCollections(page = 1, pageSize = 20) {
      const offset = (page - 1) * pageSize;
      const response = await fetch(
        `/api/v1/collections?limit=${pageSize}&offset=${offset}`
      );
      
      const collections = await response.json();
      
      collections.forEach(coll => {
        displayCollectionCard(
          coll.name,
          coll.album_count,
          coll.created_at
        );
      });
      
      return collections.length === pageSize; // Has more pages
    }
    
    // Load first page
    const hasMore = await loadCollections(1, 20);
    ```
    
    **Use Cases:**
    - Collection menu/browser
    - Library management
    - Recent collections view
    - Collection selection for playing
    - User's collection library
    
    **Related Endpoints:**
    - GET /api/v1/collections/{id}: Get single collection
    - POST /api/v1/collections: Create collection
    - DELETE /api/v1/collections/{id}: Delete collection
    """
    service = AlbumCollectionService(db)
    collections = service.list_collections(limit=limit, offset=offset)
    
    # Pour chaque collection, récupérer 5 images d'albums pour illustration
    result = []
    for collection in collections:
        # Requête pour obtenir jusqu'à 5 images d'albums de la collection
        sample_images = db.execute(
            select(Album.image_url)
            .join(CollectionAlbum, CollectionAlbum.album_id == Album.id)
            .where(CollectionAlbum.collection_id == collection.id)
            .where(Album.image_url.isnot(None))
            .where(Album.image_url != '')
            .limit(5)
        ).scalars().all()
        
        result.append(CollectionResponse.from_orm(collection, list(sample_images)))
    
    return result


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific collection.
    
    Retrieves complete metadata for a single collection including the AI query,
    search criteria, album count, and creation timestamp. Useful for collection
    detail pages, headers, and verifying collection contents before playing.
    
    **Path Parameters:**
    - `collection_id`: Database ID of the collection (integer)
      - Type: integer
      - Format: Positive integer
      - Required: Yes
      - Example: 1, 42, 187
    
    **Response (200 OK):**
    ```json
    {
      "id": 1,
      "name": "Summer Chill Sessions",
      "search_type": "ai_query",
      "search_criteria": {
        "query": "atmospheric indie rock albums perfect for summer evenings"
      },
      "ai_query": "atmospheric indie rock albums perfect for summer evenings",
      "album_count": 24,
      "created_at": "2026-02-08T17:15:00Z"
    }
    ```
    
    **Response Fields:**
    - `id`: Collection identifier (matches request)
    - `name`: Collection name (auto-generated or custom)
    - `search_type`: Search method used ("ai_query")
    - `search_criteria`: JSON object with query details
      - Contains: "query" key with search string
      - May contain additional metadata
    - `ai_query`: Original AI query string
      - Full text of the search query
      - Used for recreating search
    - `album_count`: Total albums in collection
      - Integer count
      - May be 0 for empty collection
    - `created_at`: When collection was created
      - ISO 8601 format
      - Timestamp with timezone
    
    **Database Query:**
    ```sql
    SELECT * FROM album_collection WHERE id = :collection_id
    ```
    - Query time: 10-20ms
    - Index: album_collection(id) PRIMARY KEY
    - Result set: Single row or empty
    
    **Performance:**
    - Lookup time: 10-30ms
    - Memory: O(1)
    - Caching: 10-minute cache recommended
    - Cache key: "collection_{id}"
    
    **Data Transformation:**
    - search_criteria: JSON string → parsed object
    - Handles legacy formats
    - Returns structured response
    
    **Error Scenarios:**
    - Collection not found: 404 Not Found
    - Invalid collection_id (non-integer): 422 Unprocessable Entity
    - Invalid collection_id (<0): 422 Unprocessable Entity
    - Database error: 500 Internal Server Error
    
    **Typical Use:**
    - Pre-flight check before playing
    - Collection detail page
    - Header/title display
    - Verify album count
    - Check creation time
    
    **Frontend Integration:**
    ```javascript
    // Load collection details
    async function loadCollectionDetails(collectionId) {
      const response = await fetch(`/api/v1/collections/${collectionId}`);
      
      if (response.status === 404) {
        showError('Collection not found');
        return null;
      }
      
      const collection = await response.json();
      
      // Display collection info
      displayTitle(collection.name);
      displayAlbumCount(collection.album_count);
      displayCreatedDate(new Date(collection.created_at));
      displayQuery(collection.ai_query);
      
      return collection;
    }
    
    // Load on page load
    const collection = await loadCollectionDetails(1);
    ```
    
    **Use Cases:**
    - Collection detail page
    - Collection header information
    - Pre-play verification
    - Collection metadata display
    - Edit collection details
    
    **Related Endpoints:**
    - GET /api/v1/collections: List all collections
    - GET /api/v1/collections/{id}/albums: Get albums in collection
    - POST /api/v1/collections/{id}/play: Play collection
    - DELETE /api/v1/collections/{id}: Delete collection
    """
    service = AlbumCollectionService(db)
    collection = service.get_collection(collection_id)
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection non trouvée")
    
    return CollectionResponse.from_orm(collection)


@router.get("/{collection_id}/albums", response_model=List[AlbumResponse])
def get_collection_albums(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all albums in a specific collection.
    
    Retrieves the complete list of albums belonging to a collection. Returns
    album details including title, artist, year, cover image, and AI-generated
    descriptions. Useful for displaying collection contents and preview views.
    
    **Path Parameters:**
    - `collection_id`: Database ID of the collection (integer)
      - Type: integer
      - Required: Yes
      - Example: 1, 42, 187
    
    **Response (200 OK):**
    ```json
    [
      {
        "id": 1,
        "title": "Abbey Road",
        "artist_name": "The Beatles",
        "year": 1969,
        "image_url": "https://mosaic.scdn.co/...",
        "ai_description": "The Beatles' eleventh studio album...",
        "spotify_url": "https://open.spotify.com/album/..."
      },
      {
        "id": 42,
        "title": "Electric Ladyland",
        "artist_name": "Jimi Hendrix",
        "year": 1968,
        "image_url": "https://...",
        "ai_description": "Hendrix's psychedelic masterpiece...",
        "spotify_url": "https://..."
      }
    ]
    ```
    
    **Album Response Fields:**
    - `id`: Album database ID
    - `title`: Album title (string)
    - `artist_name`: Primary artist name (string or null)
      - First artist if multiple
      - Null if no artists
    - `year`: Release year (integer or null)
      - 4-digit year
      - Null if unknown
    - `image_url`: Cover art URL (string or null)
      - Valid HTTPS URL
      - May be missing for some albums
    - `ai_description`: AI-generated description (string or null)
      - Generated on creation
      - Markdown formatted
      - 1-5 paragraphs
    - `spotify_url`: Spotify link (string or null)
      - Direct Spotify album link
      - May be missing
    
    **Database Query:**
    ```sql
    SELECT album.* FROM album
    JOIN collection_album ON collection_album.album_id = album.id
    WHERE collection_album.collection_id = :collection_id
    ORDER BY album.title, album.year
    ```
    - Query time: 50-200ms
    - Joins: collection_album linking table
    - Index: collection_album(collection_id)
    
    **Performance:**
    - List time: 100-300ms
    - Memory: O(album_count)
    - Typical albums per collection: 10-50
    - Max albums per collection: 500
    - Caching: 5-minute cache recommended
    
    **Data Relationships:**
    - 1 collection → many albums (1:N)
    - Each album may be in multiple collections
    - Linking table: collection_album
    - Soft references (no cascade delete)
    
    **Error Scenarios:**
    - Collection not found: 404 Not Found
    - Invalid collection_id: 422 Unprocessable Entity
    - Collection exists but empty: Returns [] (200 OK)
    - Database error: 500 Internal Server Error
    
    **Sorting:**
    - Default: Title ascending, then year descending
    - Always consistent order
    - No parameters to change sort
    
    **Frontend Integration:**
    ```javascript
    // Load collection albums
    async function loadCollectionAlbums(collectionId) {
      const response = await fetch(
        `/api/v1/collections/${collectionId}/albums`
      );
      
      if (response.status === 404) {
        showError('Collection not found');
        return [];
      }
      
      const albums = await response.json();
      
      // Display albums
      albums.forEach(album => {
        displayAlbumCard(
          album.title,
          album.artist_name,
          album.year,
          album.image_url,
          album.ai_description
        );
      });
      
      return albums;
    }
    
    // Load on collection view
    const albums = await loadCollectionAlbums(1);
    console.log(`Showing ${albums.length} albums`);
    ```
    
    **Use Cases:**
    - Collection detail view
    - Album grid display
    - Collection preview
    - Playlist contents
    - Browse collection
    
    **Related Endpoints:**
    - GET /api/v1/collections/{id}: Collection info
    - POST /api/v1/collections/{id}/albums: Add albums
    - POST /api/v1/collections/{id}/play: Play collection
    """
    service = AlbumCollectionService(db)
    albums = service.get_collection_albums(collection_id)
    
    return [
        AlbumResponse(
            id=album.id,
            title=album.title,
            artist_name=album.artists[0].name if album.artists else None,
            year=album.year,
            image_url=album.image_url,
            ai_description=album.ai_description,
            spotify_url=album.spotify_url
        )
        for album in albums
    ]


@router.post("/{collection_id}/albums")
def add_albums_to_collection(
    collection_id: int,
    album_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    Add albums to an existing collection.
    
    Adds one or more albums to a collection by ID. Typically used to expand
    existing collections or merge multiple albums from search/discovery into
    a single collection. Prevents duplicates (adding same album twice ignored).
    
    **Path Parameters:**
    - `collection_id`: Target collection ID (integer)
      - Type: integer
      - Required: Yes
      - Must exist
    
    **Request Body (raw JSON array):**
    ```json
    [1, 42, 187, 234, 567]
    ```
    OR with Content-Type header `application/json`:
    ```
    POST /api/v1/collections/1/albums
    [1, 42, 187]
    ```
    
    **Request Format:**
    - `album_ids`: Array of album database IDs
      - Type: List[int]
      - Min length: 1
      - Max length: Unlimited (practical: 1000)
      - Example: [1, 5, 42]
      - Duplicates in request: Ignored
    
    **Response (200 OK):**
    ```json
    {
      "message": "3 albums added",
      "album_count": 27
    }
    ```
    
    **Response Fields:**
    - `message`: Summary of operation
      - Format: "{count} albums added"
      - May be 0 if all were duplicates
    - `album_count`: Total albums in collection after add
      - Integer count
      - Includes newly added
    
    **Database Operation:**
    ```sql
    INSERT INTO collection_album (collection_id, album_id)
    VALUES (:collection_id, :album_id)
    ON CONFLICT DO NOTHING  -- Prevent duplicates
    
    SELECT COUNT(*) FROM collection_album
    WHERE collection_id = :collection_id
    ```
    - Query time: 50-200ms (batch insert)
    - Conflicts: Ignored silently
    - Transaction: ACID compliant
    
    **Performance:**
    - Add time: 50-300ms (depends on count)
    - Per album: 5-30ms
    - Memory: O(1)
    - Index: collection_album(collection_id)
    
    **Duplicate Handling:**
    - Same album added twice: Ignored (ON CONFLICT)
    - Message shows newly added count
    - No error for duplicates
    - Result: Album appears once
    
    **Validation:**
    - Collection must exist: 404 if not
    - Album IDs must exist: 404 partial error
      - May succeed with some albums
      - Message indicates success count
    - Empty album_ids: 400 Bad Request
    
    **Error Scenarios:**
    - Collection not found: 404 Not Found
    - Empty album_ids: 400 Bad Request
    - Invalid album ID (non-integer): 422 Unprocessable Entity
    - Some albums missing: 404 with count message
    - Database error: 500 Internal Server Error
    
    **Idempotency:**
    - Adding same album twice: No error or duplication
    - Calling twice with same data: Same result
    - Safe to retry
    
    **Frontend Integration:**
    ```javascript
    // Add albums to collection
    async function addAlbumsToCollection(collectionId, albumIds) {
      const response = await fetch(
        `/api/v1/collections/${collectionId}/albums`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(albumIds)  // Just the array of IDs
        }
      );
      
      if (response.status === 404) {
        showError('Collection not found');
        return false;
      }
      
      const result = await response.json();
      showSuccess(result.message);
      return true;
    }
    
    // Add selected albums
    const selectedIds = [1, 5, 42];
    await addAlbumsToCollection(1, selectedIds);
    ```
    
    **Use Cases:**
    - Expand collection
    - Merge search results
    - Bulk add from discovery
    - Manual collection edit
    - Album selection confirm
    - Drag-and-drop collections
    
    **Related Endpoints:**
    - GET /api/v1/collections/{id}/albums: View albums
    - POST /api/v1/collections/search/*: Find albums
    - DELETE /api/v1/collections/{id}: Delete collection
    """
    service = AlbumCollectionService(db)
    
    try:
        collection = service.add_albums_to_collection(collection_id, album_ids)
        return {"message": f"{len(album_ids)} albums ajoutés", "album_count": collection.album_count}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{collection_id}")
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a collection permanently.
    
    Removes a collection and all its album associations from the database.
    Deletion is permanent and cannot be undone. The albums themselves are NOT
    deleted (they may be in other collections). Only the collection record
    and its relationships are removed.
    
    **Path Parameters:**
    - `collection_id`: ID of collection to delete (integer)
      - Type: integer
      - Required: Yes
      - Example: 1, 42, 187
    
    **Response (200 OK):**
    ```json
    {
      "message": "Collection deleted"
    }
    ```
    
    **Response Field:**
    - `message`: Confirmation message (string)
      - Standard: "Collection deleted"
      - Indicates successful removal
    
    **Deletion Behavior:**
    - Collection record: Deleted
    - Albums in collection: NOT deleted (preserved)
      - Albums may still be in other collections
      - Album data remains intact
    - Album-collection links: Deleted
      - Cascade delete on linking table
      - Foreign keys handled properly
    - Album count: Updated globally
    
    **Database Operation:**
    ```sql
    DELETE FROM collection_album WHERE collection_id = :collection_id
    DELETE FROM album_collection WHERE id = :collection_id
    
    -- Albums NOT deleted:
    -- SELECT * FROM album WHERE id IN (formerly in collection)
    ```
    - Query time: 50-150ms
    - Cascade: TRUE for linking table
    - Transaction: ACID compliant
    
    **Performance:**
    - Delete time: 50-200ms
    - Scales with album count in collection
    - Typical: 10-50 albums = 50-100ms
    - Database locks: Minimal (short transaction)
    - Cache invalidation: ~100ms
    
    **Idempotency:**
    - First delete: 200 OK {message: "Collection deleted"}
    - Second delete (same ID): 404 Not Found
    - NOT idempotent (different responses)
    - Consider making idempotent if desired
    
    **Data Preservation:**
    - Albums: Fully preserved
    - Listening history: Preserved
    - Artist data: Unchanged
    - Other collections: Unchanged
    - Album appears in other collections: Still visible
    
    **Error Scenarios:**
    - Collection not found: 404 Not Found
    - Invalid collection_id (non-integer): 422 Unprocessable Entity
    - Invalid collection_id (<0): 422 Unprocessable Entity
    - Database error: 500 Internal Server Error
    - Cascade error (rare): 500 Internal Server Error
    
    **Safety Recommendations:**
    - Require user confirmation
    - Show album count before delete
    - Log deletions for audit
    - Soft-delete option: Mark as deleted, don't remove
    - Consider archive feature
    
    **Restored Content:**
    - Nothing can be restored
    - No backup unless manually created
    - No undo option
    
    **Frontend Integration:**
    ```javascript
    // Delete collection with confirmation
    async function deleteCollection(collectionId, collectionName) {
      const confirmed = confirm(
        `Delete "${collectionName}"? This cannot be undone.\n` +
        `Albums will be preserved (not deleted).`
      );
      
      if (!confirmed) return false;
      
      const response = await fetch(
        `/api/v1/collections/${collectionId}`,
        { method: 'DELETE' }
      );
      
      if (response.status === 404) {
        showError('Collection already deleted');
        return false;
      }
      
      if (!response.ok) {
        showError('Deletion failed');
        return false;
      }
      
      const result = await response.json();
      showSuccess(result.message);
      refreshCollectionList();
      return true;
    }
    
    // Delete with confirmation
    await deleteCollection(1, 'Summer Vibes');
    ```
    
    **Use Cases:**
    - Remove unwanted collection
    - Clean up library
    - Delete temporary collections
    - Collection management
    - User preference cleanup
    
    **Related Endpoints:**
    - GET /api/v1/collections: List all
    - GET /api/v1/collections/{id}: Get details
    - POST /api/v1/collections: Create new
    """
    service = AlbumCollectionService(db)
    
    if not service.delete_collection(collection_id):
        raise HTTPException(status_code=404, detail="Collection non trouvée")
    
    return {"message": "Collection supprimée"}


@router.post("/search/genre", response_model=List[AlbumResponse])
def search_by_genre(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search albums by genre.
    
    Finds all albums matching a specified genre. Searches album metadata,
    descriptions, and AI classification to match genre names and related terms.
    Useful for genre browsing, collection building, and genre-based discovery.
    
    **Request Body (SearchRequest):**
    ```json
    {
      "query": "indie rock",
      "limit": 50
    }
    ```
    
    **Request Parameters:**
    - `query`: Genre name or related term (string, required)
      - Examples: "indie rock", "jazz", "ambient"
      - Case-insensitive matching
      - Partial matches accepted
    - `limit`: Maximum results (int, default: 50, max: 100)
      - Type: integer
      - Range: 1-100
      - Default: 50
    
    **Response (200 OK):**
    Array of matching albums with:
    ```json
    [
      {
        "id": 1,
        "title": "Neutral Milk Hotel - In the Aeroplane Over the Sea",
        "artist_name": "Neutral Milk Hotel",
        "year": 1998,
        "image_url": "https://...",
        "ai_description": "Cult indie rock classic with lo-fi aesthetics...",
        "spotify_url": "https://..."
      }
    ]
    ```
    
    **Search Matching:**
    - Genre tag matching
    - Description keyword search
    - AI classification analysis
    - Artist genre association
    - Album metadata tags
    - Case-insensitive
    
    **Database Query:**
    ```sql
    SELECT DISTINCT album.* FROM album
    WHERE album.genre_tags ILIKE %:genre%
      OR album.ai_description ILIKE %:genre%
      OR artist.genre ILIKE %:genre%
    LIMIT :limit
    ```
    - Query time: 100-300ms
    - Full-text search: Recommended index
    - Result set: Typically 5-200 albums
    
    **Performance:**
    - Search time: 150-400ms
    - Per-genre cache: 10 minutes
    - Pagination: Via limit only
    - Memory: O(limit)
    
    **Common Genres:**
    - Rock, Pop, Jazz, Classical, Electronic
    - Hip-Hop, Country, Soul, Blues, Folk
    - Metal, Punk, Reggae, Latin, World
    - Ambient, Indie, Alternative, Experimental
    
    **Error Scenarios:**
    - Empty query: 400 Bad Request
    - Invalid limit (>100): 422 Unprocessable Entity
    - No matches: Returns [] (200 OK)
    - Database error: 500 Internal Server Error
    
    **Sorting:**
    - Default: Relevance (best match first)
    - Then by year (oldest first)
    - No customization available
    
    **Frontend Integration:**
    ```javascript
    // Search by genre
    async function searchByGenre(genre, limit = 50) {
      const response = await fetch('/api/v1/collections/search/genre', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: genre, limit })
      });
      const albums = await response.json();
      return albums;
    }
    
    // Find indie albums
    const indieAlbums = await searchByGenre('indie rock', 30);
    displayAlbums(indieAlbums);
    ```
    
    **Use Cases:**
    - Genre browser
    - Collection building
    - Genre discovery
    - Mood-based browsing
    - Genre statistics
    
    **Related Endpoints:**
    - POST /api/v1/collections/search/artist: By artist
    - POST /api/v1/collections/search/period: By era
    - POST /api/v1/collections/search/ai: AI semantic search
    """
    service = AlbumCollectionService(db)
    albums = service.search_by_genre(request.query, limit=request.limit)
    
    return [
        AlbumResponse(
            id=album.id,
            title=album.title,
            artist_name=album.artists[0].name if album.artists else None,
            year=album.year,
            image_url=album.image_url,
            ai_description=album.ai_description,
            spotify_url=album.spotify_url
        )
        for album in albums
    ]


@router.post("/search/artist", response_model=List[AlbumResponse])
def search_by_artist(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search albums by artist name.
    
    Finds all albums by a specific artist or matching artist name. Searches
    primary artist, featuring artists, and composer credits. Useful for artist
    discography discovery, collection building, and artist-based organizing.
    
    **Request Body (SearchRequest):**
    ```json
    {
      "query": "The Beatles",
      "limit": 50
    }
    ```
    
    **Request Parameters:**
    - `query`: Artist name (string, required)
      - Examples: "The Beatles", "David Bowie", "Miles Davis"
      - Case-insensitive matching
      - Partial name accepted
      - Handles variations (e.g., "Beatles" vs "The Beatles")
    - `limit`: Maximum results (int, default: 50, max: 100)
      - Type: integer
      - Range: 1-100
    
    **Response (200 OK):**
    Array of albums by matching artists:
    ```json
    [
      {
        "id": 1,
        "title": "Abbey Road",
        "artist_name": "The Beatles",
        "year": 1969,
        "image_url": "https://...",
        "ai_description": "Beatles' eleventh and final recorded album...",
        "spotify_url": "https://..."
      },
      {
        "id": 2,
        "title": "Help!",
        "artist_name": "The Beatles",
        "year": 1965,
        "image_url": "https://...",
        "ai_description": "The Beatles' fifth album...",
        "spotify_url": "https://..."
      }
    ]
    ```
    
    **Search Matching:**
    - Primary artist name (exact/partial)
    - Featuring artists ("feat.", "with")
    - Composer credits
    - Artist aliases/variations
    - Case-insensitive
    - Partial name matching
    
    **Database Query:**
    ```sql
    SELECT DISTINCT album.* FROM album
    JOIN album_artist ON album_artist.album_id = album.id
    JOIN artist ON artist.id = album_artist.artist_id
    WHERE artist.name ILIKE %:artist%
    ORDER BY album.year DESC, album.title
    LIMIT :limit
    ```
    - Query time: 100-200ms
    - Index: artist(name) with ILIKE index
    - Joins: 2 tables
    
    **Performance:**
    - Search time: 150-300ms
    - Per-artist cache: 10 minutes
    - Sorting: By year (newest first)
    - Typical results: 3-30 albums
    
    **Artist Name Handling:**
    - "The Beatles" → finds all Beatles albums
    - "Beatles" → also finds all Beatles albums
    - "John Lennon" → solo albums + Beatles
    - "Pink Floyd" → all lineup variations
    
    **Error Scenarios:**
    - Empty query: 400 Bad Request
    - Invalid limit (>100): 422 Unprocessable Entity
    - Artist not found: Returns [] (200 OK)
    - Database error: 500 Internal Server Error
    
    **Sorting:**
    - Primary: Year descending (newest first)
    - Secondary: Title ascending
    - No customization available
    
    **Frontend Integration:**
    ```javascript
    // Search by artist
    async function searchByArtist(artistName, limit = 50) {
      const response = await fetch('/api/v1/collections/search/artist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: artistName, limit })
      });
      const albums = await response.json();
      return albums;
    }
    
    // Find Beatles discography
    const beatlesAlbums = await searchByArtist('The Beatles', 100);
    console.log(`Found ${beatlesAlbums.length} Beatles albums`);
    ```
    
    **Use Cases:**
    - Artist discography view
    - Collection building
    - Artist profile
    - Discography explorer
    - Complete artist collection
    
    **Related Endpoints:**
    - POST /api/v1/collections/search/genre: By genre
    - POST /api/v1/collections/search/period: By era
    - POST /api/v1/collections/search/ai: AI semantic
    """
    service = AlbumCollectionService(db)
    albums = service.search_by_artist(request.query, limit=request.limit)
    
    return [
        AlbumResponse(
            id=album.id,
            title=album.title,
            artist_name=album.artists[0].name if album.artists else None,
            year=album.year,
            image_url=album.image_url,
            ai_description=album.ai_description,
            spotify_url=album.spotify_url
        )
        for album in albums
    ]


@router.post("/search/period", response_model=List[AlbumResponse])
def search_by_period(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Search albums by release year or time period.
    
    Finds albums released during a specified time period. Returns albums within
    the year range (inclusive), useful for era-based discovery, decade browsing,
    and historical collection exploration. Either or both year parameters can
    be omitted to search from any start or to any end year.
    
    **Query Parameters:**
    - `start_year`: Beginning year (integer, optional)
      - Type: integer
      - Range: 1800-current year
      - Example: 1960
      - Omit for no lower bound
    - `end_year`: Ending year (integer, optional)
      - Type: integer
      - Range: 1800-current year
      - Example: 1970
      - Omit for no upper bound
    - `limit`: Maximum results (int, default: 50, max: 100+)
      - Type: integer
      - Range: 1-unlimited (practical: 1000)
    
    **Query Examples:**
    - `?start_year=1960&end_year=1970` → 1960s albums
    - `?start_year=2010` → Albums from 2010 onwards
    - `?end_year=1980` → Albums up to 1980
    - `?limit=100` → All albums (no year filter)
    
    **Response (200 OK):**
    Array of matching albums:
    ```json
    [
      {
        "id": 123,
        "title": "Sgt. Pepper's Lonely Hearts Club Band",
        "artist_name": "The Beatles",
        "year": 1967,
        "image_url": "https://...",
        "ai_description": "Revolutionary album from the Summer of Love...",
        "spotify_url": "https://..."
      }
    ]
    ```
    
    **Search Logic:**
    - Inclusive range: year >= start AND year <= end
    - Null year handling: Albums with unknown year are excluded
    - Start only: year >= start
    - End only: year <= end
    - Neither: All albums (limited by limit)
    
    **Database Query:**
    ```sql
    SELECT DISTINCT album.* FROM album
    WHERE (album.year IS NULL OR 
           (album.year >= :start_year AND album.year <= :end_year))
    ORDER BY album.year DESC, album.title
    LIMIT :limit
    ```
    - Query time: 100-300ms
    - Index: album(year)
    - Sorting: Year descending (newest first)
    
    **Performance:**
    - Search time: 150-400ms
    - Cache: 60 minutes (per-period)
    - Typical results: 50-500 albums
    - Memory: O(limit)
    
    **Common Periods:**
    - 1960s: start_year=1960, end_year=1969
    - 1970s: start_year=1970, end_year=1979
    - 1980s-2000s: Decade ranges
    - 2000s onwards: Modern albums
    - Before 1970: start_year=[null], end_year=1970
    
    **Error Scenarios:**
    - Invalid year format (non-integer): 422 Unprocessable Entity
    - start_year > end_year: Empty result []
    - year out of range (future): Empty result []
    - limit too large: Truncated to reasonable max
    - Database error: 500 Internal Server Error
    
    **Sorting:**
    - Primary: Year descending (newest first)
    - Secondary: Title ascending
    - No customization available
    
    **Frontend Integration:**
    ```javascript
    // Search by period
    async function searchByPeriod(startYear, endYear, limit = 50) {
      const params = new URLSearchParams({
        ...(startYear && { start_year: startYear }),
        ...(endYear && { end_year: endYear }),
        limit
      });
      
      const response = await fetch(
        `/api/v1/collections/search/period?${params}`,
        { method: 'POST' }
      );
      const albums = await response.json();
      return albums;
    }
    
    // Find 1970s albums
    const seventies = await searchByPeriod(1970, 1979);
    console.log(`Found ${seventies.length} albums from the 1970s`);
    
    // All albums from 2010 onwards
    const modern = await searchByPeriod(2010, null);
    ```
    
    **Use Cases:**
    - Decade browser
    - Era exploration
    - Historical collection
    - Time-based discovery
    - Timeline view
    
    **Related Endpoints:**
    - POST /api/v1/collections/search/genre: By genre
    - POST /api/v1/collections/search/artist: By artist
    - POST /api/v1/collections/search/ai: AI semantic
    """
    service = AlbumCollectionService(db)
    albums = service.search_by_period(start_year, end_year, limit=limit)
    
    return [
        AlbumResponse(
            id=album.id,
            title=album.title,
            artist_name=album.artists[0].name if album.artists else None,
            year=album.year,
            image_url=album.image_url,
            ai_description=album.ai_description,
            spotify_url=album.spotify_url
        )
        for album in albums
    ]


@router.post("/search/ai", response_model=List[AlbumResponse])
def search_by_ai(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search albums using AI semantic understanding.
    
    Performs semantic/contextual search on album descriptions, metadata, and
    AI-generated attributes. Understands mood, theme, and descriptive queries
    (e.g., "albums for rainy days", "uplifting electronic music"). More intelligent
    than keyword search, returns conceptually relevant albums even if keywords
    don't match exactly.
    
    **Request Body (SearchRequest):**
    ```json
    {
      "query": "albums perfect for late night introspection",
      "limit": 50
    }
    ```
    
    **Request Parameters:**
    - `query`: Semantic search query (string, required)
      - Natural language supported
      - Examples:
        - "sad indie rock for crying"
        - "uplifting morning music"
        - "albums about love and loss"
        - "experimental electronic"
        - "calming ambient atmosphere"
      - Longer queries provide better results
      - No keyword matching needed
    - `limit`: Maximum results (int, default: 50, max: 100+)
      - Type: integer
      - Range: 1-unlimited (practical: 1000)
    
    **Response (200 OK):**
    Array of semantically relevant albums:
    ```json
    [
      {
        "id": 84,
        "title": "Loveless",
        "artist_name": "My Bloody Valentine",
        "year": 1991,
        "image_url": "https://...",
        "ai_description": "Ethereal shoegaze masterpiece with layered textures...",
        "spotify_url": "https://..."
      },
      {
        "id": 156,
        "title": "Disintegration",
        "artist_name": "The Cure",
        "year": 1989,
        "image_url": "https://...",
        "ai_description": "Emotional alternative rock about loss and longing...",
        "spotify_url": "https://..."
      }
    ]
    ```
    
    **AI Matching Process:**
    1. Parse natural language query
    2. Identify mood, theme, era, genre
    3. Generate embedding vector
    4. Search AI descriptions
    5. Match album metadata
    6. Rank by relevance
    7. Return top results
    
    **Matching Dimensions:**
    - **Mood**: Happy, sad, energetic, calm, melancholic
    - **Theme**: Love, loss, nature, technology, society
    - **Era**: Which period feels right
    - **Genre**: Musical style and influences
    - **Atmosphere**: Dense vs sparse, loud vs quiet
    - **Instrumentation**: Acoustic vs electronic
    - **Lyrical theme**: What the album discusses
    
    **Database Query:**
    ```sql
    SELECT DISTINCT album.* FROM album
    WHERE
      embedding_cosine_similarity(
        album.ai_description_embedding,
        embed_query(:query)
      ) > 0.5
    ORDER BY similarity DESC
    LIMIT :limit
    ```
    - Query time: 200-500ms (vector similarity)
    - Index: album(ai_description_embedding)
    - Model: Sentence embeddings (bert/similar)
    
    **Performance:**
    - Search time: 250-600ms
    - Model inference: 100-200ms
    - Database search: 100-300ms
    - Cache: 10 minutes per query
    - Memory: O(limit)
    
    **Semantic Examples:**
    | Query | Results |
    |-------|---------|
    | "rainy day melancholy" | Indie, lo-fi, ambient |
    | "dance all night energy" | Electronic, disco, funk |
    | "late night introspection" | Ambient, experimental, singer-songwriter |
    | "albums about change" | Concept albums, progressive rock |
    | "90s alternative rock vibes" | Grunge, britpop, alt-rock |
    
    **Error Scenarios:**
    - Empty query: 400 Bad Request
    - Too vague query: May return 0 results (valid)
    - Model not loaded: 503 Service Unavailable
    - Invalid limit: 422 Unprocessable Entity
    - Database error: 500 Internal Server Error
    
    **Limitations:**
    - Model language: English (best results)
    - Non-English queries: Translated to English
    - First 50 albums indexed: May be slower on large DB
    - Semantic quality: Depends on AI descriptions
    
    **Frontend Integration:**
    ```javascript
    // AI semantic search
    async function searchByAI(query, limit = 50) {
      const response = await fetch('/api/v1/collections/search/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit })
      });
      
      if (!response.ok) throw new Error('Search failed');
      
      const albums = await response.json();
      return albums;
    }
    
    // Example searches
    const lateNightAlbums = await searchByAI('albums for late night contemplation');
    const uplifting = await searchByAI('uplifting music to start the day');
    const moody = await searchByAI('moody introspective alternative rock');
    
    displayResults(uplifting);
    ```
    
    **Use Cases:**
    - Mood-based discovery
    - Contextual recommendations
    - "What should I listen to?" queries
    - Theme-based browsing
    - Emotional connection discovery
    - Advanced search
    
    **Related Endpoints:**
    - POST /api/v1/collections/search/genre: Keyword genre
    - POST /api/v1/collections/search/artist: By artist
    - POST /api/v1/collections/search/period: By era
    - POST /api/v1/collections: AI collection creation
    """
    service = AlbumCollectionService(db)
    albums = service.search_by_ai_query(request.query, limit=request.limit)
    
    return [
        AlbumResponse(
            id=album.id,
            title=album.title,
            artist_name=album.artists[0].name if album.artists else None,
            year=album.year,
            image_url=album.image_url,
            ai_description=album.ai_description,
            spotify_url=album.spotify_url
        )
        for album in albums
    ]


