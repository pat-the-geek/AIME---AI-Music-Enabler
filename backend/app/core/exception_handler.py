"""Global exception handlers et error middleware pour FastAPI."""

import logging
from typing import Callable
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Format standardisé pour les réponses d'erreur."""
    
    @staticmethod
    def format_error(
        error_type: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None
    ) -> dict:
        """Formater une réponse d'erreur."""
        response = {
            "error": error_type,
            "message": message,
            "status_code": status_code,
        }
        
        if details:
            response["details"] = details
        
        return response


def setup_exception_handlers(app: FastAPI):
    """Configurer les handlers d'exceptions pour l'application."""
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handler pour les erreurs de validation Pydantic."""
        logger.error(f"❌ Erreur validation: {exc.errors()}")
        
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"][1:]),
                "type": error["type"],
                "message": error["msg"]
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse.format_error(
                "VALIDATION_ERROR",
                "Les données envoyées ne sont pas valides",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                {"errors": errors}
            )
        )
    
    @app.exception_handler(TimeoutError)
    async def timeout_exception_handler(request: Request, exc: TimeoutError):
        """Handler pour les timeouts."""
        logger.error(f"⏱️ Timeout: {exc}")
        
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content=ErrorResponse.format_error(
                "TIMEOUT_ERROR",
                "La requête a dépassé le délai d'attente",
                status.HTTP_504_GATEWAY_TIMEOUT
            )
        )
    
    @app.exception_handler(ConnectionError)
    async def connection_exception_handler(request: Request, exc: ConnectionError):
        """Handler pour les erreurs de connexion."""
        logger.error(f"🔗 Erreur connexion: {exc}")
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse.format_error(
                "CONNECTION_ERROR",
                "Impossible de se connecter au service",
                status.HTTP_503_SERVICE_UNAVAILABLE
            )
        )
    
    @app.exception_handler(ValueError)
    async def value_exception_handler(request: Request, exc: ValueError):
        """Handler pour les erreurs de valeur."""
        logger.error(f"❌ Erreur valeur: {exc}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse.format_error(
                "VALUE_ERROR",
                str(exc),
                status.HTTP_400_BAD_REQUEST
            )
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handler pour les exceptions non gérées."""
        # Logger le traceback complet
        logger.error(f"❌ Exception non gérée: {exc}")
        logger.error(traceback.format_exc())
        
        # Déterminer si c'est une erreur exposable à l'utilisateur
        error_type = exc.__class__.__name__
        message = str(exc)
        
        # Ne pas exposer les détails sensibles en production
        if "CONSTRAINT" in message or "integrity" in message.lower():
            message = "Conflit d'intégrité des données"
            error_type = "DATABASE_INTEGRITY_ERROR"
        elif "no such table" in message.lower():
            message = "Table de base de données introuvable"
            error_type = "DATABASE_TABLE_ERROR"
        elif "syntax error" in message.lower():
            message = "Erreur de syntaxe SQL"
            error_type = "DATABASE_SYNTAX_ERROR"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse.format_error(
                error_type,
                message,
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        )


async def add_process_time_header(request: Request, call_next: Callable):
    """Middleware pour tracker le temps de traitement."""
    import time
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        if process_time > 10:
            logger.warning(f"⚠️ Requête lente: {request.url.path} - {process_time:.2f}s")
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ Erreur dans middleware: {e} ({process_time:.2f}s)")
        raise


async def add_request_id_header(request: Request, call_next: Callable):
    """Middleware pour ajouter un request ID."""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response
