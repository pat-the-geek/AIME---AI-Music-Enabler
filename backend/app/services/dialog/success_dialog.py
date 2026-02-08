"""Unified success response handling and success dialogs.

Provides consistent success response formatting across all API endpoints.
Supports standard operations (create, read, update, delete, list) and
Server-Sent Event chunks for streaming responses.

Key Functions:
- create_success_response(): Low-level success dict construction
- create_success_dialog(): UI-ready success dialog with title/message
- create_created_response(): 201 Created responses
- create_updated_response(): 200 OK for updates
- create_deleted_response(): 200 OK for deletes
- create_list_response(): Paginated list responses
- create_sse_success_chunk(): Success chunks for streaming
- create_sse_metadata_chunk(): Resource metadata chunks

Architecture:
- All successes use consistent dict format: status, message, status_code, data, metadata
- Status codes: 200 (OK), 201 (Created)
- Metadata includes pagination info (count, limit, offset, has_more)
- SSE chunks for real-time streaming responses

Used By:
- API route handlers for consistent success responses
- Streaming endpoints for in-flight data delivery
- CRUD endpoints for standard response formatting
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def create_success_response(
    data: Any,
    message: str = "Success",
    status_code: int = 200,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized success response dict with consistent structure.
    
    Low-level success dict constructor used by all success functions.
    Ensures all successful API responses follow identical JSON format.
    
    Args:
        data: Response payload (list, dict, single object, or any JSON-serializable)
        message: Human-readable success message (default Success)
        status_code: HTTP status code: 200 (OK) or 201 (Created)
        metadata: Optional dict with pagination or operation info
    
    Returns:
        Dict with keys: status=success, message, status_code, data, metadata (optional)
    
    Performance:
        O(1) - simple dict construction
    """
    response = {
        "status": "success",
        "message": message,
        "status_code": status_code,
        "data": data
    }
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def create_success_dialog(
    title: str,
    message: str,
    action_url: Optional[str] = None
) -> Dict[str, Any]:
    """Create success dialog dict for frontend UI display.
    
    Formats success notification for display in UI toast/modal.
    Includes auto-dismiss timeout and optional action button.
    
    Args:
        title: Dialog title (short, 2-5 words recommended)
        message: Dialog content message (user-friendly text)
        action_url: Optional URL to navigate on action button click
    
    Returns:
        Dict with keys: type=success_dialog, title, message, action_url, duration=3000
    
    UI Behavior:
        - Displays for 3000ms (3 seconds) before auto-dismiss
        - Optional action button with action_url navigation
        - Non-blocking (doesn't prevent user interaction)
    
    Performance:
        O(1) - simple dict construction
    """
    return {
        "type": "success_dialog",
        "title": title,
        "message": message,
        "action_url": action_url,
        "duration": 3000  # milliseconds
    }


def create_created_response(resource: str, data: Any, resource_id: Any) -> Dict[str, Any]:
    """Create 201 Created response for new resource creation.
    
    Convenience function for POST/create endpoints.
    Returns resource data with 201 status and created_id in metadata.
    
    Args:
        resource: Resource type name (Album, Playlist, Collection, etc.)
        data: Created resource data
        resource_id: ID of newly created resource
    
    Returns:
        Dict with status=success, status_code=201, metadata={created_id: resource_id}
    
    Performance:
        O(1) - simple dict construction
    """
    return create_success_response(
        data=data,
        message=f"{resource} created successfully",
        status_code=201,
        metadata={"created_id": resource_id}
    )


def create_updated_response(resource: str, data: Any) -> Dict[str, Any]:
    """Create 200 OK response for successful resource update.
    
    Convenience function for PUT/PATCH update endpoints.
    Returns updated resource data with success status.
    
    Args:
        resource: Resource type name (Album, Playlist, etc.)
        data: Updated resource data
    
    Returns:
        Dict with status=success, status_code=200
    
    Performance:
        O(1) - simple dict construction
    """
    return create_success_response(
        data=data,
        message=f"{resource} updated successfully"
    )


def create_deleted_response(resource: str, resource_id: Any) -> Dict[str, Any]:
    """Create 200 OK response for successful resource deletion.
    
    Convenience function for DELETE endpoints.
    Returns confirmation with deleted resource ID.
    
    Args:
        resource: Resource type name (Album, Playlist, etc.)
        resource_id: ID of deleted resource
    
    Returns:
        Dict with status=success, message={resource} deleted successfully
    
    Performance:
        O(1) - simple dict construction
    """
    return create_success_response(
        data={"deleted_id": resource_id},
        message=f"{resource} deleted successfully"
    )


def create_list_response(items: list, count: int, limit: int, offset: int) -> Dict[str, Any]:
    """Create 200 OK response for paginated list results.
    
    Standard paginated response with offset/limit pagination info.
    Calculates has_more flag for infinite scroll UI patterns.
    
    Args:
        items: List of items to return
        count: Total number of items matching query
        limit: Items per page
        offset: Starting position in result set (0-indexed)
    
    Returns:
        Dict with status=success, data=items, metadata={count, limit, offset, has_more}
    
    Pagination Logic:
        has_more = (offset + limit) < count
    
    Performance:
        O(1) - simple calculation
    """
    return create_success_response(
        data=items,
        message="List retrieved successfully",
        metadata={
            "count": count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < count
        }
    )


def create_sse_success_chunk(data: Dict[str, Any]) -> str:
    """Create Server-Sent Event success chunk for streaming responses.
    
    Formats success data for delivery in SSE stream.
    
    Args:
        data: Success data dict to transmit
    
    Returns:
        Formatted SSE chunk: "data: {...json...}\\n\\n"
    
    Performance:
        O(1) - simple JSON encoding
    """
    import json
    chunk = {"type": "success", **data}
    return f"data: {json.dumps(chunk)}\n\n"


def create_sse_metadata_chunk(
    title: str,
    subtitle: Optional[str] = None,
    image_url: Optional[str] = None,
    **kwargs
) -> str:
    """Create Server-Sent Event metadata chunk for streaming responses.
    
    Sends resource metadata (title, image, etc.) in SSE stream.
    Used to display resource info while data streams in.
    
    Args:
        title: Resource title (Album, Artist, Playlist name)
        subtitle: Optional subtitle (Artist name, description)
        image_url: Optional image URL (album art, artist photo)
        **kwargs: Additional arbitrary metadata fields
    
    Returns:
        Formatted SSE chunk: "data: {...json...}\\n\\n"
    
    UI Pattern:
        Displays metadata immediately (header/cover image)
        while data/tracks load in background
    
    Performance:
        O(1) - simple JSON encoding
    """
    import json
    metadata = {
        "type": "metadata",
        "title": title,
        "subtitle": subtitle,
        "image_url": image_url,
        **kwargs
    }
    return f"data: {json.dumps(metadata)}\n\n"
