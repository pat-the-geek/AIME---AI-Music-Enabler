# ADR-004: External API Integration Pattern

**Status**: ✅ Accepted  
**Date**: 2026-02-07  
**Priority**: High  
**Author**: Engineering Team  
**Reviewers**: Architecture Committee  

## 1. Context

AIME integrates with three critical external music APIs:

1. **Spotify Web API** (OAuth 2.0)
   - User authentication and playlist management
   - Track information and streaming metadata
   - Requires token refresh mechanism

2. **Discogs API** (REST with API Key)
   - Music collection database and release information
   - Album/artist information retrieval
   - Rate limiting: 60 req/min for authenticated requests

3. **EurIA/AI Service** (Custom SSE endpoint)
   - AI-generated descriptions for albums/artists
   - Server-Sent Events (SSE) streaming for long operations
   - Timeout handling for generation operations

Each service has unique:
- Authentication mechanisms
- Rate limiting requirements
- Error conditions and recovery strategies
- Fallback behaviors
- Performance characteristics

**Problem**: How to integrate disparate external APIs consistently while maintaining:
- Resilience under API failures
- Rate limit compliance
- Token/key security
- Fallback and degradation strategies
- Testability and mocking

## 2. Decision

We adopt a **Unified External Service Integration Pattern** with:

### 2.1 Service Layer Architecture

Each external API gets a dedicated service class:

```python
# Pattern: backend/app/services/{service_name}_service.py

class SpotifyService:
    """Spotify Web API integration with OAuth token refresh."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._cache_token()
    
    @retry_with_exponential_backoff(max_retries=3)
    async def search(self, query: str, search_type: str) -> Dict[str, Any]:
        """Execute search with automatic retry and token refresh."""
    
    def _refresh_token_if_needed(self) -> None:
        """Manage OAuth token lifecycle."""

class DiscogsService:
    """Discogs API client with rate limiting and pagination."""
    
    def __init__(self, api_key: str, username: str):
        self.api_key = api_key
        self.client = discogs_client.Client(...)
        self.rate_limit_delay = 0.5  # 500ms between requests
        self.last_request_time = 0
    
    @circuit_breaker
    def get_collection(self) -> List[Dict[str, Any]]:
        """Fetch user's collection with circuit breaker protection."""
    
    def _rate_limit_wait(self) -> None:
        """Enforce minimum delay between API requests."""

class EuriaService:
    """AI description generation with SSE streaming."""
    
    @timeout(seconds=120)
    async def generate_description(self, topic: str) -> AsyncIterator[str]:
        """Stream AI-generated description, yielding chunks."""
```

### 2.2 Authentication & Secrets Management

```python
# Pattern: backend/app/core/security.py

class SecretsManager:
    """Central vault for API credentials."""
    
    def __init__(self, config_path: str):
        self.secrets = load_secrets(config_path)
    
    @property
    def spotify_client_id(self) -> str:
        """Spotify OAuth client ID from env/config."""
    
    @property
    def discogs_api_key(self) -> str:
        """Discogs API key (can be None for anonymous)."""
    
    @property
    def euria_endpoint(self) -> str:
        """EurIA service base URL."""
```

