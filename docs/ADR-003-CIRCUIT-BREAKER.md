# ADR-003: Circuit Breaker & Error Handling Pattern

**Status**: Accepted  
**Date**: 2026-02-07  
**Priority**: High  
**Impact**: Resilience, API Stability, User Experience

---

## Context

AIME integrates with three external APIs (Spotify, Discogs, EurIA) that can:
1. **Timeout**: Network delays or service slowness
2. **Throttle**: Rate limiting (429 Too Many Requests)
3. **Fail**: Intermittent server errors (5xx)
4. **Go Down**: Temporary unavailability

**Problems Without Circuit Breaker**:
- Failed API calls retry infinitely, increasing latency
- Rate limits cause cascading failures
- Bad service conditions propagate through system
- Users see slow/broken app during external API issues
- Resource exhaustion (connection pools, memory)

**Example Scenario**:
```
User requests import → Discogs Service fails → Retries 3x → 
Takes 30+ seconds → App appears frozen → User might reload →
Even more Discogs API calls → Service floods → Rate limited →
Everyone gets errors
```

---

## Decision

**Implement Circuit Breaker Pattern with Exponential Backoff & Fallback Strategies:**

### 1. **Circuit Breaker State Machine**

```
┌─────────────┐
│   CLOSED    │ (Normal operation)
│ (Working)   │
└──────┬──────┘
       │ threshold failures
       └──────────────────────┐
                              ▼
                    ┌──────────────────┐
                    │      OPEN        │
                    │  (Not working,   │
                    │   rejecting      │
                    │   requests)      │
                    └────────┬─────────┘
                             │ timeout
                             ▼
                    ┌─────────────────┐
                    │ HALF_OPEN       │
                    │ (Testing if     │
                    │  service works) │
                    └────────┬────────┘
                             │
                ┌────────────┴──────────────┐
         success│                          │failure
                ▼                          ▼
         ┌─────────┐              ┌────────────┐
         │ CLOSED  │              │ OPEN       │
         └─────────┘              └────────────┘
```

### 2. **Circuit Breaker Implementation**

**Configuration**:
```python
discogs_circuit_breaker = CircuitBreaker(
    name="Discogs",
    failure_threshold=5,      # Open after 5 failures
    success_threshold=3,      # Close after 3 successes
    timeout=60,               # Try after 60 seconds in OPEN
    recovery_timeout=300      # Wait 5 min before HALF_OPEN->CLOSED
)
```

**States & Behavior**:

| State | Behavior | When It Occurs |
|-------|----------|---|
| **CLOSED** | Requests go through, failures tracked | Normal operation |
| **OPEN** | Requests rejected with exception, no API calls | After threshold failures |
| **HALF_OPEN** | Allow single test request to check if service recovered | After timeout from OPEN |

### 3. **Error Handling Hierarchy**

```python
try:
    # LAYER 1: Check circuit breaker
    if circuit_breaker.state == "OPEN":
        raise DiscogsServiceException("Service temporarily unavailable")
    
    # LAYER 2: Rate limit wait
    self._rate_limit_wait()
    
    # LAYER 3: Make API call with timeout
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    
    # LAYER 4: Record success (for circuit breaker)
    circuit_breaker.record_success()
    return response.json()
    
except requests.exceptions.Timeout:
    # Circuit breaker records failure
    circuit_breaker.record_failure()
    # Log and retry
    logger.warning("API timeout, will retry")
    raise
    
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:  # Rate limited
        # Special handling - wait before retry
        logger.warning("Rate limited, backing off")
    circuit_breaker.record_failure()
    raise
    
except DiscogsServiceException:
    # Circuit breaker already open - fail fast
    raise
```

### 4. **Retry Strategy with Exponential Backoff**

```python
@retry_with_backoff(
    max_attempts=3,
    initial_delay=2.0,    # Start with 2 seconds
    max_delay=10.0,       # Cap at 10 seconds
    exponential_base=2.0  # 2^attempt
)
def get_collection(self):
    """Retry on failure: 2s, 4s, 8s (max 10s)."""
    pass
```

**Backoff Formula**:
```
delay = min(initial_delay * (exponential_base ** attempt), max_delay)

Attempt 1: min(2 * 2^0, 10) = 2s
Attempt 2: min(2 * 2^1, 10) = 4s  
Attempt 3: min(2 * 2^2, 10) = 8s
Attempt 4: min(2 * 2^3, 10) = 10s (capped)
```

### 5. **Service-Specific Strategies**

**Discogs Service** (Strict Rate Limits):
```python
class DiscogsService:
    def __init__(self):
        self.rate_limit_delay = 0.5  # Min 500ms between requests
        self.circuit_breaker = CircuitBreaker(
            "Discogs",
            failure_threshold=5,
            success_threshold=3
        )
    
    def _rate_limit_wait(self):
        """Enforce 500ms minimum between API calls."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
```

**Spotify Service** (Token-Based Requests):
```python
class SpotifyService:
    def __init__(self):
        self.token_cache = None
        self.token_expiry = 0
        self.circuit_breaker = CircuitBreaker(
            "Spotify",
            failure_threshold=10,  # More lenient
            success_threshold=3
        )
    
    async def _get_access_token(self):
        """Cache token to reduce API calls."""
        if self.token_cache and time.time() < self.token_expiry:
            return self.token_cache
        # Refresh token
```

