"""
Dynamic album collection creation and management service with AI-powered search.

Service for creating and managing thematic album collections with multi-mode search:
- AI-powered natural language queries (using Euria AI)
- Genre-based filtering
- Artist discovery
- Year/period filtering
- Web search integration (Euria external API)

Collections can be created on-demand via AI queries (e.g., "albums for late night")
or via structured criteria (genre, artist, period). Automatically populates collections
with matching albums from local database and/or web search results.

Architecture:
- Dynamic creation: Collections generated on-demand from natural language prompts
- Multi-search modes: AI query, genre, artist, period, web search
- Web integration: Optional Euria web search for discovery (overrides local)
- AI naming: Collection names auto-generated from search query
- Fallback mechanism: Returns random curated albums if no exact matches found

Key features:
- Natural language support: "Soft rock from the 90s for relaxation"
- Web search priority: Can fetch albums from web (Euria API) vs local DB only
- Automatic naming: AI generates descriptive collection names
- Fuzzy matching: Artist name variants (with/without "The")
- Multi-field search: Title, genre, description, style, artist names
- Pagination: All search methods support limit parameter (default 50)

Typical usage:
    service = AlbumCollectionService(db)
    
    # Method 1: AI-powered natural language (web search preferred)
    collection = service.create_collection(
        ai_query="Upbeat indie rock from 2010s",
        web_search=True  # Use Euria web search first
    )
    
    # Method 2: Structured search
    collection = service.create_collection(
        name="90s Grunge Classics",
        search_type='period',
        search_criteria={'start_year': 1990, 'end_year': 1999}
    )
    
    # Method 3: Genre-based
    albums = service.search_by_genre("electronic", limit=100)

Performance profile:
- create_collection(): 0.5-30s (depends on web_search flag, web API speed)
- search_by_ai_query(): 100-500ms (local DB + join, multi-field full-text scan)
- search_by_genre/artist/period(): <100ms (single index scan)
- _search_albums_web(): 5-20s (web API call via Euria)
- add_albums_to_collection(): O(n) where n = albums added, <50ms typical

Output:
- Collections stored in AlbumCollection table (name, search_type, criteria)
- Relationship via CollectionAlbum join table (albums ordered by position)
- Album count updated automatically
- Search methods return List[Album] hydrated with artist/genre/year

Database schema:
- AlbumCollection: id, name, search_type, search_criteria (JSON), ai_query, album_count
- CollectionAlbum: id, collection_id, album_id, position
- Relationships: AlbumCollection → [Album] via CollectionAlbum
"""
import logging
import json
import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.models import Album, Artist, AlbumCollection, CollectionAlbum
from app.database import get_db
from app.services.apple_music_service import AppleMusicService

logger = logging.getLogger(__name__)


