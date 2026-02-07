"""Server-Sent Event (SSE) streaming dialog handling."""

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
    """
    Create a formatted Server-Sent Event chunk.
    
    Args:
        event_type: Type of event (e.g., 'message', 'progress', 'complete', 'error')
        data: Event data
        event_id: Optional event ID for client-side tracking
        
    Returns:
        Formatted SSE chunk
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
    """
    Create a StreamingResponse with proper SSE headers.
    
    Args:
        generator: Async generator yielding SSE chunks
        media_type: Media type (default: text/event-stream)
        
    Returns:
        StreamingResponse with proper SSE configuration
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
    """
    Create a progress event chunk.
    
    Args:
        current: Current progress count
        total: Total count
        message: Progress message
        percent: Optional manual percentage
        
    Returns:
        Formatted SSE progress chunk
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
    """
    Create a message event chunk.
    
    Args:
        message: Message text
        level: Message level ('info', 'warning', 'error')
        
    Returns:
        Formatted SSE message chunk
    """
    return create_sse_chunk("message", {
        "level": level,
        "text": message
    })


def create_sse_data_chunk(data: Dict[str, Any], chunk_id: Optional[str] = None) -> str:
    """
    Create a data event chunk.
    
    Args:
        data: Data to send
        chunk_id: Optional chunk identifier
        
    Returns:
        Formatted SSE data chunk
    """
    return create_sse_chunk("data", data, event_id=chunk_id)


def create_sse_done_chunk(summary: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a completion event chunk.
    
    Args:
        summary: Optional summary data
        
    Returns:
        Formatted SSE done chunk
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
    """
    Create an error event chunk.
    
    Args:
        error_message: Error message
        error_type: Error type
        error_code: Optional error code
        
    Returns:
        Formatted SSE error chunk
    """
    data = {
        "message": error_message,
        "error_type": error_type
    }
    
    if error_code:
        data["error_code"] = error_code
    
    return create_sse_chunk("error", data)


class SSEStreamBuilder:
    \"\"\"Helper class for building SSE streams.\"\"\"\n    \n    def __init__(self):\n        self.chunks = []\n    \n    def add_metadata(self, **metadata) -> \"SSEStreamBuilder\":\n        \"\"\"Add metadata chunk.\"\"\"\n        self.chunks.append(create_sse_chunk(\"metadata\", metadata))\n        return self\n    \n    def add_message(self, message: str, level: str = \"info\") -> \"SSEStreamBuilder\":\n        \"\"\"Add message chunk.\"\"\"\n        self.chunks.append(create_sse_message_chunk(message, level))\n        return self\n    \n    def add_progress(self, current: int, total: int, message: str = \"\") -> \"SSEStreamBuilder\":\n        \"\"\"Add progress chunk.\"\"\"\n        self.chunks.append(create_sse_progress_chunk(current, total, message))\n        return self\n    \n    def add_data(self, data: Dict[str, Any]) -> \"SSEStreamBuilder\":\n        \"\"\"Add data chunk.\"\"\"\n        self.chunks.append(create_sse_data_chunk(data))\n        return self\n    \n    def add_error(self, message: str, error_type: str = \"error\") -> \"SSEStreamBuilder\":\n        \"\"\"Add error chunk.\"\"\"\n        self.chunks.append(create_sse_error_chunk(message, error_type))\n        return self\n    \n    def done(self, summary: Optional[Dict[str, Any]] = None) -> \"SSEStreamBuilder\":\n        \"\"\"Mark stream as done.\"\"\"\n        self.chunks.append(create_sse_done_chunk(summary))\n        return self\n    \n    async def stream(self):\n        \"\"\"Yield all chunks.\"\"\"\n        for chunk in self.chunks:\n            yield chunk\n    \n    def get_response(self) -> StreamingResponse:\n        \"\"\"Get streaming response.\"\"\"\n        return create_streaming_response(self.stream())\n