**AI Service** (Timeout-Prone):
```python
class AIService:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            "AI",
            failure_threshold=3,   # Fail fast
            success_threshold=2,
            timeout=30             # Quick recovery
        )
    
    async def ask_for_ia(self, prompt: str):
        """SSE streaming from EurIA API."""
        # Timeout if no data for 120 seconds
        async with httpx.AsyncClient(timeout=120) as client:
            pass
```

### 6. **Fallback Strategies**

When a service fails, implement fallbacks:

**Spotify Image Search**:
```python
async def search_album_image(artist: str, album: str):
    """Try multiple search strategies."""
    
    # Strategy 1: Exact match
    result = await try_search(f'artist:"{artist}" album:"{album}"')
    if result: return result
    
    # Strategy 2: Without quotes
    result = await try_search(f'artist:{artist} album:{album}')
    if result: return result
    
    # Strategy 3: Artist only
    result = await try_search(f'artist:{artist}')
    if result: return result
    
    # Strategy 4: Last.FM fallback
    result = await try_lastfm_image(artist, album)
    if result: return result
    
    # All strategies failed
    return None
```

**Discogs Import**:
```python
def get_collection(self, skip_ids=None):
    """Pagination with error recovery."""
    albums = []
    
    try:
        # Normal pagination
        for page in range(1, max_pages):
            releases = fetch_page(page)
            albums.extend(releases)
    
    except RateLimitError:
        # Return what we got, log how much succeeded
        logger.info(f"Got {len(albums)} albums before rate limit")
        return albums  # Partial success
    
    except ServiceUnavailable:
        # Circle breaker will handle retry
        raise
    
    return albums
```

---

## Consequences

### ✅ Positive Impacts

1. **System Stability**: Failed services don't crash app
2. **Fast Failure**: Don't waste time retrying dead services
3. **Graceful Degradation**: Partial functionality instead of complete failure
4. **Resource Protection**: Prevent connection pool exhaustion
5. **User Experience**: App responds quickly even if services down
6. **Monitoring**: Circuit breaker state can trigger alerts

### ⚠️ Trade-offs

1. **Complexity**: More code to understand and maintain
2. **Configuration**: Need to tune failure thresholds per service
3. **Partial Data**: Fallbacks might return incomplete results
4. **Monitoring**: Need to track circuit breaker state
5. **Testing**: Harder to test failure scenarios

### 📊 Real-World Impact

**Before Circuit Breaker**:
- User imports Discogs collection
- Discogs API timeouts on page 5
- System retries 10x, each takes 30s
- Total import time: 5+ minutes
- User thinks app is broken

**After Circuit Breaker**:
- User imports Discogs collection
- Discogs API timeouts on page 5
- Circuit breaker opens after 2-3 failures
- System returns what it got (4 pages worth)
- User gets partial import in 30 seconds
- App notes "partial import due to API issue"

---

## Alternatives Considered

### 1. Retry Forever with Longer Waits
- **Pros**: Eventually succeeds if service recovers
- **Cons**: App appears frozen, user thinks it's broken
- **Rejected**: Bad UX, resource waste

### 2. Timeout & Fail Immediately
- **Pros**: Fast feedback
- **Cons**: Transient errors cause failures, no resilience
- **Rejected**: Doesn't handle temporary glitches

### 3. Queue Tasks for Later
- **Pros**: Decouple from API availability
- **Cons**: Adds complexity (background worker), delayed feedback
- **Adopted For**: Future enhancement (Phase 6+)

### 4. Always Serve Cached Data
- **Pros**: No failures with cache
- **Cons**: Data becomes stale, inconsistent
- **Adopted For**: Limited use (avatar images, thumbnails)

---

## Implementation Status

### ✅ Implemented (Phase 4)

- `CircuitBreaker` class in `app/core/retry.py`
- `retry_with_backoff` decorator
- Integrated into `AIService`
- Integrated into `DiscogsService`
- Rate limiting in `DiscogsService`

### 🟡 In Progress (Phase 5)

- [ ] Add circuit breaker to `SpotifyService`
- [ ] Document circuit breaker states & metrics
- [ ] Add circuit breaker monitoring endpoint
- [ ] Test all failure scenarios

### 🔴 Future (Phase 6+)

- [ ] Queue failed requests for retry
- [ ] Circuit breaker dashboard
- [ ] Alert when circuit opens
- [ ] Graceful service degradation page

---

## References

### Resilience Patterns
- **Circuit Breaker Pattern**: https://martinfowler.com/bliki/CircuitBreaker.html
- **Timeouts & Retries**: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
- **Fallback Strategies**: https://en.wikipedia.org/wiki/Fallback_(network_engineering)

### AIME Implementation
- Circuit breaker: `backend/app/core/retry.py`
- DiscogsService usage: `backend/app/services/discogs_service.py`
- AIService usage: `backend/app/services/external/ai_service.py`

### Python Libraries
- **tenacity**: Advanced retry decorator
- **pybreaker**: Alternative circuit breaker
- **timeout-decorator**: Function-level timeouts

---

**Status**: ✅ Accepted as of 2026-02-07  
**Owner**: GitHub Copilot  
**Next Review**: 2026-03-07

