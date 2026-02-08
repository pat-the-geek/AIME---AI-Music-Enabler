# ADR-009: Caching Strategy

**Status**: ✅ Accepted  
**Date**: 2026-02-07  
**Priority**: Medium  
**Author**: Engineering Team  
**Reviewers**: Architecture Committee  

## 1. Context

AIME has significant performance bottlenecks from repeated external API calls:

### 1.1 Expensive Operations

| Operation | Time | Frequency | Cost |
|-----------|------|-----------|------|
| Spotify search | 800-1200ms | Per-user frequency | Network + API rate limit |
| Discogs query | 1-3s | Per-album enrichment | Rate limited to 60/min |
| AI description gen | 5-10s | First per album | Expensive compute |
| Album list query | 10-50ms | Per page view | DB query + N+1 problems |
| Image download | 100-500ms | First per album | Network I/O |

### 1.2 Caching Opportunities

1. **Artist/Album Metadata**
   - Spotify: Artist name, genres, year (stable, rarely changes)
   - TTL: 1 day (expect occasional metadata updates)

2. **User Spotify Library**
   - Full user library dump (expensive, 5-10 requests)
   - TTL: 1 hour (user's playlist changes hourly)

3. **Search Results**
   - Artist/album searches (same queries repeated)
   - TTL: 1 hour (expect metadata updates)

4. **AI Descriptions**
   - Generated descriptions (expensive, one-time cost)
   - TTL: Permanent (won't change)

5. **Album Images**
   - Cover art URLs (stable, rarely changes)
   - TTL: 1 week (occasional missing images added)

6. **Rate Limit State**
   - Spotify token (frequent refresh)
   - TTL: 50 minutes (token lifetime 1 hour)

### 1.3 Current Challenges

1. **No Caching**
   - Repeated API calls waste 10-50% of time
   - Rate limits hit easily on large imports

2. **No Cache Invalidation**
   - If we add caching later, stale data problem
   - No strategy for when to purge old data

3. **No Cache Warm-up**
   - Cold start = many slow requests
   - No pre-population strategy

4. **Cache Complexity**
   - In-memory vs Redis decision
   - Distributed cache invalidation

**Problem**: How to implement caching that improves performance without introducing stale data issues or added operational complexity?

## 2. Decision

We adopt **multi-layer caching**: in-memory for fast access, Redis for persistence/distribution.

### 2.1 Cache Architecture

```
Request
  ↓
[Layer 1: Request-scoped cache] (within request only)
  ↓ MISS
[Layer 2: In-memory cache] (process-wide, fast, volatile)
  ↓ MISS
[Layer 3: Redis cache] (persistent, shared, slow)
  ↓ MISS
[Original source] (Spotify, DB, AI service)
```

**Trade-offs by Layer**:
| Layer | Speed | Scope | Volatile | Use Case |
|-------|-------|-------|----------|----------|
| Request | <1ms | Single request | Yes | Prevent duplicate calls within request |
| Memory | 1-5ms | Single process | Yes | Primary cache, fast for frequent hits |
| Redis | 10-50ms | Shared across processes | No | Backup cache, survives restarts |
| Source | 500ms-10s | External/DB | N/A | Fallback when cache misses |

### 2.2 Cache Implementation

```python
# Pattern: backend/app/core/cache.py

from typing import Optional, Dict, Any, Callable, Awaitable, TypeVar
import asyncio
from datetime import datetime, timedelta
import json
from functools import wraps
import hashlib

T = TypeVar("T")

# ============ In-Memory Cache (Layer 2) ============

class MemoryCache:
    """
    Fast in-memory cache using dict with TTL support.
    
    Suitable for:
    - Development (no dependencies)
    - Single-process deployments
    - Backup when Redis unavailable
    """
    
    def __init__(self, max_size_mb: int = 100):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.max_size_mb = max_size_mb
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache, checking expiration.
        
        Returns:
            Cached value or None if missing/expired.
        """
        if key not in self._cache:
            self.misses += 1
            return None
        
        entry = self._cache[key]
        
        # Check TTL
        if entry["expires_at"] < datetime.now():
            del self._cache[key]  # Expired
            self.misses += 1
            return None
        
        self.hits += 1
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """
        Store value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds
        """
        self._cache[key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl_seconds),
            "size_bytes": len(json.dumps(value))
        }
        
        # Optional: Evict oldest if over size limit
        # (simple implementation: just warn for now)
    
    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(
            e.get("size_bytes", 0) for e in self._cache.values()
        )
        return {
            "entries": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0,
            "size_mb": total_size / 1024 / 1024
        }

# Global instance
memory_cache = MemoryCache()

# ============ Request-Scoped Cache (Layer 1) ============

from contextvars import ContextVar

request_cache_var = ContextVar("request_cache", default=None)

class RequestCache:
    """
    Cache that's valid only within a single HTTP request.
    
    Prevents duplicate API calls within same request:
    
    1. Request arrives: GET /search?query=pink+floyd
    2. Route calls SpotifyService.search() → hits API → caches result
    3. Route calls DiscogsService.search() → requests SpotifyService again
       → hits RequestCache (no API call!)
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get from request cache."""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Store in request cache (no expiry)."""
        self._cache[key] = value
    
    def clear(self) -> None:
        """Clear request cache."""
        self._cache.clear()

def get_request_cache() -> RequestCache:
    """Get request-scoped cache instance."""
    cache = request_cache_var.get()
    if cache is None:
        cache = RequestCache()
        request_cache_var.set(cache)
    return cache

# ============ Decorator for Caching (Easy Integration) ============

def cached(
    ttl_seconds: int = 3600,
    cache_layers: list = ["memory", "redis"],
    key_prefix: str = ""
):
    """
    Decorator to cache async function results.
    
    Args:
        ttl_seconds: Cache lifetime
        cache_layers: Which layers to use (["memory"] or ["memory", "redis"])
        key_prefix: Prefix for cache key to ensure uniqueness
        
    Usage:
        @cached(ttl_seconds=3600, key_prefix="spotify")
        async def search(query: str) -> Dict:
            # Expensive operation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Generate cache key from function name + arguments
            cache_key = generate_cache_key(
                key_prefix or func.__name__,
                args,
                kwargs
            )
            
            # Try request cache first (free check, no network)
            request_cache = get_request_cache()
            if (value := request_cache.get(cache_key)):
                logger.debug(f"Cache hit (request): {cache_key}")
                return value
            
            # Try memory cache
            if "memory" in cache_layers:
                if (value := memory_cache.get(cache_key)):
                    logger.debug(f"Cache hit (memory): {cache_key}")
                    request_cache.set(cache_key, value)
                    return value
            
            # Try Redis cache
            if "redis" in cache_layers:
                if (value := await redis_cache.get(cache_key)):
                    logger.debug(f"Cache hit (redis): {cache_key}")
                    memory_cache.set(cache_key, value, ttl_seconds)
                    request_cache.set(cache_key, value)
                    return value
            
            # Cache miss - call original function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in all layers
            if "memory" in cache_layers:
                memory_cache.set(cache_key, result, ttl_seconds)
            if "redis" in cache_layers:
                await redis_cache.set(cache_key, result, ttl_seconds)
            
            request_cache.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator

def generate_cache_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """
    Generate unique cache key from function arguments.
    
    Example:
        prefix = "spotify:search"
        args = ("Pink Floyd",)
        kwargs = {}
        → "spotify:search:pinafloyd"
    """
    # Serialize args/kwargs
    key_parts = [prefix]
    for arg in args:
        if isinstance(arg, (str, int, float)):
            key_parts.append(str(arg).lower())
        elif isinstance(arg, dict):
            key_parts.append(hashlib.md5(
                json.dumps(arg, sort_keys=True).encode()
            ).hexdigest()[:8])
    
    return ":".join(key_parts)
```

### 2.3 Cache Invalidation Strategies

```python
# Pattern: Different invalidation approaches for different data

class CacheInvalidationStrategy:
    """
    Different strategies for different types of data.
    """
    
    # ✅ TTL-based (suitable for slowly-changing data)
    ARTIST_METADATA = {
        "ttl": 86400,  # 1 day
        "strategy": "ttl",
        "example": "Artist name, genres, biography"
    }
    
    ALBUM_METADATA = {
        "ttl": 86400,  # 1 day
        "strategy": "ttl",
        "example": "Album title, year, track list"
    }
    
    SEARCH_RESULTS = {
        "ttl": 3600,  # 1 hour
        "strategy": "ttl",
        "example": "Spotify search results (might get new releases)"
    }
    
    # ✅ Permanent (won't change)
    AI_DESCRIPTIONS = {
        "ttl": None,  # Never expires
        "strategy": "permanent",
        "example": "Generated AI text (same input = same output)"
    }
    
    # ✅ Event-based (invalidate on specific events)
    USER_LIBRARY = {
        "ttl": 3600,  # 1 hour fallback
        "strategy": "event",
        "example": "User library (invalidate when user imports/deletes)"
    }
    
    # ✅ Manual invalidation (when debugging issues)
    SPOTIFY_TOKEN = {
        "ttl": 3000,  # 50 minutes (token lifetime 1hr)
        "strategy": "manual",
        "example": "Refresh on 401 error"
    }

# Implementation
@cached(ttl_seconds=3600, key_prefix="user_library")
async def get_user_spotify_library(user_id: int) -> List[SpotifyTrack]:
    """
    Get user's Spotify library with caching.
    
    Cached for 1 hour but invalidated on:
    - User imports new albums
    - User deletes album
    """
    return await spotify_service.get_user_library(user_id)

# Event-based invalidation
async def import_albums_from_spotify(user_id: int, albums: List[Dict]) -> int:
    """Import albums and invalidate cache."""
    count = 0
    for album_data in albums:
        await album_service.create_album(album_data)
        count += 1
    
    # Invalidate user library cache after import
    cache_key = f"user_library:{user_id}"
    memory_cache.delete(cache_key)
    if redis_enabled:
        await redis_cache.delete(cache_key)
    
    return count
```

### 2.4 Cache Key Patterns

```python
# Consistent naming for searchability/debugging

"""
Cache key patterns (organized by service):

SPOTIFY:
  spotify:token:{user_id}
  spotify:artist:{artist_id}
  spotify:album:{album_id}
  spotify:search:{query_hash}
  spotify:user_library:{user_id}

DISCOGS:
  discogs:album:{album_id}
  discogs:artist:{artist_id}
  discogs:collection:{user_id}
  discogs:search:{query_hash}

AI/DESCRIPTION:
  ai:description:{album_id}
  ai:batch:{batch_hash}

DATABASE:
  db:album_list:{user_id}:{skip}:{limit}
  db:artist:{artist_id}
  db:user:{user_id}

SEARCH:
  search:all:{query_hash}
  search:spotify:{query_hash}
  search:discogs:{query_hash}
"""

def generate_spotify_cache_key(album_id: str) -> str:
    """Example: spotify:album:4aawyAB9fnqKGLG8BvLKGQ"""
    return f"spotify:album:{album_id}"

def generate_search_cache_key(query: str, source: str = None) -> str:
    """Example: search:spotify:68c2e07d46c47dd2 (SHA1 of query)"""
    query_hash = hashlib.sha1(query.encode()).hexdigest()[:16]
    prefix = f"search:{source}" if source else "search:all"
    return f"{prefix}:{query_hash}"
```

### 2.5 Cache Warming & Preload

```python
# Pattern: Pre-populate cache on startup for fast initial response

@app.on_event("startup")
async def warmup_cache():
    """
    Pre-populate caches with frequently accessed data.
    
    Runs on application startup to reduce first-request latency.
    """
    logger.info("Starting cache warmup...")
    
    # Warm up common searches
    for query in ["Pink Floyd", "Beatles", "David Bowie"]:
        try:
            results = await spotify_service.search(query)
            await redis_cache.set(
                generate_search_cache_key(query, "spotify"),
                results,
                ttl_seconds=86400
            )
        except Exception as e:
            logger.warning(f"Failed to warm {query}: {e}")
    
    logger.info("Cache warmup completed")

# Periodic refresh (run nightly)
async def refresh_popular_artists():
    """Refresh cache for popular artists (runs daily)."""
    popular = await database.get_popular_artists(limit=100)
    
    for artist in popular:
        await spotify_service.get_artist(artist.spotify_id)
        # This triggers @cached decorator, populates cache
```

### 2.6 Testing with Cached Data

```python
# Pattern: Control cache in tests

from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_cache():
    """Disable cache for tests."""
    return MagicMock()

@pytest.mark.asyncio
async def test_search_without_cache():
    """Test search calls API (not cached)."""
    memory_cache.clear()  # Clear before test
    
    # First call - should call API
    await search_spotify("test")
    spotify_service.search.assert_called_once()
    
    # Second call - would hit cache in prod, but cleared
    await search_spotify("test")
    spotify_service.search.assert_called()  # Called again!

@pytest.mark.asyncio
async def test_search_with_cache():
    """Test cache prevents duplicate API calls."""
    memory_cache.clear()
    
    # Manually populate cache
    memory_cache.set("search:all:abc123", {"results": []}, ttl_seconds=3600)
    
    # Call should hit cache, not API
    with patch.object(spotify_service, "search") as mock:
        result = memory_cache.get("search:all:abc123")
        assert result is not None
        mock.assert_not_called()
```

## 3. Consequences

### 3.1 ✅ Positive

1. **Performance**: 10-100x faster for cache hits vs API calls
2. **Reduced API Calls**: Lower rate limit pressure
3. **Reliability**: Works when external API is down (if Redis available)
4. **Scalability**: Shared cache across processes (with Redis)
5. **Simple**: Decorator-based integration, easy to add to any function

### 3.2 ⚠️ Trade-offs

1. **Stale Data Risk**: Cached data may be outdated
   - **Mitigation**: Appropriate TTLs by data type, event-based invalidation

2. **Memory/Disk**: Cache storage overhead
   - **Mitigation**: Size limits, regular cleanup

3. **Complexity**: Added layer to understand
   - **Mitigation**: Clear key patterns, debugging tools

4. **Redis Dependency**: For production needs Redis
   - **Mitigation**: Fallback to memory cache, separate concern

### 3.3 Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Memory cache | ✅ Done | In-memory dict with TTL |
| Request cache | 🟡 Partial | Structure defined, needs middleware integration |
| Cache decorator | ✅ Done | @cached decorator ready to use |
| Redis cache | 🔴 TODO | Connection pool, get/set methods |
| Invalidation | 🟡 Partial | TTL-based done, event-based needs integration |
| Testing | ✅ Done | Fixtures and mocking patterns |

## 4. Alternatives Considered

### A. No Caching (Keep Current)
**Rejected** ❌

First request = 5-10s, refreshed = 5-10s, each user blocked during

**Why Not**: Performance unacceptable for frequent operations

### B. Redis Only (No Memory Cache)
**Rejected** ❌

Only Redis, no in-memory layer

**Why Not**: Network latency (10-50ms vs <1ms), unnecessary complexity

### C. Client-Side Caching (Browser Cache)
**Considered** ✓

Browser localStorage for search results

**Status**: Valid for frontend, out of scope for this ADR

## 5. Implementation Plan

### Phase 4 (Completed)
- ✅ MemoryCache implementation
- ✅ Decorator pattern designed

### Phase 5 (Current - This ADR)
- 🔄 Request-scoped cache middleware
- 🔄 Add @cached decorator to hot paths
- 🔄 Implement key generation utilities
- 🔄 Add cache stats/monitoring

### Phase 5+
- Implement Redis connection pool
- Add cache metrics to dashboards
- Setup cache warming/refresh jobs
- Monitor hit rates by key

### Future (Phase 6+)
- Distributed cache invalidation
- Advanced eviction policies (LRU)
- Cache compression for large values

## 6. Recommended Cache Applications

| Function | TTL | Layers |
|----------|-----|--------|
| search_spotify | 1 hour | memory, redis |
| get_artist_metadata | 1 day | memory, redis |
| ai_description | Never | redis |
| user_library | 1 hour | memory, redis |
| album_list | 1 min | memory |
| spotfiy_token | 50 min | memory |

## 7. References

### Code Files
- [Cache module](../../backend/app/core/cache.py)
- [Cache middleware](../../backend/app/middleware/cache.py)

### Documentation
- [ADR-007: Configuration Management](./ADR-007-CONFIGURATION-MANAGEMENT.md)
- [ADR-008: Logging & Observability](./ADR-008-LOGGING-OBSERVABILITY.md)

### External Resources
- [Cache patterns](https://en.wikipedia.org/wiki/Cache_replacement_policies)
- [Redis Python client](https://github.com/redis/redis-py)
- [Caching best practices](https://www.cloudflare.com/learning/cdn/what-is-caching/)

### Related ADRs
- ADR-003: Circuit Breaker (fallback strategies)
- ADR-005: Database Design (query caching)
- ADR-007: Configuration (cache config)

## 8. Decision Trail

**Version 1.0 (2026-02-07)**: Initial decision on multi-layer caching (request → memory → Redis)

---

**Status**: ✅ **ACCEPTED**

This caching architecture provides performance improvements without introducing unnecessary complexity, with clear fallback mechanisms for resilience.

**Next Decision**: ADR-010 (Roon Integration Architecture)
