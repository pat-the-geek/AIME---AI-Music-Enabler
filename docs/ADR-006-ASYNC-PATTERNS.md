# ADR-006: Async/Await Patterns & Concurrency

**Status**: ✅ Accepted  
**Date**: 2026-02-07  
**Priority**: High  
**Author**: Engineering Team  
**Reviewers**: Architecture Committee  

## 1. Context

AIME is built on **FastAPI**, which is fundamentally asynchronous:
- HTTP requests are handled by async route handlers
- Multiple concurrent requests don't block each other
- External API calls (Spotify, Discogs) are I/O-bound operations
- Background jobs run concurrently with request handling

### 1.1 Concurrency Challenges

1. **Mixed Sync/Async Code**
   - Database queries: SQLAlchemy is synchronous by default
   - External APIs: Requests library is synchronous
   - Services: Mix of sync and async methods

2. **Resource Contention**
   - Rate limiting: Multiple requests hitting same API rate limit
   - Database connections: Limited pool of 5-10 connections
   - Memory: Large album imports across multiple concurrent requests

3. **Error Handling in Async**
   - Task cancellation when request times out
   - Exception propagation from async subtasks
   - Deadlock risk in lock-based synchronization

4. **Testing Complexity**
   - Async test fixtures must be properly scoped
   - Mocking async functions different from sync
   - Race conditions hard to reproduce reliably

**Problem**: How to structure FastAPI applications, manage concurrency, coordinate background tasks, and test async code while maintaining readability and preventing common pitfalls?

## 2. Decision

We adopt **async-first architecture with strategic sync bridges** and **explicit concurrency control**.

### 2.1 Request Handler Pattern (FastAPI Routes)

**Rule: All HTTP handlers must be async**

```python
# Pattern: backend/app/api/v1/collection.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import asyncio

router = APIRouter(prefix="/api/v1/collection", tags=["collection"])

@router.get("/albums")
async def list_albums(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    user_id: int = Depends(get_current_user_id)
) -> List[AlbumResponse]:
    """
    List user's albums with pagination.
    
    Args:
        skip: Number of albums to skip
        limit: Maximum albums to return (capped at 100)
        session: Async database session
        user_id: Current authenticated user ID
        
    Returns:
        List[AlbumResponse]: Paginated album list
        
    Raises:
        HTTPException: 401 if not authenticated
    """
    # Step 1: Query database (async)
    query = select(Album).where(Album.user_id == user_id)
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    albums = result.scalars().all()
    
    # Step 2: Enrich with AI descriptions (parallel async calls)
    enriched = await asyncio.gather(
        *[_enrich_album(album, session) for album in albums],
        return_exceptions=False
    )
    
    # Step 3: Transform to response schema
    return [AlbumResponse.from_orm(a) for a in enriched]

async def _enrich_album(album: Album, session: AsyncSession) -> Album:
    """Enrich single album with AI description asynchronously."""
    description = await AIService().generate_description(album.title)
    album.ai_description = description
    return album
```

### 2.2 Service Layer Pattern (Mixed Sync/Async)

**Rule: Async-capable services use `run_in_executor` for sync calls**

```python
# Pattern: backend/app/services/album_service.py

import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session

class AlbumService:
    """Album management with async rate limiting."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    # ✅ Async method for API routes
    async def list_albums_async(
        self,
        user_id: int,
        session: AsyncSession,
        limit: int = 100
    ) -> List[AlbumResponse]:
        """
        List albums asynchronously.
        
        Bridges async FastAPI route with async database operations.
        """
        query = select(Album).where(Album.user_id == user_id).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()
    
    # ✅ Sync method for background jobs (no await needed)
    def import_from_spotify(
        self,
        user_id: int,
        spotify_tracks: List[Dict[str, Any]],
        session: Session  # Sync session
    ) -> int:
        """
        Import albums from Spotify (sync version for background jobs).
        
        Args:
            user_id: User importing albums
            spotify_tracks: Tracks from Spotify API
            session: Synchronous database session
            
        Returns:
            Number of albums created/updated
        """
        count = 0
        for track in spotify_tracks:
            album = self._get_or_create_album(
                track["album"]["external_ids"]["spotify"],
                track["album"]["name"],
                user_id,
                session
            )
            count += 1
        session.commit()
        return count
    
    # ✅ Async wrapper for background job invocation
    async def import_from_spotify_async(
        self,
        user_id: int,
        spotify_tracks: List[Dict[str, Any]],
        session: AsyncSession
    ) -> int:
        """
        Async wrapper that runs sync import in thread pool.
        
        Prevents blocking the event loop during I/O-heavy sync operations.
        """
        loop = asyncio.get_event_loop()
        
        # Run sync operation in thread pool
        return await loop.run_in_executor(
            self.executor,
            self.import_from_spotify,
            user_id,
            spotify_tracks,
            session  # ⚠️ Note: AsyncSession can't be passed to sync context
        )
```

