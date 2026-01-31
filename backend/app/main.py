"""Application FastAPI principale."""
import sys
import warnings
import asyncio
import logging
from contextlib import asynccontextmanager

# Contournement pour Python 3.14 et SQLAlchemy
if sys.version_info >= (3, 14):
    warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.exception_handler import setup_exception_handlers, add_process_time_header, add_request_id_header
from app.database import init_db, engine
from app.api.v1 import collection, history, playlists, services, search

# Configuration du logging amélioré
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Récupérer les settings
settings = get_settings()

# Variables globales pour les services
services_initialized = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # Startup
    try:
        logger.info("Démarrage de l'application AIME - AI Music Enabler")
        init_db()
        logger.info("Base de données initialisée")
        global services_initialized
        services_initialized = True
    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    try:
        logger.info("Arrêt de l'application AIME - AI Music Enabler")
        # Dispose du pool de connexions
        engine.dispose()
        logger.info("Ressources libérées")
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt: {e}", exc_info=True)

# Créer l'application FastAPI avec lifespan
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API REST pour Music Tracker - Gestion d'écoute musicale avec enrichissement IA",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ajouter les middlewares de traçage et timing
app.middleware("http")(add_request_id_header)
app.middleware("http")(add_process_time_header)

# Configurer les exception handlers
setup_exception_handlers(app)

# Inclure les routers
app.include_router(collection.router, prefix="/api/v1/collection", tags=["Collection"])
app.include_router(history.router, prefix="/api/v1/history", tags=["History"])
app.include_router(playlists.router, prefix="/api/v1/playlists", tags=["Playlists"])
app.include_router(services.router, prefix="/api/v1/services", tags=["Services"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])


@app.get("/")
async def root():
    """Route racine."""
    return {
        "message": "Music Tracker API",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Vérification de santé de l'API."""
    from app.services.health_monitor import health_monitor
    return health_monitor.get_status()


@app.get("/ready")
async def readiness_check():
    """Vérification de préparation (readiness probe)."""
    try:
        from app.services.health_monitor import health_monitor
        db_ok = await health_monitor.check_database_health()
        if db_ok and services_initialized:
            return {"ready": True, "message": "Application ready"}
        else:
            return {"ready": False, "message": "Application not ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"ready": False, "message": str(e)}
