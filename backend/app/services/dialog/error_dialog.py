"""Unified error dialog and error response handling."""

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
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        error_type: Type of error (e.g., 'validation_error', 'not_found', 'internal_error')
        message: User-friendly error message
        details: Additional error details
        
    Returns:
        Standardized error response dict
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
    """
    Create a standardized HTTPException with error dialog.
    
    Args:
        status_code: HTTP status code
        error_type: Type of error
        message: Error message
        details: Additional details
        log_error: Whether to log the error
        
    Returns:
        HTTPException with standardized response
    """
    response = create_error_response(status_code, error_type, message, details)
    
    if log_error:
        logger.error(f"❌ [{error_type}] {message}", extra={"details": details})
    
    raise HTTPException(
        status_code=status_code,
        detail=response
    )


def create_validation_error(field: str, message: str) -> Dict[str, Any]:
    """Create a validation error response."""
    return create_error_response(
        status_code=422,
        error_type="validation_error",
        message="Validation error",
        details={"field": field, "reason": message}
    )


def create_not_found_error(resource: str, resource_id: Any) -> Dict[str, Any]:
    """Create a not found error response."""
    return create_error_response(
        status_code=404,
        error_type="not_found",
        message=f"{resource} not found",
        details={"resource": resource, "id": resource_id}
    )


def create_service_error(service: str, message: str) -> Dict[str, Any]:
    """Create a service integration error response."""
    return create_error_response(
        status_code=502,
        error_type="service_error",
        message=f"Error from {service}",
        details={"service": service, "reason": message}
    )


def create_internal_server_error(message: str, exc: Optional[Exception] = None) -> Dict[str, Any]:
    """Create an internal server error response."""
    return create_error_response(
        status_code=500,
        error_type="internal_error",
        message=message,
        details={"exception": str(exc) if exc else None}
    )


def create_sse_error_chunk(error_type: str, message: str) -> str:
    """
    Create a Server-Sent Event chunk for error.
    
    Returns:
        Formatted SSE error chunk
    """
    error_data = {
        "type": "error",
        "error_type": error_type,
        "message": message
    }
    return f"data: {json.dumps(error_data)}\n\n"