### 2.3 Background Task Pattern (Celery Alternative)

**Use `asyncio.create_task()` for fire-and-forget operations**

```python
# Pattern: Long-running operations without waiting

@router.post("/albums/import")
async def import_albums(
    import_request: ImportRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
) -> {"status": "queued", "task_id": str}:
    """
    Queue album import and return immediately.
    
    Long operation (30-60s) runs in background without blocking response.
    """
    # Create background task without waiting
    task = asyncio.create_task(
        _import_albums_background(
            user_id=user_id,
            import_type=import_request.type,
            session=session
        )
    )
    
    # Store task ID for later polling
    task_registry[task.id] = task
    
    return {"status": "queued", "task_id": str(task.id)}

async def _import_albums_background(
    user_id: int,
    import_type: str,
    session: AsyncSession
) -> None:
    """
    Background task: Import albums from external service.
    
    Runs concurrently with request handling. Any exceptions logged
    and not propagated to client (already responded).
    """
    try:
        if import_type == "spotify":
            await import_from_spotify(user_id, session)
        elif import_type == "discogs":
            await import_from_discogs(user_id, session)
        
        # Update completion status
        job = await get_import_job(user_id, session)
        job.status = "completed"
        await session.commit()
    except Exception as e:
        logger.error(f"Background import failed: {e}", exc_info=True)
        job = await get_import_job(user_id, session)
        job.status = "failed"
        job.error = str(e)
        await session.commit()
```

### 2.4 Concurrency Control (Rate Limiting, Locks)

**Pattern: Semaphores for resource limits**

```python
# Pattern: backend/app/core/concurrency.py

import asyncio
from typing import Optional

class ConcurrencyManager:
    """Manage concurrent resource access."""
    
    def __init__(self):
        # Limit to 10 concurrent import operations
        self.import_semaphore = asyncio.Semaphore(10)
        
        # Per-service rate limiting
        self.spotify_semaphore = asyncio.Semaphore(1)  # Serialize Spotify calls
        self.discogs_semaphore = asyncio.Semaphore(5)  # Allow 5 concurrent Discogs
        
        # Database connection limit (enforced by SQLAlchemy pool)
        # but we add application-level limit for safety
        self.db_semaphore = asyncio.Semaphore(8)  # Max 8 concurrent transactions

concurrency = ConcurrencyManager()

# Usage in service
async def import_spotify_album(
    album_id: str,
    user_id: int,
    session: AsyncSession
) -> Album:
    """
    Import single album with concurrency control.
    
    Ensures max 1 concurrent Spotify call, max 10 concurrent imports total.
    """
    async with concurrency.import_semaphore:
        async with concurrency.spotify_semaphore:
            # Fetch from Spotify (serialized)
            spotify_data = await spotify_service.get_album(album_id)
        
        # Process in parallel (up to 10 concurrent)
        async with concurrency.db_semaphore:
            album = await self._save_album(spotify_data, user_id, session)
    
    return album

# Protect critical sections with locks
lock = asyncio.Lock()

async def update_user_state(user_id: int) -> None:
    """
    Update user state with exclusive lock.
    
    Prevents race conditions when multiple imports running concurrently.
    """
    async with lock:
        user = await get_user(user_id)
        user.last_import_at = datetime.now()
        user.import_count += 1
        await session.commit()
```

### 2.5 Timeout Management

```python
# Pattern: Explicit timeouts for external API calls

async def search_spotify(
    query: str,
    timeout_seconds: int = 10
) -> Dict[str, Any]:
    """
    Search Spotify with timeout.
    
    Args:
        query: Search string
        timeout_seconds: Abort if no response in N seconds
        
    Returns:
        Search results or empty dict if timeout
        
    Raises:
        asyncio.TimeoutError: If timeout exceeded
    """
    try:
        return await asyncio.wait_for(
            spotify_service.search(query),
            timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        logger.warning(f"Spotify search timeout after {timeout_seconds}s for '{query}'")
        return {}

# Route with explicit timeout
@router.get("/search")
async def search(query: str = Query(..., min_length=1)) -> SearchResponse:
    """
    Search across all services with overall timeout.
    
    If any service takes too long, skip it and return partial results.
    """
    # Overall request timeout: 30 seconds
    try:
        return await asyncio.wait_for(
            _execute_search(query),
            timeout=30
        )
    except asyncio.TimeoutError:
        logger.error(f"Search timeout for '{query}'")
        raise HTTPException(
            status_code=504,
            detail="Search took too long, please try again"
        )

async def _execute_search(query: str) -> SearchResponse:
    """
    Execute search in parallel across services.
    
    Returns whatever completes within timeout.
    """
    results = await asyncio.gather(
        search_spotify(query, timeout_seconds=10),
        search_discogs(query, timeout_seconds=10),
        search_local(query, timeout_seconds=5),
        return_exceptions=True  # Don't fail if one service errors
    )
    
    # Aggregate results, filter out timeouts/errors
    return SearchResponse(
        spotify=results[0] if not isinstance(results[0], Exception) else {},
        discogs=results[1] if not isinstance(results[1], Exception) else {},
        local=results[2] if not isinstance(results[2], Exception) else {}
    )
```