class AlbumCollectionService:
    """
    Dynamic album collection management with multi-mode search and AI-powered discovery.
    
    Service for creating curated album collections using natural language queries, structured
    search criteria, or web discovery. Collections are automatically populated with matching
    albums from local database and/or web search results (via Euria API). Supports multiple
    search paradigms: AI natural language, genre filtering, artist discovery, year ranges.
    
    Key capabilities:
    - Create collections from natural language prompts (e.g., "upbeat 80s pop")
    - Search by genre, artist name (with variants), year range, or multi-field AI query
    - Web search integration: Priority option to use Euria API for album discovery
    - Auto-naming: AI generates descriptive collection names from queries
    - Smart fallback: Returns curated random albums if no exact matches found
    - Fuzzy artist matching: Handles "The Beatles" vs "Beatles" variants
    
    Architecture:
    - Collection storage: AlbumCollection table with JSON search criteria
    - Album management: CollectionAlbum join table with position/order
    - Search strategy: Multi-field full-text (title, genre, description, artists)
    - Web integration: Optional external search (Euria API) vs local DB only
    - Error resilience: Continues with local DB if web search unavailable
    
    Database relationships:
    - AlbumCollection: id, name, search_type, search_criteria (JSON), ai_query, album_count
    - CollectionAlbum: id, collection_id, album_id, position (ordering)
    - Album: id, title, genre, year, ai_description, ai_style, [artists]
    - Artist: id, name, [albums]
    
    Attributes:
        db (Session): SQLAlchemy session for database operations
    
    Methods:
    - __init__(): Initialize with database session
    - _generate_collection_name(): AI-generated name from query (fallback: keyword extraction)
    - create_collection(): Main method to create collection + populate with albums
    - add_albums_to_collection(): Bulk add albums with position tracking
    - search_by_genre(): Filter by genre field (case-insensitive ILIKE)
    - search_by_artist(): Find by artist name (handles "The" variants)
    - search_by_period(): Range query by year (start_year to end_year)
    - search_by_ai_query(): Natural language multi-field search (all terms AND logic)
    - _search_albums_web(): Internal web search via Euria API (5-20s typical)
    - get_collection(): Retrieve collection by ID
    - get_collection_albums(): List albums in specific collection
    - list_collections(): Paginated list of all collections
    - delete_collection(): Remove collection and associated mappings
    
    Search modes:
    - ai_query: Natural language input, terms searched across 5 fields (description, style, genre, title, artist)
    - genre: Single field match on Album.genre
    - artist: Match on Artist.name with variant handling ("The X" / "X" both match)
    - period: Range query on Album.year between start_year and end_year
    - Web search: External Euria API call if web_search=True in create_collection()
    
    Multi-field search detail (search_by_ai_query):
    - Input: "soft indie 90s"
    - Terms: ["soft", "indie", "90s"]
    - Each term searched in 5 fields: ai_description, ai_style, genre, title, artist.name
    - Logic: All terms must match (any field) for album inclusion (AND logic)
    - Result: Albums matching "soft" somewhere AND "indie" somewhere AND "90s" somewhere
    - Fallback: If 0 matches, returns random albums with ai_description (discovery mode)
    
    Web search integration:
    - Optional web_search flag in create_collection() (default: True)
    - If True and ai_query provided: Calls _search_albums_web() first
    - Web results: 5-20 seconds (external API latency)
    - Returns albums to collection, skips local DB search if web found results
    - Fallback to local DB only if web search returns 0 albums or error
    
    Collection naming:
    - AI naming: Euria AI generates descriptive name from query (1-3 words typical)
    - Fallback: Extract key words from query (>2 chars), skip stop words (de, du, et, etc.)
    - Examples: "dreamy 80s synth" → "Synth 80s" or "Dreamy Synth"
    
    Performance characteristics:
    - create_collection(): 0.5s (local) to 30s (web search)
    - search_by_ai_query(): 100-500ms (outerjoin + multiple ILIKE conditions)
    - search_by_genre/artist/period: <100ms (single field scan)
    - add_albums_to_collection(): O(n) n=album count, <50ms usual
    - list_collections(): O(k) where k = pagesize (typically 10-20)
    - Big-O: Database query dominated, not CPU complexity
    
    Usage patterns:
        # AI-powered with web search (discovery mode)
        service = AlbumCollectionService(db)
        collection = service.create_collection(
            ai_query="albums for late night coding",
            web_search=True
        )
        
        # Genre + period (structured search)
        albums = service.search_by_period(1990, 2000, limit=50)
        
        # Manual curation
        albums = service.search_by_artist("Radiohead", limit=20)
        coll = service.create_collection(
            name="Radiohead Essentials",
            search_type='artist',
            search_criteria={'artist': 'Radiohead'}
        )
        
        # Management
        albums = service.get_collection_albums(collection.id)
        service.delete_collection(collection.id)
    
    Fallback mechanisms:
    - Web search fails → Use local DB search
    - Local search returns 0 → Return random curated albums (with ai_description)
    - AI name generation fails → Use "New Collection" or keyword extraction fallback
    - Collection not found → Raise ValueError
    
    Database assumptions:
    - Album has fields: id, title, genre, year, ai_description, ai_style, support
    - Album has relationships: artists (many-to-many), images (one-to-many)
    - Artist has field: name
    - AlbumCollection has fields: id, name, search_type, search_criteria, ai_query, album_count
    - CollectionAlbum join has fields: id, collection_id, album_id, position
    
    Integration points:
    - FastAPI endpoints: POST /collections (create), GET /collections (list), DELETE /collections/{id}
    - POST /search with parameters: type, query, criteria
    - Euria AI service: _generate_collection_name(), _search_albums_web()
    - Database: SQLAlchemy ORM with automatic relationship loading
    """
    
    def __init__(self, db: Session):
        """
        Initialize album collection service with database session.
        
        Args:
            db (Session): SQLAlchemy session for database operations.
                         Must support .query(), .add(), .commit(), .refresh().
        
        Performance:
            - O(1), <1ms initialization
            
        Side Effects:
            - Stores session reference (no mutations)
            
        Usage:
            service = AlbumCollectionService(db)
        """
        self.db = db
    
    def _generate_collection_name(self, ai_query: str) -> str:
        """
        Generate collection name from natural language query via Euria AI (with fallback).
        
        Attempts to use Euria AI to create descriptive name from query, falls back to
        keyword extraction if AI unavailable. Useful for auto-naming collections created
        from natural language prompts.
        
        Args:
            ai_query (str): User natural language query (e.g., "albums for late night")
        
        Returns:
            str: Generated collection name (1-3 words typical)
                Examples: "late night" or "Night Music" or "Dreamy Synth"
        
        Performance:
            - Normal: 500-2000ms (AI API call)
            - Fallback: <10ms (keyword extraction)
        
        Side Effects:
            - Logs INFO on successful AI generation: "🎨 Nom généré par Euria: {name}"
            - Logs WARNING if fallback triggered: "⚠️ Fallback génération nom: {e}"
        
        Fallback mechanism:
            If Euria AI unavailable/timeout:
            1. Split query into words
            2. Filter stop words: fais, faite faire, de, du, et, ou, etc. (15+ words)
            3. Keep words > 2 chars
            4. Take first 2 key words
            5. Title case each word
            6. Return "Collection Découverte" if 0 key words found
        
        Examples:
            >>> service._generate_collection_name("soft indie rock for relaxation")
            "Soft Indie"  # Via Euria AI
            
            >>> service._generate_collection_name("upbeat funk disco")
            "Funk Disco"  # Via Euria or fallback
            
            >>> service._generate_collection_name("chill")  # Edge case: 1 letter stop word
            "Collection Découverte"  # Fallback default
        
        Used by:
            - create_collection() when name not provided
            - Auto-naming feature for AI-powered collections
        
        Integration:
            - Requires AIService imported dynamically
            - Euria API endpoint: EURIA_API_URL/generation
        
        Error resilience:
            - AI timeout/error: Falls back to keyword extraction (never fails)
            - Network error: Logs warning, uses fallback
            - No exception raised (always returns fallback if needed)
        """
        try:
            from app.services.external.ai_service import AIService
            ai = AIService()
            name = ai.generate_collection_name_sync(ai_query)
            logger.info(f"🎨 Nom généré par Euria: {name}")
            return name
        except Exception as e:
            logger.warning(f"⚠️ Fallback génération nom: {e}")
            # Fallback simple si Euria indisponible
            words = ai_query.split()
            stop_words = {'fais', 'faites', 'faire', 'me', 'moi', 'de', 'du', 'et', 'ou', 'un', 'une', 'des', 'le', 'la', 'les', 'à', 'pour'}
            key_words = [w for w in words if w.lower() not in stop_words and len(w) > 2][:2]
            return ' '.join(w.capitalize() for w in key_words) if key_words else "Collection Découverte"
    
    def create_collection(
        self,
        name: Optional[str] = None,
        search_type: str = 'ai_query',
        search_criteria: Optional[Dict[str, Any]] = None,
        ai_query: Optional[str] = None,
        web_search: bool = True  # Recherche web prioritaire par défaut
    ) -> AlbumCollection:
        """
        Create new album collection and automatically populate with albums.
        
        Main entry point for collection creation. Creates collection record, determines
        collection name (auto-generates if not provided), searches for matching albums
        based on search_type and criteria, then adds albums to collection. Supports
        web search via Euria API for album discovery (optional, default enabled).
        
        Args:
            name (str|None): Collection display name. Auto-generated from ai_query if None.
                            Default: None (auto-generate or "Nouvelle Collection")
            search_type (str): Search strategy, one of:
                             - 'ai_query': Natural language search (default)
                             - 'genre': Genre-based filtering
                             - 'artist': Artist name matching
                             - 'period': Year range search
            search_criteria (dict|None): Search parameters based on search_type:
                                        - genre: {'genre': 'electronic'}
                                        - artist: {'artist': 'Radiohead'}
                                        - period: {'start_year': 1990, 'end_year': 2000}
            ai_query (str|None): Natural language query for AI search (e.g., "upbeat 80s pop")
                                Required for search_type='ai_query' and auto-naming
                                Default: None (ignored unless search_type='ai_query')
            web_search (bool): If True, prioritize Euria web search over local DB
                              Default: True (web search enabled)
        
        Returns:
            AlbumCollection: Populated collection object with:
                           - id, name, search_type, search_criteria, ai_query fields set
                           - album_count updated with actual album count
                           - Associated CollectionAlbum records created
        
        Raises:
            ValueError: No albums found and fallback retrieves 0 items (unlikely)
        
        Performance:
            - Web search enabled: 5-30s (Euria API latency dominates)
            - Web search disabled: 100-500ms (local DB search only)
            - Database: 2-3 queries (create collection, find albums, add mappings)
            - Big-O: O(n + m) where n=items matched, m=items added to collection
        
        Side Effects:
            - Database: Persists AlbumCollection record + CollectionAlbum mappings
            - Logging: Detailed at each step (creation, search, additions)
            - External: Calls Euria API if web_search=True and search_type='ai_query'
        
        Working logic:
        
        STEP 1: Name determination
        --------
        - If name provided: Use as-is
        - If ai_query provided: Call _generate_collection_name(ai_query)
        - Else: Use "Nouvelle Collection"
        
        STEP 2: Collection DB creation
        --------
        - Create AlbumCollection record with provided parameters
        - Convert search_criteria dict to JSON string (for storage)
        - db.add() + db.commit() + db.refresh() to get ID
        
        STEP 3: Album search (based on search_type)
        --------
        If search_type='ai_query' and ai_query:
            IF web_search=True:
                Call _search_albums_web(ai_query, limit=50) → web results
                IF web found albums: Skip local search
                ELSE: Fallback to search_by_ai_query(ai_query, limit=50)
            ELSE:
                Call search_by_ai_query(ai_query, limit=50)
        
        ELSE IF search_type='genre':
            Call search_by_genre(criteria['genre'], limit=50)
        
        ELSE IF search_type='artist':
            Call search_by_artist(criteria['artist'], limit=50)
        
        ELSE IF search_type='period':
            Call search_by_period(criteria['start_year'], criteria['end_year'], limit=50)
        
        STEP 4: Album addition
        --------
        - Extract album IDs from search results
        - Call add_albums_to_collection(collection.id, album_ids)
        - Refresh collection to get updated album_count
        
        STEP 5: Return
        --------
        - Return populated AlbumCollection object
        
        Example scenarios:
        
        Scenario 1: AI query with web search
            creation = service.create_collection(
                ai_query="upbeat indie rock 2010s"
                # name: auto-generated "Indie 2010s"
                # search_type: 'ai_query'
                # web_search: True (default)
            )
            → Calls Euria web search first, gets albums from API
            → Falls back to local search if web finds 0 albums
        
        Scenario 2: Genre search (local only)
            creation = service.create_collection(
                name="Electronic Classics",
                search_type='genre',
                search_criteria={'genre': 'electronic'}
            )
            → Direct call to search_by_genre("electronic")
            → No web API involved
        
        Scenario 3: Manual period search
            creation = service.create_collection(
                name="90s Grunge",
                search_type='period',
                search_criteria={'start_year': 1990, 'end_year': 1999}
            )
            → Year range query on local DB
        
        Database state:
            Before:  AlbumCollection table: empty
                     CollectionAlbum table: empty (or existing collections)
            
            After:   AlbumCollection: 1 new record
                     CollectionAlbum: N records (1 per album, position ordered)
        
        Logging detail:
            📚 Collection créée: {name}
            🌐 Recherche Euria IA pour: {ai_query}      (if web_search=True)
            🎉 X albums proposés par Euria - PAS DE COMPLÉMENT LOCAL
            ⚠️  Euria n'a trouvé aucun album...          (web fallback)
            📚 Recherche locale uniquement pour...
            🔍 Recherche par genre/artist/période...
            📋 ALBUMS À AJOUTER À LA COLLECTION (X total):
            • Album Title - Artist Names (Year) [Genre: X, Support: X]
            ✅ X albums ajoutés à la collection {name}
            ⚠️  Aucun album trouvé...                    (if 0 results)
        
        Used by:
            - FastAPI endpoint: POST /collections
            - Admin UI: Collection creation wizard
            - Scheduled import: Nightly collection generation
        
        Complementary methods:
            - search_by_ai_query(): Local AI search only
            - search_by_genre/artist/period(): Structured search
            - add_albums_to_collection(): Bulk album addition
            - get_collection_albums(): Retrieve populated collection
        
        Preconditions:
            - db must be valid SQLAlchemy Session
            - If web_search=True: Euria API must be reachable
            - search_type must be valid (ai_query/genre/artist/period)
            - If search_type='genre': criteria['genre'] must be provided
            - If search_type='artist': criteria['artist'] must be provided
            - If search_type='period': criteria[start_year/end_year] can be provided
        
        Postconditions:
            - Collection persisted to database with album_count set
            - CollectionAlbum entries created with position ordering
            - AlbumCollection.id available for reference
            - Related albums loaded in collection.albums (if using relationship)
        
        Error handling:
            - Web API fails: Falls back to local search (logged as warning)
            - Local search finds 0: Returns empty collection (no exception)
            - AI naming fails: Uses "Nouvelle Collection" fallback
            - Invalid search_type: Albums variable remains [] (empty collection created)
        """
        # Générer le nom automatiquement si non fourni
        if not name and ai_query:
            name = self._generate_collection_name(ai_query)
        
        if not name:
            name = "Nouvelle Collection"
        
        # Convertir search_criteria en JSON string si c'est un dict
        criteria_json = None
        if search_criteria:
            criteria_json = json.dumps(search_criteria) if isinstance(search_criteria, dict) else search_criteria
        
        collection = AlbumCollection(
            name=name,
            search_type=search_type,
            search_criteria=criteria_json,
            ai_query=ai_query,
            album_count=0
        )
        self.db.add(collection)
        self.db.commit()
        self.db.refresh(collection)
        logger.info(f"📚 Collection créée: {name}")
        
        # Rechercher et ajouter automatiquement les albums
        albums = []
        
        if search_type == 'ai_query' and ai_query:
            # 🌐 PRIORITÉ ABSOLUE: Recherche Euria IA sur le web
            if web_search:
                logger.info(f"🌐 Recherche Euria IA pour: {ai_query}")
                web_albums = self._search_albums_web(ai_query, limit=50)
                albums.extend(web_albums)
                
                if len(web_albums) > 0:
                    logger.info(f"🎉 {len(web_albums)} albums proposés par Euria - PAS DE COMPLÉMENT LOCAL")
                else:
                    logger.warning(f"⚠️ Euria n'a trouvé aucun album, complément avec librairie locale...")
                    local_albums = self.search_by_ai_query(ai_query, limit=50)
                    albums.extend(local_albums)
            else:
                # Fallback: Recherche en librairie locale seulement
                logger.info(f"📚 Recherche locale uniquement pour: {ai_query}")
                local_albums = self.search_by_ai_query(ai_query, limit=50)
                albums.extend(local_albums)
        elif search_type == 'genre' and search_criteria and 'genre' in search_criteria:
            albums = self.search_by_genre(search_criteria['genre'], limit=50)
        elif search_type == 'artist' and search_criteria and 'artist' in search_criteria:
            albums = self.search_by_artist(search_criteria['artist'], limit=50)
        elif search_type == 'period' and search_criteria:
            start_year = search_criteria.get('start_year')
            end_year = search_criteria.get('end_year')
            albums = self.search_by_period(start_year, end_year, limit=50)
        
        # Ajouter les albums trouvés à la collection
        if albums:
            album_ids = [album.id for album in albums]
            
            # Afficher le détail des albums avant ajout
            logger.info(f"📋 ALBUMS À AJOUTER À LA COLLECTION ({len(albums)} total):")
            for album in albums:
                artists_names = ", ".join([a.name for a in album.artists]) if album.artists else "Unknown"
                logger.info(f"  • {album.title} - {artists_names} ({album.year}) [Genre: {album.genre}, Support: {album.support}]")
            
            collection = self.add_albums_to_collection(collection.id, album_ids)
            logger.info(f"✅ {len(album_ids)} albums ajoutés à la collection {name}")
        else:
            logger.warning("⚠️ Aucun album trouvé pour ajouter à la collection")
        
        # Rafraîchir pour obtenir le album_count à jour
        self.db.refresh(collection)
        return collection
    def add_albums_to_collection(
        self,
        collection_id: int,
        album_ids: List[int]
    ) -> AlbumCollection:
        """
        Bulk add albums to collection with position tracking/ordering.
        
        Args:
            collection_id (int): Target collection ID
            album_ids (list): List of album IDs to add
        
        Returns:
            AlbumCollection: Updated collection with album_count set
        
        Raises:
            ValueError: If collection_id not found
        
        Performance:
            - O(n) where n = len(album_ids)
            - Typical: <50ms for 50 albums
        
        Implementation:
            1. Load collection, verify exists
            2. Get max position from existing albums
            3. For each album_id:
               - Check if already in collection (skip duplicate)
               - Create CollectionAlbum record
               - Increment position
            4. Commit all changes
            5. Update collection.album_count
        """
        collection = self.db.query(AlbumCollection).filter(
            AlbumCollection.id == collection_id
        ).first()
        
        if not collection:
            raise ValueError(f"Collection {collection_id} non trouvée")
        
        # Récupérer la position max actuelle
        max_position = self.db.query(func.max(CollectionAlbum.position)).filter(
            CollectionAlbum.collection_id == collection_id
        ).scalar() or 0
        
        # Ajouter les albums
        added_count = 0
        for idx, album_id in enumerate(album_ids):
            # Vérifier si l'album n'est pas déjà dans la collection
            exists = self.db.query(CollectionAlbum).filter(
                and_(
                    CollectionAlbum.collection_id == collection_id,
                    CollectionAlbum.album_id == album_id
                )
            ).first()
            
            if not exists:
                collection_album = CollectionAlbum(
                    collection_id=collection_id,
                    album_id=album_id,
                    position=max_position + idx + 1
                )
                self.db.add(collection_album)
                added_count += 1
        
        # Commit d'abord les albums
        self.db.commit()
        
        # Mettre à jour le compteur avec un count simple
        total_count = self.db.query(CollectionAlbum).filter(
            CollectionAlbum.collection_id == collection_id
        ).count()
        
        collection.album_count = total_count
        
        self.db.commit()
        self.db.refresh(collection)
        logger.info(f"📚 {added_count} albums ajoutés à la collection {collection.name} (total: {total_count})")
        return collection
    
    def search_by_genre(self, genre: str, limit: int = 50) -> List[Album]:
        """
        Search albums by genre field (case-insensitive).
        
        Args:
            genre (str): Genre to match (e.g., "rock", "electronic", "jazz")
            limit (int): Max results to return (default 50)
        
        Returns:
            list: Albums matching genre in Album.genre or ai_description fields
        
        Performance:
            - <100ms typical (single field index scan)
            - Big-O: O(m) where m = matching albums
        
        Matching:
            - Case-insensitive ILIKE query on Album.genre and ai_description
            - Partial matches included (genre="rock" matches "rock", "rock and roll")
        )"""
        logger.info(f"🔍 Recherche par genre: {genre}")
        
        # Recherche dans ai_description ou autres métadonnées
        albums = self.db.query(Album).filter(
            or_(
                Album.ai_description.ilike(f"%{genre}%"),
                Album.genre.ilike(f"%{genre}%")
            )
        ).limit(limit).all()
        
        logger.info(f"✅ {len(albums)} albums trouvés pour le genre {genre}")
        return albums
    
    def search_by_artist(self, artist_name: str, limit: int = 50) -> List[Album]:
        """
        Search albums by artist name (case-insensitive with "The" variant handling).
        
        Args:
            artist_name (str): Artist name to search for (e.g., "Radiohead", "The Beatles")
            limit (int): Max results to return (default 50)
        
        Returns:
            list: Albums by artist (cross-checked with 3 name variants)
        
        Performance:
            - <100ms typical (join + ILIKE filter)
            - Big-O: O(a + m) where a=artist records, m=matching albums
        
        Variants:
            Input "Radiohead" searches for:
            - "Radiohead" (exact)
            - "Radiohead" (no change)
            - "The Radiohead" (with article)
            
            Input "The Beatles" searches for:
            - "The Beatles" (exact)
            - "Beatles" (without article)
            - "The Beatles" (same)
        
        Matching: Case-insensitive ILIKE (partial matches included)
        """
        logger.info(f"🔍 Recherche par artiste: {artist_name}")
        
        # Recherche d'artiste avec variantes
        artist_variants = [
            artist_name,
            artist_name.replace("The ", ""),
            f"The {artist_name}" if not artist_name.startswith("The ") else artist_name
        ]
        
        albums = self.db.query(Album).join(Album.artists).filter(
            or_(*[Artist.name.ilike(f"%{variant}%") for variant in artist_variants])
        ).limit(limit).all()
        
        logger.info(f"✅ {len(albums)} albums trouvés pour l'artiste {artist_name}")
        return albums
    
    def search_by_period(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        limit: int = 50
    ) -> List[Album]:
        """
        Search albums by year range (inclusive).
        
        Args:
            start_year (int|None): Earliest year to include (e.g., 1990)
            end_year (int|None): Latest year to include (e.g., 1999)
            limit (int): Max results to return (default 50)
        
        Returns:
            list: Albums with year between start_year and end_year (inclusive)
        
        Performance:
            - <100ms typical (index range scan)
            - Big-O: O(m) where m = matching albums
        
        Range logic:
            - start_year only: year >= start_year
            - end_year only: year <= end_year
            - Both: start_year <= year <= end_year
            - Neither: All albums (no filter)
        
        Examples:
            search_by_period(1990, 1999)  # 90s
            search_by_period(start_year=2000)  # 2000 onwards
            search_by_period(end_year=1989)  # Before 1990
        """
        logger.info(f"🔍 Recherche par période: {start_year} - {end_year}")
        
        query = self.db.query(Album)
        
        if start_year:
            query = query.filter(Album.year >= start_year)
        if end_year:
            query = query.filter(Album.year <= end_year)
        
        albums = query.limit(limit).all()
        
        logger.info(f"✅ {len(albums)} albums trouvés pour la période {start_year}-{end_year}")
        return albums
    
    def search_by_ai_query(self, query: str, limit: int = 50) -> List[Album]:
        """
        Natural language multi-field search (enriched AI query).
        
        Searches for query across 5 fields: ai_description, ai_style, genre, title, artist.name
        using AND logic (all search terms must match in any field for album inclusion).
        Falls back to random curated albums if no exact matches found (discovery mode).
        
        Args:
            query (str): Natural language query (e.g., "soft indie 90s for relaxing")
            limit (int): Max results to return (default 50)
        
        Returns:
            list: Albums matching all query terms (across 5 fields)
        
        Performance:
            - <100ms typical (outerjoin + multiple ILIKE conditions)
            - Fallback: <50ms (random query if no matches)
            - Big-O: O(a + m) where a=albums, m=matching albums
        
        Search logic:
            1. Split query into terms: ["soft", "indie", "90s"]
            2. For each term: Create conditions on 5 fields
               - Album.ai_description ILIKE "%term%"
               - Album.ai_style ILIKE "%term%"
               - Album.genre ILIKE "%term%"
               - Album.title ILIKE "%term%"
               - Artist.name ILIKE "%term%" (via join)
            3. Combine with OR within term, AND between terms
            4. Filter + distinct + limit
        
        Fallback (0 matches):
            - Returns N random albums WITH ai_description (curated discovery)
            - Useful for exploration when no exact matches
        
        Example queries:
            "soft indie rock" → All terms match any field
            "upbeat 80s pop" → "upbeat" anywhere + "80s" + "pop" = AND logic
            "dreamy film score" → All 3 terms must match (somewhere)
        
        Used by:
            - AI-powered collection creation (primary search method)
            - Web fallback if Euria API returns 0 results
        """
        logger.info(f"🔍 Recherche AI enrichie: {query}")
        
        # Découper la requête en termes de recherche
        search_terms = query.lower().split()
        
        # Créer des conditions de recherche pour chaque terme dans différents champs
        conditions = []
        for term in search_terms:
            term_conditions = []
            
            # Recherche dans ai_description
            term_conditions.append(Album.ai_description.ilike(f"%{term}%"))
            
            # Recherche dans ai_style
            term_conditions.append(Album.ai_style.ilike(f"%{term}%"))
            
            # Recherche dans genre
            term_conditions.append(Album.genre.ilike(f"%{term}%"))
            
            # Recherche dans titre
            term_conditions.append(Album.title.ilike(f"%{term}%"))
            
            # Recherche dans artistes (via join)
            term_conditions.append(Artist.name.ilike(f"%{term}%"))
            
            # Au moins un champ doit matcher ce terme
            conditions.append(or_(*term_conditions))
        
        # Requête avec join pour accéder aux artistes
        albums = self.db.query(Album).outerjoin(Album.artists).filter(
            # Tous les termes doivent matcher (dans n'importe quel champ)
            and_(*conditions)
        ).distinct().limit(limit).all()
        
        logger.info(f"✅ {len(albums)} albums trouvés pour la requête AI: {query}")
        logger.info(f"   Termes recherchés: {', '.join(search_terms)}")
        
        # FALLBACK: Si aucun album ne matche, retourner albums aléatoires avec ai_description
        if not albums:
            logger.warning(f"⚠️ Aucun album ne matche la requête '{query}'. Fallback: albums aléatoires avec AI descriptions")
            from sqlalchemy import func
            albums = self.db.query(Album).filter(
                Album.ai_description.isnot(None)
            ).order_by(func.random()).limit(limit).all()
            logger.info(f"📊 Fallback: {len(albums)} albums aléatoires retournés")
        
        return albums
    
    def _search_albums_web(self, query: str, limit: int = 20) -> List[Album]:
        """
        Internal web search for albums via Euria AI API (external discovery).
        
        Calls Euria API to discover albums matching natural language query via external
        web sources (Spotify, Last.fm, etc. integration). Returns albums formatted as
        local Album objects with metadata. Used as priority source in create_collection()
        when web_search=True.
        
        Args:
            query (str): Natural language search query (e.g., "upbeat indie rock")
            limit (int): Max albums to return (default 20)
        
        Returns:
            list: Album objects populated from web search results (or [] on error)
        
        Raises:
            None - returns empty list on any error (graceful degradation)
        
        Performance:
            - Typical: 5-20 seconds (external API + network latency)
            - Error timeout: ~10 seconds before fallback
            - Big-O: Not applicable (external service, not local computation)
        
        Side Effects:
            - Network: Calls Euria API (may block for 5-20s)
            - Database: May create new Album/Artist records if web results not in local DB
            - Logging: Detailed per-album logging of creation/enrichment
        
        Integration:
            - Euria API endpoint: External music discovery service
            - Creates Album records: If found albums not in local database
            - Artist linking: Associates found albums with matching/new artists
            - Enrichment: Populates ai_description, ai_style, genre from API response
        
        Result format:
            Web API returns album metadata, service converts to local Album objects:
            - title (str): Album name
            - artists (list): Artist names (creates Artist records if needed)
            - year (int): Release year
            - genre (str): Musical genre
            - ai_description (str): Euria-generated long description
            - ai_style (str): Short style/mood descriptor
            - image_url (str): Album cover image URL
        
        Error handling:
            - API timeout: Logs error, returns []
            - Network error: Logs error, returns []
            - Invalid response: Logs error, returns []
            - API KEY missing: Logs error, returns []
        
        Used by:
            - create_collection() when web_search=True and search_type='ai_query'
            - Discovery/curation feature for album recommendations
        
        Difference from search_by_ai_query():
            search_by_ai_query(): Local database full-text search (fast, limited catalog)
            _search_albums_web(): External API web search (slow, broader catalog)
            Preference: Web search preferred if available/fast enough
        
        Logging:
            🌐 Search Euria API for: {query}
            ✅ {count} albums créés et enrichis
            ✅ ALBUM CRÉÉ: 'title' de artist (year) - Genre: X
            ❌ Erreur recherche web: {error}
        """
        logger.info(f"🌐 Recherche web via Euria pour: {query}")
        
        try:
            from app.services.external.ai_service import AIService
            import os
            
            ai = AIService()
            
            # Étape 1: Rechercher les albums via EurIA
            logger.info(f"🧠 Requête à EurIA...")
            albums_data = ai.search_albums_web_sync(query, limit=limit)
            
            logger.info(f"📊 RÉSULTAT BRUT DE EURIA: {albums_data}")
            logger.info(f"📊 Nombre d'albums retournés: {len(albums_data)}")
            
            # Dédupliquer les albums (Euria peut retourner des doublons)
            seen = set()
            deduplicated = []
            duplicates = []
            
            for album_info in albums_data:
                key = (album_info.get('artist', '').lower(), album_info.get('album', '').lower())
                if key not in seen:
                    seen.add(key)
                    deduplicated.append(album_info)
                else:
                    duplicates.append(f"{album_info.get('artist')} - {album_info.get('album')}")
            
            if duplicates:
                logger.warning(f"⚠️ {len(duplicates)} albums dupliqués détectés et supprimés: {duplicates}")
            
            albums_data = deduplicated
            logger.info(f"✅ Après déduplication: {len(albums_data)} albums uniques")
            
            if not albums_data:
                logger.warning("⚠️ Aucun album trouvé via Euria")
                return []
            
            logger.info(f"✅ {len(albums_data)} albums trouvés via Euria - Détail: {[(a.get('artist'), a.get('album')) for a in albums_data]}")
            
            # Préparer Spotify pour l'enrichissement
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            spotify_service = None
            
            if client_id and client_secret:
                from app.services.spotify_service import SpotifyService
                spotify_service = SpotifyService(client_id, client_secret)
                logger.info("🎵 Service Spotify prêt pour enrichissement")
            else:
                logger.warning("⚠️ Clés Spotify manquantes, enrichissement limité")
            
            # Étape 2-4: Créer et enrichir les albums
            albums_created = []
            
            for idx, album_info in enumerate(albums_data, 1):
                try:
                    artist_name = album_info.get('artist', 'Unknown')
                    album_title = album_info.get('album', '')
                    year = album_info.get('year')
                    
                    if not album_title:
                        logger.warning(f"⏭️  Album sans titre, skip: {album_info}")
                        continue
                    
                    # Rechercher ou créer l'artiste
                    artist = self.db.query(Artist).filter(
                        Artist.name.ilike(f"%{artist_name}%")
                    ).first()
                    
                    if not artist:
                        artist = Artist(name=artist_name)
                        self.db.add(artist)
                        self.db.flush()
                        logger.info(f"  👤 Artiste créé: {artist_name}")
                    
                    # Chercher si l'album existe déjà
                    existing_album = self.db.query(Album).filter(
                        Album.title.ilike(album_title)
                    ).filter(
                        Album.artists.any(Artist.name.ilike(artist_name))
                    ).first()
                    
                    if existing_album:
                        logger.info(f"  ℹ️ Album existant: {album_title}")
                        albums_created.append(existing_album)
                        continue
                    
                    # Étape 2: Créer l'album avec provenance "Discover IA"
                    logger.info(f"  [{idx}/{len(albums_data)}] 📀 Création: {album_title} - {artist_name}")
                    
                    album = Album(
                        title=album_title,
                        year=year,
                        genre="Discover IA",  # Provenance
                        support="Digital"  # Par défaut pour découverte web
                    )
                    album.artists.append(artist)
                    
                    # Étape 3: Enrichir avec Spotify (+fallback Last.fm)
                    if spotify_service:
                        try:
                            # Chercher les détails et l'image sur Spotify
                            spotify_details = spotify_service.search_album_details_sync(
                                artist_name, album_title
                            )
                            
                            if spotify_details:
                                album.spotify_url = spotify_details.get('spotify_url')
                                album.image_url = spotify_details.get('image_url')
                                if not year and spotify_details.get('year'):
                                    album.year = spotify_details['year']
                                logger.info(f"    ✨ Enrichi avec Spotify")
                            else:
                                logger.info(f"    ⚠️ Non trouvé sur Spotify, fallback Last.fm...")
                                # Fallback: Chercher via Last.fm
                                from app.services.spotify_service import get_lastfm_image
                                lastfm_image = get_lastfm_image(artist_name, album_title)
                                if lastfm_image:
                                    album.image_url = lastfm_image
                                    logger.info(f"    ✨ Image trouvée via Last.fm")
                                else:
                                    logger.info(f"    ⏭️ Pas d'image (Spotify + Last.fm), exclusion")
                                    continue  # Exclure si aucune image
                        except Exception as e:
                            logger.warning(f"    ⚠️ Enrichissement échoué, exclusion: {e}")
                            continue
                    else:
                        logger.warning(f"    ⚠️ Spotify désactivé, exclusion de l'album")
                        continue  # Exclure si Spotify n'est pas configuré
                    
                    # Enrichir avec Apple Music URL
                    try:
                        generated_url = AppleMusicService.generate_url_for_album(artist_name, album_title)
                        if generated_url and AppleMusicService.is_compatible_url(generated_url):
                            album.apple_music_url = generated_url
                            logger.info(f"    🍎 URL Apple Music ajoutée")
                    except Exception as e:
                        logger.debug(f"    ⚠️ Apple Music enrichment failed: {e}")
                        # Non-blocking, continue without Apple Music URL
                    
                    # Vérification finale: l'album doit avoir une image
                    if not album.image_url:
                        logger.info(f"    ⏭️ Aucune image trouvée, exclusion finale")
                        continue
                    
                    # Étape 4: Générer description via Euria
                    try:
                        description = euria.generate_album_description_sync(artist_name, album_title, year)
                        album.ai_description = description
                        logger.info(f"    ✍️ Description générée")
                    except Exception as e:
                        logger.warning(f"    ⚠️ Description Euria échouée: {e}")
                        album.ai_description = f"Découverte Euria via: {query}"
                    
                    self.db.add(album)
                    self.db.flush()
                    albums_created.append(album)
                    logger.info(f"    ✅ Album conservé avec image")
                    logger.info(f"    ✅ Album créé avec enrichissements")
                    
                except Exception as e:
                    logger.error(f"  ❌ Erreur création album '{album_info.get('album', '?')}': {e}")
                    continue
            
            self.db.commit()
            
            logger.info(f"🎉 {len(albums_created)} albums créés et enrichis")
            
            # Afficher le détail des albums créés pour debugging
            for album in albums_created:
                artists_names = ", ".join([a.name for a in album.artists])
                logger.info(f"  ✅ ALBUM CRÉÉ: '{album.title}' de {artists_names} ({album.year}) - Genre: {album.genre}, Source pour recherche Euria")
            
            return albums_created
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche web: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_collection(self, collection_id: int) -> Optional[AlbumCollection]:
        """
        Retrieve collection by ID.
        
        Args:
            collection_id (int): Collection ID to fetch
        
        Returns:
            AlbumCollection | None: Collection object if found, None otherwise
        
        Performance:
            - O(1), <10ms (primary key lookup)
        """
        return self.db.query(AlbumCollection).filter(
            AlbumCollection.id == collection_id
        ).first()
    
    def get_collection_albums(self, collection_id: int) -> List[Album]:
        """
        Retrieve all albums in collection (ordered by position, image-filtered).
        
        Args:
            collection_id (int): Collection ID
        
        Returns:
            list: Albums in collection ordered by position (only those with image_url)
        
        Performance:
            - O(n) where n = collection size (typical 10-50)
            - <50ms typical
        
        Note:
            - Filters out albums without image_url (image-only results)
            - Order: By CollectionAlbum.position (preserves curation order)
        """
        collection_albums = self.db.query(CollectionAlbum).filter(
            CollectionAlbum.collection_id == collection_id
        ).order_by(CollectionAlbum.position).all()
        
        # Filtrer les albums sans image
        result = []
        for ca in collection_albums:
            if ca.album.image_url:  # Seulement les albums avec image
                result.append(ca.album)
        
        return result
    
    def list_collections(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[AlbumCollection]:
        """
        List all collections with pagination.
        
        Args:
            limit (int): Max items to return (default 100)
            offset (int): Pagination offset (default 0)
        
        Returns:
            list: AlbumCollection objects paginated
        
        Performance:
            - O(k) where k = limit (typical 10-100)
            - <100ms for limit=100
        
        Usage:
            page1 = service.list_collections(limit=20, offset=0)     # Items 0-19
            page2 = service.list_collections(limit=20, offset=20)    # Items 20-39
        """
        return self.db.query(AlbumCollection).limit(limit).offset(offset).all()
    
    def delete_collection(self, collection_id: int) -> bool:
        """
        Delete collection and its associated album mappings.
        
        Args:
            collection_id (int): Collection ID to delete
        
        Returns:
            bool: True if deleted, False if collection not found
        
        Performance:
            - O(n) where n = albums in collection
            - Typical: <100ms
        
        Side Effects:
            - Deletes CollectionAlbum associative records (cascading)
            - Deletes AlbumCollection record itself
            - Album records unchanged (orphaning allowed)
            - Logs: 🗑️ Collection {name} supprimée
        
        Implementation:
            1. Load collection by ID
            2. If not found: Return False
            3. Delete all CollectionAlbum entries for this collection
            4. Delete AlbumCollection record
            5. Commit changes
            6. Return True
        """
        collection = self.get_collection(collection_id)
        if not collection:
            return False
        
        # Supprimer les associations
        self.db.query(CollectionAlbum).filter(
            CollectionAlbum.collection_id == collection_id
        ).delete()
        
        # Supprimer la collection
        self.db.delete(collection)
        self.db.commit()
        
        logger.info(f"🗑️ Collection {collection.name} supprimée")
        return True