**Rules**:
- **Never** hardcode credentials in code
- Store in `secrets.json` (gitignore'd) or environment variables
- Rotate OAuth tokens automatically
- Cache tokens temporarily (1hr TTL for Spotify)
- Log requests at DEBUG level only (no credentials)

### 2.3 Error Handling & Fallback Strategy

```python
# Pattern: backend/app/core/exceptions.py

class ExternalServiceException(Exception):
    """Base for all external API failures."""
    
    def __init__(self, service: str, operation: str, 
                 status_code: int, message: str):
        self.service = service  # "spotify", "discogs", "euria"
        self.operation = operation  # "search", "get_item", etc
        self.status_code = status_code
        self.message = message

class RateLimitExceeded(ExternalServiceException):
    """API rate limit hit (429)."""
    def __init__(self, service: str, retry_after: int):
        self.retry_after = retry_after

class ServiceDown(ExternalServiceException):
    """API temporary unavailable (503, timeout)."""
    pass

class AuthenticationFailed(ExternalServiceException):
    """Token expired or invalid credentials (401, 403)."""
    pass

# Fallback strategies per service
FALLBACK_STRATEGIES = {
    "spotify": [
        ("cache_from_previous_session", "Cached results"),
        ("return_minimal_data", "ID only, no metadata"),
        ("fail_gracefully", "Return empty, log error"),
    ],
    "discogs": [
        ("lightweight_retry", "Exponential backoff 2-5s"),
        ("cache_from_last_import", "Use last known state"),
        ("manual_entry_mode", "User can add via UI"),
    ],
    "euria": [
        ("use_template_description", "Generic fallback text"),
        ("queue_for_retry", "Retry in background job"),
        ("skip_enrichment", "Leave field empty"),
    ],
}
```

### 2.4 Request/Response Handling

```python
# Pattern: Consistent request patterns across services

class SpotifyService:
    async def search(self, query: str) -> Dict[str, Any]:
        """
        Search Spotify for artists/albums.
        
        Args:
            query: Search string (artist name, album, track)
            
        Returns:
            Dict with normalized structure:
            {
                "artists": [{"id": "...", "name": "...", "uri": "..."}],
                "albums": [{"id": "...", "artist": "...", "title": "..."}],
            }
            
        Raises:
            RateLimitExceeded: If 429 received
            AuthenticationFailed: If token invalid/expired
            ServiceDown: If 503 or timeout
            ExternalServiceException: For other errors
        """
        # Step 1: Validate input
        query = query.strip()
        if not query or len(query) < 2:
            raise ValueError("Query too short")
        
        # Step 2: Check cache (Redis/in-memory)
        cache_key = f"spotify:search:{query}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        # Step 3: Prepare request
        headers = self._build_headers()  # Adds auth token
        params = {"q": query, "limit": 20}
        
        # Step 4: Execute with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.get(
                    "/search",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    # Token expired, refresh and retry
                    self._refresh_token_if_needed()
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise AuthenticationFailed(...)
                elif e.response.status_code == 429:
                    # Rate limit: back off
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    raise RateLimitExceeded("spotify", retry_after)
                else:
                    raise
            except (asyncio.TimeoutError, httpx.ConnectError):
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise ServiceDown("spotify", "search")
        
        # Step 5: Normalize response
        results = self._normalize_search_results(response.json())
        
        # Step 6: Cache and return
        self._set_cache(cache_key, results, ttl=3600)  # 1 hour
        return results
```

### 2.5 Rate Limiting per Service

**Spotify**:
- No explicit rate limit enforcement (uses 429 responses)
- Built-in retry with Retry-After header
- Token refresh: Once per hour or on 401

**Discogs**:
- Rate limit: 60 requests/minute (authenticated)
- Client side enforcement: 500ms delay between calls
- Implementation:
  ```python
  def _rate_limit_wait(self) -> None:
      """Wait until 500ms elapsed since last request."""
      elapsed = time.time() - self.last_request_time
      if elapsed < self.rate_limit_delay:
          time.sleep(self.rate_limit_delay - elapsed)
      self.last_request_time = time.time()
  ```

**EurIA**:
- Timeout: 120 seconds per operation
- No rate limiting (internal service)
- SSE stream buffer: 8KB chunks

### 2.6 Circuit Breaker Integration

```python
# All external service calls go through circuit breaker

@circuit_breaker(failure_threshold=5, timeout=60)
async def get_artist_info(artist_id: str) -> Dict[str, Any]:
    """Fetch artist from Spotify with circuit breaker."""
    # Implementation

# Circuit breaker states:
# CLOSED: Normal operation, allow requests
# OPEN: Service failing, reject requests, wait 60s
# HALF_OPEN: Test request, decide if move to CLOSED or OPEN
```

### 2.7 Testing Strategy

**Unit Testing** (No network):
```python
def test_spotify_search_success(spotify_service, httpx_mock):
    """Mock successful search response."""
    httpx_mock.add_response(
        method="GET",
        url="https://api.spotify.com/v1/search",
        json={"artists": {...}, "albums": {...}}
    )
    
    result = spotify_service.search("Pink Floyd")
    
    assert len(result["albums"]) > 0
    assert result["albums"][0]["title"] == "The Wall"

def test_spotify_rate_limit(spotify_service, httpx_mock):
    """Rate limit 429 triggers backoff."""
    httpx_mock.add_response(
        method="GET",
        status_code=429,
        headers={"Retry-After": "60"}
    )
    
    with pytest.raises(RateLimitExceeded) as exc:
        spotify_service.search("query")
    
    assert exc.value.retry_after == 60

def test_discogs_enforce_rate_limit(discogs_service):
    """Rate limiter enforces 500ms minimum between calls."""
    import time
    
    start = time.time()
    discogs_service._rate_limit_wait()
    discogs_service._rate_limit_wait()
    elapsed = time.time() - start
    
    assert elapsed >= 0.5  # At least 500ms between calls
```

**Integration Testing** (Real APIs, with caution):
```python
@pytest.mark.integration
async def test_spotify_oauth_flow():
    """Full OAuth token refresh cycle."""
    service = SpotifyService(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET
    )
    
    # Simulate token expiry
    service.token_expires_at = time.time() - 1
    service._refresh_token_if_needed()
    
    assert service.token_expires_at > time.time()
```

## 3. Consequences

### 3.1 ✅ Positive

1. **Consistency**: All external APIs follow same error handling pattern
2. **Resilience**: Circuit breaker, retry logic, fallback strategies built-in
3. **Testability**: Easy to mock with httpx-mock or unit test fixtures
4. **Security**: Centralized secrets management, no credential leaks
5. **Observability**: Consistent logging across services
6. **Scalability**: Easy to add new external services following pattern
7. **Performance**: Built-in caching, rate limit respect

### 3.2 ⚠️ Trade-offs

1. **Complexity**: More code for error handling vs simple requests
   - **Mitigation**: Utilities and base classes reduce boilerplate

2. **Token Management**: Spotify OAuth refresh logic increases state
   - **Mitigation**: Immutable tokens with clear refresh strategy

3. **Debugging**: Multiple fallback paths make tracing harder
   - **Mitigation**: Comprehensive logging at each decision point

4. **Performance Overhead**: Circuit breaker state machine adds latency
   - **Mitigation**: <1ms overhead, negligible vs network latency

### 3.3 Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| SpotifyService | 🟡 Partial | Token refresh done, caching needed |
| DiscogsService | ✅ Implemented | Rate limiting, pagination working |
| EuriaService | 🟡 Partial | SSE streaming present, error handling TODO |
| Circuit breaker | ✅ Implemented | Phase 4 complete |
| Secrets Manager | ✅ Implemented | secrets.json pattern established |
| Error hierarchy | 🟡 Partial | Basic exceptions in place, domain-specific TODO |

## 4. Alternatives Considered

### A. Monolithic API Wrapper
**Rejected** ❌

Single class wrapping all three services:
```python
class MusicAPI:
    def spotify_search(self): ...
    def discogs_get(self): ...
    def euria_generate(self): ...
```

**Why Not**: Violates Single Responsibility, hard to test, mixes auth mechanisms

### B. Direct Library Usage
**Rejected** ❌

Use Spotify/Discogs Python libraries directly without our wrapper:
```python
from spotipy import Spotify
spotify = Spotify(auth_manager=SpotifyClientCredentials(...))
results = spotify.search(q="artist")
```

**Why Not**: No circuit breaker, no fallback strategy, tight coupling to library versions

### C. Message Queue for Async
**Rejected (for now)** ⏳

Use Celery/RQ for all external API calls:
```python
@celery_app.task
def fetch_spotify_search(query):
    ...

# Call: fetch_spotify_search.delay(query)
```

**Why Not**: Adds operational complexity (Redis), overkill for queries <5s
**Future**: May reconsider for long-running operations (bulk imports)

### D. Generic Service Base Class
**Considered** ✓

Create ServiceBase with common patterns:
```python
class ExternalServiceBase:
    def _execute_request(self, method, url, **kwargs):
        # Handle auth, rate limit, retry, circuit breaker
```

**Status**: Partially implemented (error handling, logging patterns)
**Gap**: SpotifyService and DiscogsService have unique auth, left as-is
**Improvement**: Could extract common patterns in Phase 5+

## 5. Implementation Plan

### Phase 5 (Current)
- ✅ Document architecture decision (this ADR)
- 🔄 Create API-specific integration guides
- 🔄 Improve error messages with fallback hints
- 🔄 Add integration tests for happy path

### Phase 5+
- Add request/response logging at DEBUG level
- Implement EurIA SSE streaming error handling
- Add metrics for API call success rates
- Create monitoring/alerting dashboards

### Future (Phase 6+)
- Consider Celery for long-running imports
- Add rate limit telemetry
- Implement advanced caching (Redis)
- Service mesh integration if scaling

## 6. References

### Code Files
- [SpotifyService](../../backend/app/services/spotify_service.py)
- [DiscogsService](../../backend/app/services/discogs_service.py)
- [EuriaService](../../backend/app/services/euria_service.py)
- [Exception Classes](../../backend/app/core/exceptions.py)
- [Retry Logic](../../backend/app/core/retry.py)

### Documentation
- [ADR-003: Circuit Breaker Pattern](./ADR-003-CIRCUIT-BREAKER.md)
- [ADR-001: Type Hints](./ADR-001-TYPE-HINTS.md)
- [Phase 4 Final Status](../PHASE4-FINAL-STATUS.txt)

### External Resources
- [Spotify Web API Authentication](https://developer.spotify.com/documentation/general/guides/authorization/)
- [Discogs API Rate Limits](https://www.discogs.com/developers/)
- [HTTP Status Codes](https://httpwg.org/specs/rfc7231.html#status.codes)
- [Retry Strategies](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

### Related ADRs
- ADR-003: Circuit Breaker & Error Handling
- ADR-005: Database Design (for caching schemas)
- ADR-008: Logging & Observability (for request logging)

## 7. Decision Trail

**Version 1.0 (2026-02-07)**: Initial decision on service-per-API pattern with unified error handling

---

**Status**: ✅ **ACCEPTED**

This pattern improves upon initial ad-hoc integration, providing resilience, testability, and consistency across all external API interactions.

**Next Decision**: ADR-005 (Database Design & ORM Usage)