### 2.6 Testing Async Code

```python
# Pattern: backend/tests/conftest.py (async fixtures)

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def async_db_session():
    """
    Create in-memory async database for each test.
    
    Automatically rolled back to prevent test pollution.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        yield session

# Usage in tests
@pytest.mark.asyncio
async def test_import_albums(async_db_session):
    """Test concurrent album imports."""
    service = AlbumService()
    
    # Simulate 5 concurrent imports
    tasks = [
        service.import_album(f"album_{i}", 1, async_db_session)
        for i in range(5)
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 5
    assert all(isinstance(r, Album) for r in results)

@pytest.mark.asyncio
async def test_timeout_handling(async_db_session):
    """Test that timeouts are handled gracefully."""
    class SlowService:
        async def search(self):
            await asyncio.sleep(5)  # Slow!
    
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            SlowService().search(),
            timeout=1
        )

# Mock async functions
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_spotify_search_mocked():
    """Mock Spotify service for testing."""
    spotify_service.search = AsyncMock(
        return_value={"results": [{"id": "1", "name": "Album"}]}
    )
    
    result = await spotify_service.search("query")
    
    assert result["results"][0]["name"] == "Album"
    spotify_service.search.assert_called_once_with("query")
```

### 2.7 Application Shutdown Cleanup

```python
# Pattern: Proper task cleanup on shutdown

from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    
    Runs startup code, yields control, runs cleanup code.
    """
    # Startup code
    logger.info("Starting AIME application")
    await initialize_services()
    
    yield  # Request handling happens here
    
    # Shutdown code - cleanup resources
    logger.info("Shutting down AIME application")
    
    # Cancel pending background tasks
    pending = asyncio.all_tasks()
    for task in pending:
        task.cancel()
    
    # Wait for all tasks with timeout
    try:
        await asyncio.wait_for(
            asyncio.gather(*pending, return_exceptions=True),
            timeout=5
        )
    except asyncio.TimeoutError:
        logger.warning("Some tasks didn't shutdown within 5 seconds")

app = FastAPI(lifespan=lifespan)
```

### 2.8 Common Pitfalls & Solutions

**Pitfall 1: Blocking the Event Loop**
```python
# ❌ WRONG: Sync I/O blocks event loop
import time
@router.get("/slow")
async def slow_endpoint():
    time.sleep(5)  # Blocks all other requests!
    return {"status": "done"}

# ✅ CORRECT: Use run_in_executor
@router.get("/slow")
async def slow_endpoint():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, time.sleep, 5)
    return {"status": "done"}
```

**Pitfall 2: Shared State in Concurrent Tasks**
```python
# ❌ WRONG: Shared mutable state
counts = {}
@router.post("/increment")
async def increment(key: str):
    count = counts.get(key, 0)
    await asyncio.sleep(0.1)  # Race condition window!
    counts[key] = count + 1

# ✅ CORRECT: Use atomic operations or locks
@router.post("/increment")
async def increment(key: str):
    async with locks[key]:  # Serialize access
        count = counts.get(key, 0)
        await asyncio.sleep(0.1)
        counts[key] = count + 1
```

**Pitfall 3: Not Handling Task Cancellation**
```python
# ❌ WRONG: Assumes task runs to completion
async def background_job():
    for i in range(1000):
        await slow_operation()
    print("Done!")  # May never execute if cancelled

# ✅ CORRECT: Handle cancellation
async def background_job():
    try:
        for i in range(1000):
            await slow_operation()
        print("Done!")
    except asyncio.CancelledError:
        print("Job cancelled, cleaning up...")
        raise  # Re-raise to properly cancel
```

## 3. Consequences

### 3.1 ✅ Positive

1. **Scalability**: Handle 100+ concurrent requests without thread overhead
2. **Responsiveness**: I/O-bound operations don't block request handling
3. **Resource Efficiency**: Async uses less memory than threading
4. **Explicit Control**: Semaphores, locks make interactions clear
5. **Modern Python**: Uses Python 3.8+ async/await syntax

