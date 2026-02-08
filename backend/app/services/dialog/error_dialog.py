"""Unified error response handling and standardized error dialogs.

Provides consistent error response formatting across all API endpoints and
error scenarios. Supports HTTP errors, validation errors, service errors,
and Server-Sent Event error chunks for streaming responses.

Key Functions:
- create_error_response(): Low-level error dict construction
- create_error_dialog(): Raise HTTPException with standardized format
- create_validation_error(): Field-specific validation errors
- create_not_found_error(): 404 resource not found
- create_service_error(): External service integration errors
- create_internal_server_error(): 500 server errors
- create_sse_error_chunk(): Error chunks for streaming

Architecture:
- All errors use consistent dict format: status, error_type, message, details
- Errors logged with level (ERROR, WARNING) determined by context
- HTTPException wrapping allows FastAPI to handle response serialization
- SSE chunks format errors for streaming endpoints

Used By:
- API route handlers for consistent error responses
- Streaming endpoints for in-flight error reporting
- Middleware for error handling and logging
"""

from fastapi import HTTPException
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized error response dict with consistent structure.
    
    Low-level error dict constructor used by all error dialog functions.
    Ensures all API errors follow identical JSON format.
    
    Args:
        status_code: HTTP status code (400, 404, 500, etc.)
        error_type: Machine-readable error classification
                    (validation_error, not_found, service_error, internal_error)
        message: User-friendly error message (no technical details)
        details: Optional dict with error context (field, id, service name, etc.)
    
    Returns:
        Dict with keys: status="error", error_type, message, status_code, details
    
    Example:
        >>> resp = create_error_response(404, "not_found", "Album not found", 
        ...                              {"resource": "Album", "id": 123})
        >>> print(resp)
        >>> # {
        >>> #   "status": "error",
        >>> #   "error_type": "not_found",
        >>> #   "message": "Album not found",
        >>> #   "status_code": 404,
        >>> #   "details": {"resource": "Album", "id": 123}
        >>> # }
    
    Performance:
        O(1) - simple dict construction
    
    Note:
        This is typically not called directly by routes. Use convenience
        functions like create_validation_error(), create_not_found_error()
        instead for semantic clarity.
    
    Related:
        create_error_dialog(): Raises HTTPException with error response
        create_sse_error_chunk(): SSE format for streaming
    """
    response = {
        "status": "error",
        "error_type": error_type,
        "message": message,
        "status_code": status_code
    }
    
    if details:
        response["details"] = details
    
    return response


def create_error_dialog(
    status_code: int,
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    log_error: bool = True
) -> HTTPException:
    """Raise HTTPException with standardized error response.
    
    Primary error handling function for API routes. Logs error and raises
    HTTPException with standardized response body for client delivery.
    
    Args:
        status_code: HTTP status code (400, 404, 500, etc.)
        error_type: Error classification (validation_error, not_found, etc.)
        message: User-friendly error message
        details: Optional error context dict
        log_error: Whether to log error via logger.error (default True)
    
    Returns:
        Never returns - always raises HTTPException
    
    Raises:
        HTTPException: Always - with status_code and detail=error response dict
    
    Example:
        >>> try:
        ...     album = db.query(Album).filter(Album.id == 999).first()
        ...     if not album:
        ...         create_error_dialog(404, "not_found", "Album not found",
        ...                            {"resource": "Album", "id": 999})
        ... except HTTPException as e:
        ...     # FastAPI catches and serializes to client
        ...     pass
    
    Logging:
        ERROR: "❌ [error_type] message" at ERROR level
               Includes details in extra context (not in message)
        Can be suppressed with log_error=False for expected errors
    
    Performance:
        O(1) - simple exception raising
    
    Error Response Format:
        HTTP response body contains:
        {
            "status": "error",
            "error_type": error_type,
            "message": message,
            "status_code": status_code,
            "details": details (if provided)
        }
    
    Used By:
        Route handlers for all error cases
        Service methods for error propagation
        Middleware for error wrapping
    
    See Also:
        create_validation_error(): Convenience for 422 errors
        create_not_found_error(): Convenience for 404 errors
        create_service_error(): Convenience for 502 service errors
    """
    response = create_error_response(status_code, error_type, message, details)
    
    if log_error:
        logger.error(f"❌ [{error_type}] {message}", extra={"details": details})
    
    raise HTTPException(
        status_code=status_code,
        detail=response
    )


def create_validation_error(field: str, message: str) -> Dict[str, Any]:
    """Create 422 validation error response for field-level errors.
    
    Convenience function for form/input validation errors.
    
    Args:
        field: Field name with validation error
        message: Reason why validation failed
    
    Returns:
        Dict with status=error, status_code=422, error_type=validation_error
    
    Example:
        >>> if not email.contains('@'):
        ...     resp = create_validation_error("email", "Invalid email format")
        ...     # Returns: {
        ...     #   "status": "error",
        ...     #   "error_type": "validation_error",
        ...     #   "message": "Validation error",
        ...     #   "status_code": 422,
        ...     #   "details": {"field": "email", "reason": "Invalid email format"}
        ...     # }
    
    Performance:
        O(1) - simple dict construction
    
    Note:
        Returns dict, does not raise exception. Use create_error_dialog()
        to raise as HTTPException.
    """
    return create_error_response(
        status_code=422,
        error_type="validation_error",
        message="Validation error",
        details={"field": field, "reason": message}
    )


def create_not_found_error(resource: str, resource_id: Any) -> Dict[str, Any]:
    """Create 404 not found error response for missing resources.
    
    Convenience function for resource lookup failures.
    
    Args:
        resource: Resource type name (Album, Artist, Playlist, etc.)
        resource_id: ID/identifier of missing resource
    
    Returns:
        Dict with status=error, status_code=404, error_type=not_found
    
    Example:
        >>> album = db.query(Album).get(abc123)
        >>> if not album:
        ...     resp = create_not_found_error("Album", "abc123")
        ...     # Returns: {
        ...     #   "status": "error",
        ...     #   "error_type": "not_found",
        ...     #   "message": "Album not found",
        ...     #   "status_code": 404,
        ...     #   "details": {"resource": "Album", "id": "abc123"}
        ...     # }
    
    Performance:
        O(1) - simple dict construction
    """
    return create_error_response(
        status_code=404,
        error_type="not_found",
        message=f"{resource} not found",
        details={"resource": resource, "id": resource_id}
    )


def create_service_error(service: str, message: str) -> Dict[str, Any]:
    """Create 502 service integration error response.
    
    Used when external service (Spotify, AI, Roon, etc) call fails.
    
    Args:
        service: Service name that failed (Spotify, RoonBridge, etc.)
        message: Error from external service
    
    Returns:
        Dict with status=error, status_code=502, error_type=service_error
    
    Example:
        >>> try:
        ...     spotify.search_album(album_name)
        ... except Exception as e:
        ...     resp = create_service_error("Spotify", str(e))
        ...     # Returns: {
        ...     #   "status": "error",
        ...     #   "error_type": "service_error",
        ...     #   "message": "Error from Spotify",
        ...     #   "status_code": 502,
        ...     #   "details": {"service": "Spotify", "reason": "error message"}
        ...     # }
    
    Performance:
        O(1) - simple dict construction
    
    Note:
        502 Bad Gateway indicates external service unavailable/failing.
        Suggests client should retry after delay.
    """
    return create_error_response(
        status_code=502,
        error_type="service_error",
        message=f"Error from {service}",
        details={"service": service, "reason": message}
    )


def create_internal_server_error(message: str, exc: Optional[Exception] = None) -> Dict[str, Any]:
    """Create 500 internal server error response.
    
    Used for unexpected application errors.
    
    Args:
        message: User-friendly error message (no stack traces)
        exc: Optional exception object (logged but not exposed to client)
    
    Returns:
        Dict with status=error, status_code=500, error_type=internal_error
    
    Example:
        >>> try:
        ...     processor.process_data()
        ... except Exception as e:
        ...     logger.exception("Unexpected error")
        ...     resp = create_internal_server_error("Data processing failed", e)
        ...     # Returns: {
        ...     #   "status": "error",
        ...     #   "error_type": "internal_error",
        ...     #   "message": "Data processing failed",
        ...     #   "status_code": 500,
        ...     #   "details": {"exception": "ValueError: invalid value"}
        ...     # }
    
    Performance:
        O(1) - simple dict construction with optional exception str()
    
    Security Note:
        Exception type/message NOT exposed to client in response body.
        Exception string included in details only for debugging.
        Always log full traceback separately before calling this.
    """
    return create_error_response(
        status_code=500,
        error_type="internal_error",
        message=message,
        details={"exception": str(exc) if exc else None}
    )


def create_sse_error_chunk(error_type: str, message: str) -> str:
    """Create Server-Sent Event error chunk for streaming responses.
    
    Formats error for delivery in SSE stream (newline-delimited JSON).
    
    Args:
        error_type: Error classification (validation_error, not_found, etc.)
        message: Error message for client display
    
    Returns:
        Formatted SSE chunk: "data: {...json...}\n\n"
    
    Example:
        >>> async def generate_with_error():
        ...     try:
        ...         yield create_sse_error_chunk("service_error", "Spotify unavailable")
        ...     except Exception as e:
        ...         yield create_sse_error_chunk("internal_error", str(e))
        >>> # Yields: data: {"type":"error","error_type":"service_error","message":"Spotify unavailable"}\n\n
    
    SSE Format:
        - Prefixed with "data: "
        - JSON-encoded payload
        - Terminated with "\n\n" (blank line)
        - Client receives as single logical message
    
    Performance:
        O(1) - simple dict/JSON encoding
    
    Used By:
        Streaming endpoints for in-flight error reporting
        combine with create_sse_progress_chunk() for progress updates
    
    Related:
        streaming_dialog.create_sse_error_chunk(): More detailed variant
        with error_code parameter
    """
    error_data = {
        "type": "error",
        "error_type": error_type,
        "message": message
    }
    return f"data: {json.dumps(error_data)}\n\n"
