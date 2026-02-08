"""Server-Sent Event (SSE) streaming dialog and response handling.

Provides unified SSE chunk formatting for streaming endpoints (articles,
magazine generation, long-running operations). Supports progress tracking,
metadata delivery, data chunks, and error reporting in streaming context.

Key Functions:
- create_sse_chunk(): Low-level SSE formatting with event type
- create_streaming_response(): Wrap async generator in StreamingResponse
- create_sse_progress_chunk(): Progress percentage updates
- create_sse_message_chunk(): Status/log messages during streaming
- create_sse_data_chunk(): Streaming data delivery
- create_sse_done_chunk(): Stream completion signal
- create_sse_error_chunk(): Error reporting in-flight
- SSEStreamBuilder: Fluent API for building complex streams

Architecture:
- All chunks use consistent JSON format: {type, ...payload}
- SSE headers: Cache-Control, Connection, X-Accel-Buffering
- Proper nginx/proxy tunnel configuration for streaming
- Event IDs for client-side tracking and reconnection

Used By:
- Article streaming endpoints
- Magazine generation progress
- Long-running operation tracking
- Real-time data delivery (search results, etc.)
"""

import json
from typing import Dict, Any, Optional
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)


def create_sse_chunk(
    event_type: str,
    data: Dict[str, Any],
    event_id: Optional[str] = None
) -> str:
    """Create formatted Server-Sent Event chunk with optional event ID.
    
    Low-level SSE chunk constructor. All streaming functions use this.
    
    Args:
        event_type: Event classification (message, progress, data, done, error, metadata)
        data: Event payload dict (automatically adds "type" key)
        event_id: Optional event ID for client-side reconnection tracking
    
    Returns:
        Formatted SSE string: "id: {id}\\ndata: {...json...}\\n\\n" (if ID provided)
                             "data: {...json...}\\n\\n" (if no ID)
    
    Example:
        >>> chunk = create_sse_chunk("progress", {"current": 50, "total": 100})
        >>> print(chunk)
        >>> # data: {"type":"progress","current":50,"total":100}\\n\\n
        
        >>> chunk_with_id = create_sse_chunk("data", {"album": "Dark Side"},
        ...                                  event_id="msg-1")
        >>> print(chunk_with_id)
        >>> # id: msg-1\\ndata: {"type":"data","album":"Dark Side"}\\n\\n
    
    SSE Format Details:
        - "type" key added automatically to data dict
        - JSON-encoded on single "data: " line
        - Terminated with blank line (\\n\\n)
        - Optional "id: " line for event tracking
    
    Performance:
        O(1) - simple dict/JSON operations
    
    Note:
        Event IDs allow clients to resume after disconnect using Last-Event-ID
        Useful for long-running streams that may experience network hiccups
    """
    chunk = {"type": event_type, **data}
    sse_line = f"data: {json.dumps(chunk)}\n\n"
    
    if event_id:
        sse_line = f"id: {event_id}\n{sse_line}"
    
    return sse_line


def create_streaming_response(
    generator,
    media_type: str = "text/event-stream"
) -> StreamingResponse:
    """Create FastAPI StreamingResponse with SSE-specific headers.
    
    Wraps async generator in StreamingResponse with proper cache control,
    connection persistence, and nginx/proxy configuration.
    
    Args:
        generator: Async generator yielding SSE chunk strings
        media_type: Media type (default "text/event-stream" for SSE)
    
    Returns:
        StreamingResponse with SSE headers configured
    
    Example:
        >>> async def stream_progress():
        ...     yield create_sse_progress_chunk(0, 100)
        ...     for i in range(1, 101):
        ...         yield create_sse_progress_chunk(i, 100)
        ...     yield create_sse_done_chunk()
        
        >>> @app.get("/generate")
        ... async def generate():
        ...     return create_streaming_response(stream_progress())
    
    Headers Set:
        - Cache-Control: no-cache (prevent proxy caching)
        - Connection: keep-alive (maintain TCP connection)
        - X-Accel-Buffering: no (disable nginx buffering)
        - Content-Encoding: none (raw SSE, not gzip)
    
    Performance:
        O(1) - wraps existing generator
    
    Used By:
        All streaming endpoints (articles, magazine generation, etc.)
        Ensures consistent SSE configuration across API
    
    Note:
        Generator should yield SSE chunks (not raw data)
        Use helper functions (create_sse_progress_chunk, etc.) to generate chunks
    """
    return StreamingResponse(
        generator,
        media_type=media_type,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Content-Encoding": "none"
        }
    )