### 3.2 ⚠️ Trade-offs

1. **Learning Curve**: Async concepts harder than sync for new developers
   - **Mitigation**: Document patterns, provide examples

2. **Debugging Difficulty**: Stack traces less intuitive, race conditions hard to reproduce
   - **Mitigation**: Comprehensive logging, structured concurrency

3. **Third-party Library Compatibility**: Not all Python libraries support async
   - **Mitigation**: Use run_in_executor for sync-only libraries

4. **Error Handling Complexity**: Exceptions in tasks can be silent
   - **Mitigation**: Check task exceptions, explicit error handling

### 3.3 Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Async routes | ✅ Done | All FastAPI endpoints async |
| Async services | 🟡 Partial | SpotifyService, AlbumService have async variants |
| Background tasks | ✅ Done | asyncio.create_task() pattern in place |
| Rate limiting | 🟡 Partial | Basic implemented, needs per-service tuning |
| Testing | ✅ Done | pytest-asyncio configured, fixtures ready |
| Timeouts | 🟡 Partial | Basic timeout handling, needs systematic review |

## 4. Alternatives Considered

### A. Thread-Based Concurrency (ThreadPoolExecutor)
**Rejected** ❌

```python
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)
def handle_request(request):
    executor.submit(process_request, request)
```

**Why Not**: 
- Higher memory overhead (1-2MB per thread)
- Complex synchronization needed
- Debugging harder with multiple threads
- FastAPI optimized for async

### B. Multi-Process (Process Pool)
**Rejected** ❌

```python
from multiprocessing import Pool
pool = Pool(processes=4)
```

**Why Not**:
- High overhead for short-lived tasks
- IPC (inter-process communication) expensive
- Shared state problematic
- Overkill for I/O-bound operations

### C. Celery/RabbitMQ for All Background Work
**Considered with Limitations** ⏳

```python
@celery_app.task
def import_albums(user_id: int):
    # Runs in separate worker process
    pass

# Call: import_albums.delay(user_id)
```

**Status**: Rejected for now (overengineering) ✗, but valid for future:
- Adds Redis/RabbitMQ operational complexity
- Best for jobs >30s or requiring retry/persistence
- AIME background jobs mostly <60s

### D. GraphQL with Async Resolvers
**Considered** ✓

Async-first GraphQL for complex nested queries

**Status**: Not adopted for Phase 4-5 (out of scope)
**Reason**: REST API sufficient, GraphQL adds complexity without proportional gain

## 5. Implementation Plan

### Phase 4 (Completed)
- ✅ Setup pytest-asyncio
- ✅ Create async database fixtures
- ✅ Async service methods in place

### Phase 5 (Current)
- 🔄 Document patterns (this ADR)
- 🔄 Add timeouts to all external API calls
- 🔄 Review and fix blocking calls
- 🔄 Comprehensive async tests

### Phase 5+
- Add metrics for task execution time
- Monitor for deadlocks/race conditions
- Profile async overhead
- Implement Celery for long jobs if needed

## 6. Performance Characteristics

| Operation | Time | Concurrency |
|-----------|------|-------------|
| Request handling | <50ms | 100+ concurrent |
| Spotify search | 500-1000ms | Serialized (1 concurrent) |
| Discogs query | 1-2s | 5 concurrent |
| Album import | 5-30s | 10 concurrent |
| Database query | 10-100ms | 8 concurrent (pool) |

## 7. References

### Code Files
- [Routes](../../backend/app/api/)
- [Services](../../backend/app/services/)
- [Core async utilities](../../backend/app/core/)
- [Tests](../../backend/tests/)

### Documentation
- [ADR-002: Testing Strategy](./ADR-002-TESTING-STRATEGY.md)
- [ADR-004: External API Integration](./ADR-004-EXTERNAL-API-INTEGRATION.md)
- [ADR-005: Database Design](./ADR-005-DATABASE-DESIGN.md)

### External Resources
- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [FastAPI async guide](https://fastapi.tiangolo.com/async-concurrency/)
- [Real Python async tutorial](https://realpython.com/async-io-python/)
- [Async best practices](https://github.com/aio-libs/aiohttp/wiki/Best-Practices)

### Related ADRs
- ADR-003: Circuit Breaker (timeout strategies)
- ADR-008: Logging & Observability (async logging)
- ADR-009: Caching Strategy (async cache layers)

## 8. Decision Trail

**Version 1.0 (2026-02-07)**: Initial decision on async-first architecture with strategic sync bridges

---

**Status**: ✅ **ACCEPTED**

This design ensures FastAPI applications remain responsive under load while preserving compatibility with synchronous libraries through executor patterns.

**Next Decision**: ADR-007 (Configuration Management)
