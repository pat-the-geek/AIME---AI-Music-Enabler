"""Unified success dialog and success response handling."""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def create_success_response(
    data: Any,
    message: str = "Success",
    status_code: int = 200,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code (200, 201, etc.)
        metadata: Additional metadata (count, page, etc.)
        
    Returns:
        Standardized success response dict
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
    """
    Create a success dialog for UI display.
    
    Args:
        title: Dialog title
        message: Dialog message
        action_url: Optional URL for action button
        
    Returns:
        Dialog object for frontend
    """
    return {
        "type": "success_dialog",
        "title": title,
        "message": message,
        "action_url": action_url,
        "duration": 3000  # milliseconds
    }


def create_created_response(resource: str, data: Any, resource_id: Any) -> Dict[str, Any]:
    """Create a resource created response (201)."""
    return create_success_response(
        data=data,
        message=f"{resource} created successfully",
        status_code=201,
        metadata={"created_id": resource_id}
    )


def create_updated_response(resource: str, data: Any) -> Dict[str, Any]:
    """Create a resource updated response."""
    return create_success_response(
        data=data,
        message=f"{resource} updated successfully"
    )


def create_deleted_response(resource: str, resource_id: Any) -> Dict[str, Any]:
    """Create a resource deleted response."""
    return create_success_response(
        data={"deleted_id": resource_id},
        message=f"{resource} deleted successfully"
    )


def create_list_response(items: list, count: int, limit: int, offset: int) -> Dict[str, Any]:
    """Create a list/paginated response."""
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
    """
    Create a Server-Sent Event chunk for success.
    
    Args:
        data: Data to send
        
    Returns:
        Formatted SSE success chunk
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
    """
    Create a Server-Sent Event chunk for metadata.
    
    Args:
        title: Resource title
        subtitle: Resource subtitle
        image_url: Resource image URL
        **kwargs: Additional metadata fields
        
    Returns:
        Formatted SSE metadata chunk
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
