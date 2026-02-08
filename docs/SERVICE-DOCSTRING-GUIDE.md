# SERVICE LAYER DOCUMENTATION GUIDE - PHASE 5

**Objective**: Add comprehensive docstrings to 80-100 service methods ensuring Args/Returns/Raises consistency

**Total Methods Found**: 150+  
**Target Coverage**: 80-100  
**Priority Order**: By service importance and usage frequency

## Services by Priority

### P1 - Critical Core Services (30-40 methods)
These are used in nearly every workflow and must have excellent documentation.

**AlbumService** (7 methods, `backend/app/services/collection/album_service.py`)
- [ ] list_albums() - Enhanced pagination/filtering docs
- [ ] get_album() - Detail retrieval with relationships
- [ ] create_album() - Batch import documentation
- [ ] update_album() - Field-level update documentation
- [ ] patch_album() - Partial update documentation
- [ ] delete_album() - Cascade behavior documentation
- [ ] _format_album_list() - Internal formatting helper

**ArtistService** (3 methods, `backend/app/services/collection/artist_service.py`)
- [ ] list_artists() - With image relationship
- [ ] get_artist_image() - Multi-service fallback
- [ ] get_artist_album_count() - Counting logic

**ExportService** (8 methods, `backend/app/services/collection/export_service.py`)
- [ ] export_markdown_full()
- [ ] export_markdown_artist()
- [ ] export_markdown_support()
- [ ] export_json_full()
- [ ] export_json_support()
- [ ] generate_presentation_markdown()
- [ ] _format_album_json() - Helper

**PlaylistService** (15 methods, `backend/app/services/playback/playlist_service.py`)
- [ ] create_playlist()
- [ ] list_playlists()
- [ ] get_playlist()
- [ ] get_playlist_tracks()
- [ ] add_track()
- [ ] remove_track()
- [ ] delete_playlist()
- [ ] export_playlist()
- [ ] generate_playlist() - Complex AI algo
- [ ] _generate_top_sessions()
- [ ] _generate_artist_correlations()
- [ ] _generate_artist_flow()
- [ ] _generate_time_based()
- [ ] _generate_complete_albums()
- [ ] _generate_rediscovery()

### P2 - External Integration Services (25-35 methods)
These handle critical external APIs and need clear contract documentation.

**SpotifyService** (8 methods, `backend/app/services/spotify_service.py`)
- [ ] __init__()
- [ ] _get_access_token() - Improved
- [ ] search_artist_image() - Improved
- [ ] search_album_image() - Improved with fallback
- [ ] search_album_url()
- [ ] search_album_details()
- [ ] get_artist_spotify_id()
- [ ] search_album_details_sync()

**DiscogsService** - Already done in earlier work ✅

**AIService** (10 methods, `backend/app/services/external/ai_service.py`)
- [ ] __init__()
- [ ] _load_config()
- [ ] ask_for_ia()
- [ ] ask_for_ia_stream()  
- [ ] search_albums_web()
- [ ] generate_album_description()
- [ ] generate_collection_name()
- [ ] generate_album_info()
- [ ] generate_haiku()
- [ ] generate_playlist_by_prompt()

**TrackerService** (7 methods, `backend/app/services/tracker_service.py`)
- [ ] start()
- [ ] stop()
- [ ] get_status()
- [ ] _poll_lastfm()
- [ ] _check_duplicate()
- [ ] _save_track()

**RoonTrackerService** (6 methods, `backend/app/services/roon_tracker_service.py`)
- [ ] start()
- [ ] stop()
- [ ] get_status()
- [ ] _poll_roon()
- [ ] _check_duplicate()
- [ ] _save_track()

### P3 - Content Generation Services (15-20 methods)
These generate complex content and need algorithmic documentation.

**MagazineGeneratorService** (12 methods, `backend/app/services/magazine_generator_service.py`)
- [ ] __init__()
- [ ] _generate_ai_haiku()
- [ ] _clean_markdown_text()
- [ ] _ensure_markdown_format()
- [ ] generate_magazine()
- [ ] _manage_background_tasks_workflow()
- [ ] _refresh_albums_in_background()
- [ ] _enrich_albums_in_background()
- [ ] get_refresh_status()
- [ ] _generate_layout_suggestion()

**ContentServices**
- HaikuService (2 methods)
- ArticleService (2 methods)
- AnalysisService (4 methods)
- DescriptionService (3 methods)

### P4 - Utility & Helper Services (10-15 methods)
These provide supporting functionality.

**DialogServices** (dialog/)
- ErrorDialog (6 functions)
- SuccessDialog (6 functions)  
- StreamingDialog (6 + builder class)

**HealthMonitor** (5 methods)
- check_database_health()
- check_database_health_sync()
- validate_startup()
- get_status()
- record_request()

**MarkdownExportService** (4 methods)
- get_collection_markdown()
- get_artist_markdown()
- get_support_markdown()

**RoonService** (15 methods)
- get_zones()
- play_album()
- play_track()
- queue_tracks()
- etc.

## Documentation Standards

### Function Signature
```python
def method_name(param1: Type, param2: Type) -> ReturnType:
```

### Docstring Template
```python
def method_name(db: Session, album_id: int) -> AlbumDetail:
    """
    One-line summary of what the method does.
    
    Extended description with context about:
    - Business logic
    - Use cases
    - Side effects
    - Performance considerations
    
    Args:
        param1: Description of parameter
        param2: Type, constraints, valid values
        
    Returns:
        Type and description of return value
        Can be multiple lines describing structure
        
    Raises:
        ExceptionType: When this error occurs
        AnotherException: Specific condition
        
    Examples:
        >>> album = get_album(db, 123)
        >>> print(album.title)
        'The Wall'
        
    Notes:
        - Performance: O(n) where n = number of artists
        - Cached for 1 hour
        - May throw timeout if service unavailable
    """
```

### Key Sections
1. **Summary**: One-line description
2. **Extended Description**: Why/when/how
3. **Args**: Parameter types, constraints, defaults
4. **Returns**: Type, structure, None behavior
5. **Raises**: All possible exceptions
6. **Examples**: Real usage patterns
7. **Notes**: Performance, side effects, caching

## Implementation Strategy

### Phase 1: Core Services (P1) - 40 methods
- **Target**: 2 hours  
- **Services**: Album, Artist, Export, Playlist
- **Approach**: Add comprehensive Args/Returns/Raises to all public methods

### Phase 2: Integration Services (P2) - 35 methods
- **Target**: 2.5 hours
- **Services**: Spotify, AI, Tracker, RoonTracker  
- **Approach**: Focus on error conditions and fallback strategies

### Phase 3: Content Services (P3) - 20 methods
- **Target**: 1.5 hours
- **Services**: Magazine, Content, Description
- **Approach**: Document algorithms and AI integration

### Phase 4: Utility Services (P4) - 15+ methods
- **Target**: 1 hour
- **Services**: Dialog, Health, Markdown, Roon
- **Approach**: Quick wins on small utility functions

**Total Estimated Time**: 7 hours for comprehensive 80-100 docstrings

## Progress Tracking

- [ ] Phase 1 (Core): 0/40
- [ ] Phase 2 (Integration): 0/35
- [ ] Phase 3 (Content): 0/20
- [ ] Phase 4 (Utility): 0/15+
- [ ] **Total**: 0/80+

---

**Created**: 2026-02-07  
**Status**: Planning Complete, Ready for Execution
