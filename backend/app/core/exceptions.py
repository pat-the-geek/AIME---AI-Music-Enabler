"""Custom exceptions et error handling pour l'application."""

from typing import Optional
from fastapi import HTTPException, status


class AIServiceException(HTTPException):
    """Exception levée par le service IA."""
    def __init__(self, message: str, status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE):
        super().__init__(status_code=status_code, detail=f"Service IA indisponible: {message}")


class DiscogsServiceException(HTTPException):
    """Exception levée par le service Discogs."""
    def __init__(self, message: str, status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE):
        super().__init__(status_code=status_code, detail=f"Service Discogs indisponible: {message}")


class SpotifyServiceException(HTTPException):
    """Exception levée par le service Spotify."""
    def __init__(self, message: str, status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE):
        super().__init__(status_code=status_code, detail=f"Service Spotify indisponible: {message}")


class LastFMServiceException(HTTPException):
    """Exception levée par le service LastFM."""
    def __init__(self, message: str, status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE):
        super().__init__(status_code=status_code, detail=f"Service Last.fm indisponible: {message}")


class DatabaseException(HTTPException):
    """Exception levée par la base de données."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=f"Erreur base de données: {message}")


class TimeoutException(HTTPException):
    """Exception levée lors d'un timeout."""
    def __init__(self, service: str = "service", timeout_seconds: int = 30):
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout du {service} après {timeout_seconds} secondes"
        )


class RateLimitException(HTTPException):
    """Exception levée lorsque les limites d'API sont atteintes."""
    def __init__(self, service: str = "service", retry_after: Optional[int] = None):
        detail = f"Limite de requêtes atteinte pour {service}"
        if retry_after is not None:
            detail += f" - réessayer après {retry_after}s"
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )


class NetworkException(HTTPException):
    """Exception levée lors d'une erreur réseau."""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erreur réseau: {message}"
        )


class CircuitBreakerOpen(Exception):
    """Exception levée quand un circuit breaker est ouvert."""
    def __init__(self, service: str, retry_after: int = 60):
        self.service = service
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker ouvert pour {service}, réessai après {retry_after}s")


class ValidationException(HTTPException):
    """Exception levée lors d'une erreur de validation."""
    def __init__(self, message: str, field: Optional[str] = None):
        detail = f"Validation échouée: {message}"
        if field:
            detail += f" (champ: {field})"
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

class ResourceNotFoundException(HTTPException):
    """Exception levée quand une ressource n'est pas trouvée."""
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        detail = f"{resource} non trouvé"
        if resource_id:
            detail += f" (ID: {resource_id})"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)