def create_sse_progress_chunk(
    current: int,
    total: int,
    message: str = "",
    percent: Optional[int] = None
) -> str:
    """Create progress event chunk for progress bar UI updates.
    
    Sends current/total progress with auto-calculated or manual percent.
    
    Args:
        current: Current progress count (e.g., items processed so far)
        total: Total count to complete (e.g., total items)
        message: Optional progress message (e.g., current item name)
        percent: Optional override percentage (calculated if not provided)
    
    Returns:
        Formatted SSE progress chunk
    
    Example:
        >>> for i in range(initial, total + 1):
        ...     yield create_sse_progress_chunk(i, total, message=f"Processing item {i}")
        ...     # Yields: data: {"type":"progress","current":1,"total":100,"percent":1,"message":"Processing item 1"}\\n\\n
    
    Auto-Calculation:
        If percent is None: percent = int((current / total * 100) if total > 0 else 0)
        Handles division by zero gracefully (returns 0%)
    
    Performance:
        O(1) - simple arithmetic
    
    Typical Use:
        Album enrichment (current album / total albums)
        Magazine page generation (current page / 5)
        File processing (current file / total files)
    """
    if percent is None:
        percent = int((current / total * 100) if total > 0 else 0)
    
    return create_sse_chunk("progress", {
        "current": current,
        "total": total,
        "percent": percent,
        "message": message
    })


def create_sse_message_chunk(message: str, level: str = "info") -> str:
    """Create message event chunk for status/log messages during streaming.
    
    Logs informational, warning, or error messages to client during long operations.
    
    Args:
        message: Message text to display
        level: Message level: "info" (default), "warning", "error"
    
    Returns:
        Formatted SSE message chunk
    
    Example:
        >>> async def stream_generation():
        ...     yield create_sse_message_chunk("Starting article generation", "info")
        ...     yield create_sse_message_chunk("No images found for artist", "warning")
        ...     # Client displays messages in real-time during operation
    
    Levels:
        "info": Informational (default, blue/info color)
        "warning": Warning (yellow/warning color)
        "error": Error (red/error color)
    
    Performance:
        O(1) - simple JSON encoding
    
    Used By:
        Magazine generation (status updates)
        Article generation (processing notes)
        Album enrichment (skipped items, etc.)
    """
    return create_sse_chunk("message", {
        "level": level,
        "text": message
    })


def create_sse_data_chunk(data: Dict[str, Any], chunk_id: Optional[str] = None) -> str:
    """Create data event chunk for streaming result items.
    
    Primary mechanism for sending streaming result data to client.
    Each item (album, article, track, etc.) sent as separate data chunk.
    
    Args:
        data: Data dict to send (album info, article chunk, etc.)
        chunk_id: Optional chunk identifier for deduplication/tracking
    
    Returns:
        Formatted SSE data chunk (with optional ID for reconnection)
    
    Example:
        >>> for album in albums:
        ...     yield create_sse_data_chunk(album.to_dict(), chunk_id=f"album-{album.id}")
        ...     # Client receives each album immediately
    
    Use Cases:
        - Album search results (one chunk per album)
        - Article generation (one chunk per paragraph)
        - Data enrichment (one chunk per enriched item)
    
    Performance:
        O(1) - simple JSON encoding
    
    Note:
        Optional chunk_id enables client to resume from specific item
        if connection drops mid-stream
    """
    return create_sse_chunk("data", data, event_id=chunk_id)


def create_sse_done_chunk(summary: Optional[Dict[str, Any]] = None) -> str:
    """Create completion event chunk to signal end of stream.
    
    Sent as final chunk to close streaming operation gracefully.
    Client stops listening for new events after receiving "done".
    
    Args:
        summary: Optional summary dict (item count, duration, etc.)
    
    Returns:
        Formatted SSE done chunk
    
    Example:
        >>> async def stream_albums():
        ...     for album in albums:
        ...         yield create_sse_data_chunk(album.to_dict())
        ...     # Signal completion
        ...     yield create_sse_done_chunk({"total": len(albums), "duration_ms": 1234})
    
    Summary Data:
        Optional dict with operation results/statistics
        Common fields: total, duration_ms, errors, skipped, etc.
    
    Performance:
        O(1) - simple JSON encoding
    
    Note:
        MUST be sent last - client stops receiving after done event
        Always use with async generators to avoid hanging connections
    """
    data = {}
    if summary:
        data.update(summary)
    
    return create_sse_chunk("done", data)


def create_sse_error_chunk(
    error_message: str,
    error_type: str = "error",
    error_code: Optional[str] = None
) -> str:
    """Create error event chunk for in-flight error reporting.
    
    Sends error during streaming operation without closing stream.
    Allows operation to continue or gracefully terminate with context.
    
    Args:
        error_message: Human-readable error message
        error_type: Error classification (error, validation, service, etc.)
        error_code: Optional error code for client handling (e.g., "ALBUM_NOT_FOUND")
    
    Returns:
        Formatted SSE error chunk
    
    Example:
        >>> try:
        ...     yield create_sse_data_chunk(item)
        ... except Exception as e:
        ...     yield create_sse_error_chunk(str(e), "processing_error", "ITEM_INVALID")
        ...     yield create_sse_done_chunk({"errors": 1})
    
    Difference from create_error_dialog():
        - create_error_dialog(): HTTP exception (immediate response end)
        - create_sse_error_chunk(): In-stream error (stream continues)
    
    Performance:
        O(1) - simple JSON encoding
    
    Used By:
        Long-running operations where single items may fail
        Magazine generation (artist enrichment failures)
        Album search (some results unavailable)
    """
    data = {
        "message": error_message,
        "error_type": error_type
    }
    
    if error_code:
        data["error_code"] = error_code
    
    return create_sse_chunk("error", data)


