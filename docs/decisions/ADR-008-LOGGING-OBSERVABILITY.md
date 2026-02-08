# ADR-008: Logging & Observability

**Status**: ✅ Accepted  
**Date**: 2026-02-07  
**Priority**: Medium  
**Author**: Engineering Team  
**Reviewers**: Architecture Committee  

## 1. Context

AIME needs visibility into runtime behavior across three environments (dev/staging/prod):

### 1.1 Observability Needs

**Debugging**:
- What happened during a failed import?
- Why did Spotify integration stop working?
- Which query was slow?

**Monitoring**:
- Is the application healthy?
- How many requests/day?
- What's the error rate?

**Alerting**:
- Alert on too many failures
- Alert when rate limits hit
- Alert on slow responses

**Compliance**:
- Audit trail for data access
- User activity log
- Security event tracking

### 1.2 Current Challenges

1. **Unstructured Logging**
   - Mix of print() and logging.info()
   - No consistent format
   - Secrets sometimes logged by accident

2. **No Centralized Logging**
   - Logs scattered across files
   - No search capability
   - No log retention policy

3. **Missing Correlation**
   - Can't trace request through async tasks
   - No parent-child relationship for related events

4. **No Metrics/Monitoring**
   - No request count/latency tracking
   - No resource usage monitoring
   - No integration with monitoring tools

**Problem**: How to provide comprehensive visibility into application behavior for debugging, monitoring, and compliance?

## 2. Decision

We adopt **structured logging with context propagation** and **basic metrics collection**.

### 2.1 Logging Infrastructure

```python
# Pattern: backend/app/core/logging_config.py

import logging
import json
from datetime import datetime
from typing import Dict, Any
import uuid

# ============ Structured Logging ============

class JSONFormatter(logging.Formatter):
    """
    Format logs as JSON for easy parsing and searching.
    
    Single-line JSON format:
    {"timestamp": "...", "level": "INFO", "logger": "aime.services", 
     "message": "...", "request_id": "...", "duration_ms": 123}
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Convert log record to JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

class ContextFilter(logging.Filter):
    """
    Add request context to all log records.
    
    Allow passing request_id, user_id, etc. through async calls.
    """
    
    def __init__(self):
        super().__init__()
        self.context = {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context fields to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True
    
    def set_context(self, **kwargs):
        """Set context fields."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all context."""
        self.context.clear()

# Global context filter
context_filter = ContextFilter()

def setup_logging(app_name: str, log_level: str, log_file: str) -> None:
    """
    Configure logging for the application.
    
    Sets up:
    - Console output (all messages)
    - File output (with rotation)
    - JSON formatting for structured logs
    - Request context propagation
    """
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(context_filter)
    root_logger.addHandler(console_handler)
    
    # File handler (JSON for parsing)
    from logging.handlers import RotatingFileHandler
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10_485_760,  # 10MB
        backupCount=5  # Keep 5 old files
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    file_handler.addFilter(context_filter)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# Convenience function
def get_logger(name: str) -> logging.LoggerAdapter:
    """Get logger for a module."""
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, {})
```

### 2.2 Request Context Propagation

```python
# Pattern: Trace requests through async calls

import contextvars
from fastapi import Request, FastAPI
from uuid import uuid4

# Create context variable for request ID
request_id_var = contextvars.ContextVar("request_id", default=None)
user_id_var = contextvars.ContextVar("user_id", default=None)

@app.middleware("http")
async def add_request_context(request: Request, call_next):
    """
    Add request context (ID, user) to all logs.
    
    Allow async tasks spawned from this request to
    inherit the same request_id for correlation.
    """
    
    # Generate or extract request ID
    request_id = str(uuid4())
    
    # Extract user ID from JWT token if available
    user_id = None
    try:
        # Decode JWT token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
            user_id = payload.get("sub")
    except:
        pass
    
    # Set context variables for this request
    request_id_var.set(request_id)
    user_id_var.set(user_id)
    
    # Add to request object for easy access
    request.state.request_id = request_id
    request.state.user_id = user_id
    
    # Set filter context
    context_filter.set_context(request_id=request_id, user_id=user_id)
    
    # Process request
    response = await call_next(request)
    
    # Add request ID to response headers (for client-side logging)
    response.headers["X-Request-ID"] = request_id
    
    # Clear context
    context_filter.clear_context()
    
    return response

# Helper to get context in any async function
def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_var.get() or "unknown"

def get_user_id() -> Optional[int]:
    """Get current user ID from context."""
    return user_id_var.get()

# Usage in service
logger = get_logger(__name__)

async def import_album(album_id: str) -> Album:
    """Import album with context in logs."""
    request_id = get_request_id()
    user_id = get_user_id()
    
    start = time.time()
    
    logger.info(
        f"Starting album import",
        extra={"album_id": album_id}
    )
    
    try:
        album = await spotify_service.get_album(album_id)
        duration_ms = (time.time() - start) * 1000
        
        logger.info(
            f"Album imported successfully",
            extra={
                "album_id": album_id,
                "album_title": album.title,
                "duration_ms": int(duration_ms)
            }
        )
        return album
    
    except Exception as e:
        logger.error(
            f"Album import failed: {e}",
            extra={"album_id": album_id},
            exc_info=True  # Include stack trace
        )
        raise
```

