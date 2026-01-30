"""Application FastAPI principale."""
import sys
import warnings

# Contournement pour Python 3.14 et SQLAlchemy
if sys.version_info >= (3, 14):
    warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import get_settings
from app.database import init_db
from app.api.v1 import collection, history, playlists, services, search

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Récupérer les settings
settings = get_settings()

# Créer l'application FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API REST pour Music Tracker - Gestion d'écoute musicale avec enrichissement IA",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(collection.router, prefix="/api/v1/collection", tags=["Collection"])
app.include_router(history.router, prefix="/api/v1/history", tags=["History"])
app.include_router(playlists.router, prefix="/api/v1/playlists", tags=["Playlists"])
app.include_router(services.router, prefix="/api/v1/services", tags=["Services"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])


@app.on_event("startup")
async def startup_event():
    """Événement au démarrage de l'application."""
    logger.info("Démarrage de l'application AIME - AI Music Enabler")
    
    # Initialiser la base de données
    init_db()
    logger.info("Base de données initialisée")


@app.on_event("shutdown")
async def shutdown_event():
    """Événement à l'arrêt de l'application."""
    logger.info("Arrêt de l'application AIME - AI Music Enabler")


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
    return {
        "status": "ok",
        "version": settings.app_version
    }