class SSEStreamBuilder:
    """Fluent builder class for constructing complex SSE streams.
    
    Method-chaining interface for building multi-chunk streams programmatically.
    Accumulates chunks and yields them as async generator.
    
    Use Cases:
        - Multi-step operations (metadata → progress → data → done)
        - Conditional chunk inclusion based on results
        - Complex stream orchestration with error handling
    
    Example:
        >>> builder = SSEStreamBuilder()
        >>> (builder
        ...     .add_metadata(title="Album Details", image_url="...")
        ...     .add_message("Loading tracks...", "info")
        ...     .add_progress(0, 100, "Start"))
        >>> for i, track in enumerate(tracks):
        ...     builder.add_progress(i+1, 100, f"Track {i+1}")
        ...     builder.add_data(track.to_dict())
        >>> builder.done({"total": len(tracks)})
        >>> response = builder.get_response()
        >>> # Returns StreamingResponse with all accumulated chunks
    
    Methods:
        - add_metadata(): Add resource metadata (title, image, etc.)
        - add_message(): Add status message (info/warning/error level)
        - add_progress(): Add progress update (current/total/percent)
        - add_data(): Add data chunk (single result item)
        - add_error(): Add error chunk (per-item error)
        - done(): Add completion signal with summary
        - stream(): Async generator yielding all chunks
        - get_response(): Wrap in StreamingResponse with SSE headers
    
    Performance:
        - accumulation: O(1) per method call (append to list)
        - stream(): O(n) where n = number of chunks
        - get_response(): O(1) wrapper
    
    Note:
        Always call done() before get_response() to signal stream end
        Fluent interface (each method returns self) enables chaining
    """
    
    def __init__(self):
        """Initialize empty chunk list for accumulation."""
        self.chunks = []
    
    def add_metadata(self, **metadata) -> "SSEStreamBuilder":
        """Add metadata chunk (title, image, etc).
        
        Args:
            **metadata: Arbitrary metadata dict (title, image_url, etc.)
        
        Returns:
            Self for method chaining
        """
        self.chunks.append(create_sse_chunk("metadata", metadata))
        return self
    
    def add_message(self, message: str, level: str = "info") -> "SSEStreamBuilder":
        """Add status/log message chunk.
        
        Args:
            message: Message text
            level: "info" (default), "warning", "error"
        
        Returns:
            Self for method chaining
        """
        self.chunks.append(create_sse_message_chunk(message, level))
        return self
    
    def add_progress(self, current: int, total: int, message: str = "") -> "SSEStreamBuilder":
        """Add progress update chunk.
        
        Args:
            current: Current count
            total: Total count
            message: Optional progress message
        
        Returns:
            Self for method chaining
        """
        self.chunks.append(create_sse_progress_chunk(current, total, message))
        return self
    
    def add_data(self, data: Dict[str, Any]) -> "SSEStreamBuilder":
        """Add data chunk for result item.
        
        Args:
            data: Item dict to send
        
        Returns:
            Self for method chaining
        """
        self.chunks.append(create_sse_data_chunk(data))
        return self
    
    def add_error(self, message: str, error_type: str = "error") -> "SSEStreamBuilder":
        """Add error chunk for per-item error.
        
        Args:
            message: Error message
            error_type: Error classification
        
        Returns:
            Self for method chaining
        """
        self.chunks.append(create_sse_error_chunk(message, error_type))
        return self
    
    def done(self, summary: Optional[Dict[str, Any]] = None) -> "SSEStreamBuilder":
        """Add completion signal with optional summary.
        
        Args:
            summary: Optional summary dict (count, errors, duration, etc.)
        
        Returns:
            Self for method chaining
        """
        self.chunks.append(create_sse_done_chunk(summary))
        return self
    
    async def stream(self):
        """Async generator yielding all accumulated chunks.
        
        Yields:
            SSE chunk strings (newline-terminated)
        """
        for chunk in self.chunks:
            yield chunk
    
    def get_response(self) -> StreamingResponse:
        """Wrap accumulated chunks in StreamingResponse with SSE headers.
        
        Returns:
            StreamingResponse ready to return from FastAPI endpoint
        
        Note:
            Always call done() before get_response() to signal completion
        """
        return create_streaming_response(self.stream())\n