### 2.3 Logging Levels & Guidelines

```python
# Pattern: Appropriate log levels for different scenarios

logger = get_logger(__name__)

# ✅ DEBUG: Detailed info for developers
logger.debug(f"Query parameters: user_id={user_id}, skip={skip}, limit={limit}")
logger.debug(f"Cache hit for key: {cache_key}")

# ✅ INFO: Important business events
logger.info(f"Album imported: {album_title} by {artist_name}")
logger.info(f"User logged in: {user_id}")
logger.info(f"Batch import completed: {count} albums")

# ⚠️ WARNING: Unexpected but recoverable errors
logger.warning(f"Spotify rate limit hit, retrying in {retry_after}s")
logger.warning(f"Missing album cover image for {album_id}")
logger.warning(f"Database query slow: {duration_ms}ms (expected <100ms)")

# ❌ ERROR: Errors that need investigation but service continues
logger.error(f"Failed to enrich album with AI description: {error}")
logger.error(f"Invalid token format in Authorization header")
logger.error(f"Database connection pool exhausted (max 5 connections)")

# 🚨 CRITICAL: Service-wide failures, immediate action needed
logger.critical(f"Database connection lost, unable to recover")
logger.critical(f"JWT secret not configured, authentication impossible")
logger.critical(f"Out of memory, terminating")
```

### 2.4 Performance Metrics & Timing

```python
# Pattern: Log performance metrics for monitoring

import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def timed_operation(operation_name: str):
    """
    Context manager that logs execution time.
    
    Usage:
        async with timed_operation("import_album"):
            # Do work
    """
    start = time.time()
    logger = get_logger(__name__)
    
    try:
        yield
    finally:
        duration_ms = (time.time() - start) * 1000
        logger.info(
            f"{operation_name} completed",
            extra={"duration_ms": int(duration_ms)}
        )

# Usage in routes
@app.get("/albums")
async def list_albums(skip: int = 0, limit: int = 20):
    """List albums with timing logs."""
    async with timed_operation("list_albums"):
        albums = await album_service.list_albums(skip, limit)
    return albums

# In service methods
async def import_from_spotify(self, user_id: int) -> int:
    """Import albums with detailed timing."""
    logger = get_logger(__name__)
    
    async with timed_operation("spotify_auth"):
        token = await self.get_spotify_token(user_id)
    
    async with timed_operation("spotify_fetch"):
        tracks = await self.fetch_user_tracks(token)
    
    logger.info(f"Fetched {len(tracks)} tracks from Spotify")
    
    async with timed_operation("database_save"):
        count = await self.save_albums(tracks, user_id)
    
    logger.info(f"Saved {count} albums to database")
    return count
```

### 2.5 Sensitive Data Masking

```python
# Pattern: Never log secrets or sensitive data

def mask_key(key: str, visible_chars: int = 4) -> str:
    """
    Mask API key showing only first/last chars.
    
    Examples:
        mask_key("spotify-abc123def456") -> "spotify-...f456"
        mask_key("secret-key") -> "secr...3-key"
    """
    if len(key) <= visible_chars * 2:
        return "*" * len(key)
    
    return key[:visible_chars] + "..." + key[-visible_chars:]

# Usage
api_key = "my-secret-spotify-key-12345"
logger.debug(f"Using API key: {mask_key(api_key)}")
# Output: "Using API key: my-s...2345"

# ❌ WRONG: Never log full secrets
logger.info(f"Spotify client secret: {client_secret}")  # NEVER!

# ✅ CORRECT: Mask sensitive data
logger.info(f"Spotify client ID: {client_id}")  # Safe, not secret
logger.debug(f"Spotify secret: {mask_key(client_secret)}")  # Masked

# For passwords/tokens, log nothing specific
if auth_failed:
    logger.warning(f"Authentication failed for user {user_id}")  # Safe
    # logger.warning(f"Invalid password: {password}")  # NEVER!
```

### 2.6 Testing & Log Assertions

```python
# Pattern: Verify logs in tests

import pytest
from unittest.mock import patch
import logging

@pytest.mark.asyncio
async def test_album_import_logs_success(test_settings):
    """Verify success is logged correctly."""
    
    with patch("app.services.album.logger") as mock_logger:
        service = AlbumService()
        album = await service.import_album("spotify:123")
        
        # Assert expected log calls
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "imported successfully" in call_args[0][0]
        assert call_args[1]["extra"]["album_id"] == "spotify:123"

@pytest.mark.asyncio
async def test_album_import_logs_error(test_settings):
    """Verify error is logged with stack trace."""
    
    with patch("app.services.album.logger") as mock_logger:
        with patch.object(SpotifyService, "get_album") as mock_spotify:
            mock_spotify.side_effect = Exception("Rate limited")
            
            service = AlbumService()
            with pytest.raises(Exception):
                await service.import_album("spotify:123")
            
            # Assert error was logged with exc_info
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert call_args[1]["exc_info"] is True
```

## 3. Consequences

### 3.1 ✅ Positive

1. **Debugging**: Structured logs make root cause analysis easier
2. **Searchability**: JSON logs can be searched/filtered in log aggregation tools
3. **Context Propagation**: Request ID ties related logs together
4. **Performance Visibility**: Timing logs show slow operations
5. **Security**: Masking prevents secret leaks
6. **Compliance**: Audit trail of important operations

### 3.2 ⚠️ Trade-offs

1. **Log Volume**: More logging = more data storage
   - **Mitigation**: Use appropriate log levels, compress old logs

2. **Performance Overhead**: Extra work to format/write logs
   - **Mitigation**: Async handlers, batch writing

3. **Context Variable Complexity**: ContextVars add conceptual overhead
   - **Mitigation**: Wrapper functions hide complexity

### 3.3 Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Logger setup | ✅ Done | logging module configured |
| JSON formatting | 🟡 Partial | Basic JSON formatter, needs testing |
| Request context | ✅ Done | Middleware captures request_id/user_id |
| Log levels | ✅ Done | Guidelines established |
| Masking | 🟡 Partial | Template provided, needs integration |
| Tests | ✅ Done | pytest fixtures for log mocking |

## 4. Alternatives Considered

### A. Print-Based Logging
**Rejected** ❌

```python
print(f"[INFO] Album imported: {title}")
```

**Why Not**: No timestamps, no levels, no filtering, no structure

### B. Cloud Logging Service (CloudWatch, Stackdriver)
**Considered for Phase 6+** ⏳

Direct integration with cloud provider logging

**Status**: Out of scope for Phase 5
**When**: When deployed to AWS/GCP

### C. Distributed Tracing (Jaeger, Zipkin)
**Considered for Future** ⏳

Full request tracing across services

**Status**: Not needed yet (single monolithic app)
**When**: If/when microservices introduced

## 5. Implementation Plan

### Phase 4 (Completed)
- ✅ Basic logging setup
- ✅ Log level configuration

### Phase 5 (Current)
- 🔄 Structured JSON logging (this ADR)
- 🔄 Request context propagation
- 🔄 Timing instrumentation
- 🔄 Sensitive data masking

### Phase 5+
- Add log aggregation (ELK or Cloud Logging)
- Setup log retention policies
- Create log analysis dashboards
- Implement log-based alerting

## 6. Log Examples

**Success Case**:
```json
{"timestamp": "2026-02-07T10:15:30Z", "level": "INFO", "logger": "aime.services.album", 
 "message": "Album imported successfully", "request_id": "req-123", "user_id": 42, 
 "album_id": "spotify:123", "album_title": "The Wall", "duration_ms": 245}
```

**Error Case**:
```json
{"timestamp": "2026-02-07T10:16:45Z", "level": "ERROR", "logger": "aime.services.spotify",
 "message": "Spotify API request failed", "request_id": "req-123", "user_id": 42,
 "duration_ms": 5000, "status_code": 429, "exception": "RateLimitExceeded..."}
```

## 7. References

### Code Files
- [Logging config](../../backend/app/core/logging_config.py)
- [Request context](../../backend/app/middleware/context.py)

### Documentation
- [ADR-007: Configuration Management](./ADR-007-CONFIGURATION-MANAGEMENT.md)

### External Resources
- [Python logging docs](https://docs.python.org/3/library/logging.html)
- [Structured logging guide](https://kartar.net/2015/12/structured-logging/)
- [Context variables in Python](https://docs.python.org/3/library/contextvars.html)

### Related ADRs
- ADR-007: Configuration Management (log config)
- ADR-006: Async Patterns (async logging)

## 8. Decision Trail

**Version 1.0 (2026-02-07)**: Initial decision on structured JSON logging with context propagation

---

**Status**: ✅ **ACCEPTED**

This approach provides visibility into application behavior while maintaining security and performance.

**Next Decision**: ADR-009 (Caching Strategy)
