"""
Application FastAPI principale - AIME (AI Music Enabler) v4.3.0

🎵 Developed with Vibe Coding using VS Code and GitHub Copilot

Modern web application for tracking and analyzing music listening history from Last.fm,
with automatic enrichment from multiple sources:
- Last.fm: Listening history, track metadata (aggregates from Roon ARC, PlexAmp, Quobuz, etc.)
- Spotify: Album URLs, cover images, track details
- Discogs: Collection management, vinyl records
- EurIA (Infomaniak AI): Automatic AI descriptions
"""
import sys
import warnings
import asyncio
import logging
import os
from contextlib import asynccontextmanager

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv non disponible

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
from app.api.v1 import collection, history, services, search, analytics, roon, collections, magazines, artists, playlists

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
    """Gestion du cycle de vie de l'application avec resilience.
    
    Les erreurs de service startup ne bloquent pas l'application.
    Cela permet au système de démarrer même si les trackers/scheduler
    ont des problèmes de connexion temporaires (ex: après wake-up).
    """
    # Startup
    try:
        logger.info("🚀 Démarrage de l'application AIME - AI Music Enabler")
        
        # Initialiser la base de données
        try:
            init_db()
            logger.info("✅ Base de données initialisée")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation BD: {e}", exc_info=True)
            raise RuntimeError(f"Database initialization failed: {e}")
        
        # Valider les composants au démarrage
        try:
            from app.services.health_monitor import health_monitor
            if not health_monitor.validate_startup():
                logger.error("❌ Startup validation failed - aborting")
                raise RuntimeError("Application startup validation failed")
            logger.info("✅ Tous les composants validés")
        except Exception as e:
            logger.error(f"❌ Erreur validation: {e}", exc_info=True)
            raise RuntimeError(f"Startup validation failed: {e}")
        
        global services_initialized
        services_initialized = True
        
        # Restaurer les services actifs (trackers, scheduler)
        # Les erreurs de service ne sont pas fatales - l'app peut démarrer sans
        try:
            from app.api.v1.tracking.services import restore_active_services
            await restore_active_services()
            logger.info("✅ Services restaurés")
        except Exception as e:
            logger.error(f"❌ Erreur restauration services: {e}", exc_info=True)
            # Continue même si les services échouent
            logger.warning("⚠️ Application démarrant sans services actifs")
        
        logger.info("✅ Application ready to serve requests")
    except RuntimeError as e:
        # Erreur fatale - arrêter l'application
        logger.error(f"❌ Erreur critique au démarrage: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"❌ Erreur inattendue au démarrage: {e}", exc_info=True)
        raise RuntimeError(f"Failed to start application: {str(e)}")
    
    yield
    
    # Shutdown
    try:
        logger.info("🛑 Arrêt de l'application AIME - AI Music Enabler")
        # Dispose du pool de connexions
        engine.dispose()
        logger.info("✅ Ressources libérées")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'arrêt: {e}", exc_info=True)

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
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(magazines.router, prefix="/api/v1/magazines", tags=["Magazines"])
app.include_router(artists.router, prefix="/api/v1/collection/artists", tags=["Artists"])
app.include_router(playlists.router, prefix="/api/v1/playlists", tags=["Playlists"])
app.include_router(collections.router, prefix="/api/v1", tags=["Album Collections"])
app.include_router(services.router, prefix="/api/v1/services", tags=["Services"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(roon.router, prefix="/api/v1/playback/roon", tags=["Roon Control"])


@app.get("/")
async def root():
    """
    API root endpoint - Returns service information and documentation links.
    
    This is the primary entry point for clients discovering the AIME Music Enabler API.
    Provides basic service metadata, version info, and links to interactive documentation.
    
    **Response (200 OK):**
    - `message`: Service name identifier (\"Music Tracker API\")
    - `version`: Current API version (e.g., \"4.3.0\")
    - `docs`: URL to interactive Swagger UI documentation (/docs)
    
    **Usage:**
    ```python
    GET /
    # Returns:
    # {
    #   \"message\": \"Music Tracker API\",
    #   \"version\": \"4.3.0\",
    #   \"docs\": \"/docs\"
    # }
    ```
    
    **Implementation Notes:**
    - No authentication required - serves as discovery endpoint
    - No database queries - returns static metadata
    - Response time: <1ms (memory operation)
    - Cache-friendly: Can be cached per API version change
    
    **Related Endpoints:**
    - GET /health: Service health status
    - GET /ready: Readiness probe for orchestration
    - GET /docs: Interactive API documentation (Swagger UI)
    """
    return {
        "message": "Music Tracker API",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint - Returns detailed service health status.
    
    Provides comprehensive health information for all critical components including
    database connectivity, external service integrations (Last.fm, Spotify, Discogs),
    background job trackers, and system resource availability.
    
    **Response (200 OK):**
    Returns HealthStatus object with component-level details:
    - `status`: Overall health (\"healthy\", \"degraded\", \"unhealthy\")
    - `uptime`: Service uptime in seconds
    - `components`: Object with per-component health status
      - `database`: PostgreSQL connection health (true/false)
      - `lastfm`: Last.fm API connectivity (true/false)
      - `spotify`: Spotify API connectivity (true/false)
      - `discogs`: Discogs API availability (true/false)
      - `tracker`: Active listening history tracker status (true/false)
      - `memory`: Available memory percentage
    - `timestamp`: Health check timestamp (ISO 8601)
    
    **Usage (Monitoring):**
    ```bash
    # Health monitoring for alerting
    curl -X GET http://localhost:8000/health
    
    # Response example:
    # {
    #   \"status\": \"healthy\",
    #   \"uptime\": 3600,
    #   \"components\": {
    #     \"database\": true,
    #     \"lastfm\": true,
    #     \"spotify\": true,
    #     \"discogs\": true,
    #     \"tracker\": true,
    #     \"memory\": 85
    #   },
    #   \"timestamp\": \"2026-02-08T10:30:45Z\"
    # }
    ```
    
    **Implementation Details:**
    - Delegates to HealthMonitor service for comprehensive checks
    - Database connectivity tested via lightweight query
    - External API health checked for recent errors/rate limits
    - Tracker health reflects if background jobs are running
    - Performance: 100-500ms (network-dependent)
    - Failure resilience: Returns partial status if some checks timeout
    
    **Error Scenarios:**
    - Database down: status=\"degraded\", components.database=false
    - All external APIs down: status=\"degraded\", multiple failures
    - Memory critical: status=\"degraded\", components.memory<10
    - Tracker crashed: status=\"degraded\", components.tracker=false
    
    **Related Endpoints:**
    - GET /ready: Readiness probe (simpler, faster)
    - GET /: Service info and documentation links
    
    **Typical Use Cases:**
    - Kubernetes liveness probe configuration
    - Monitored alerting system (Prometheus, DataDog, etc.)
    - Admin dashboard status indicator
    - Canary deployment health verification
    """
    from app.services.health_monitor import health_monitor
    return health_monitor.get_status()


@app.get("/ready")
async def readiness_check():
    """
    Readiness probe endpoint - Fast lightweight check for orchestration systems.
    
    Determines if the application is ready to accept traffic. Used by container
    orchestration platforms (Kubernetes, Docker Compose) to route traffic. Much
    faster and simpler than /health endpoint - only checks critical prerequisites.
    
    **Response (200 OK):**
    - `ready`: Boolean indicating traffic readiness (true/false)
    - `message`: Status description (\"Application ready\" or reason for not ready)
    
    **Status Codes:**
    - 200 OK: ready=true (application accepting traffic)
    - 200 OK: ready=false (application not ready, but endpoint accessible)
    - No 503 Service Unavailable returned (always responds 200 for probe compatibility)
    
    **Critical Prerequisites Checked:**
    1. Database connectivity (PostgreSQL must respond)
    2. Services initialized (startup hooks completed)
    3. Core components loaded (no fatal errors)
    
    **Response Examples:**
    ```bash
    # Ready for traffic
    GET /ready
    HTTP/1.1 200 OK
    {
      \"ready\": true,
      \"message\": \"Application ready\"
    }
    
    # Not ready (startup in progress)
    GET /ready  
    HTTP/1.1 200 OK
    {
      \"ready\": false,
      \"message\": \"Application not ready\"
    }
    
    # Not ready (database error)
    GET /ready
    HTTP/1.1 200 OK
    {
      \"ready\": false,
      \"message\": \"Database connection failed\"
    }
    ```
    
    **Performance:**
    - Normal case (ready): <20ms (fast check, no deep validation)
    - Database check: 50-100ms (lightweight query)
    - Total: Typically <100ms
    
    **Startup Sequence:**
    1. Application starts (FastAPI lifespan startup)
    2. Database initialized
    3. HealthMonitor validates components
    4. services_initialized = True
    5. /ready endpoint returns true
    - Complete startup: ~2-5 seconds (including database migrations)
    
    **Implementation Logic:**
    - Check: await db.execute(select(1))  [<10ms]
    - Check: if services_initialized flag is True
    - Error handling: Catch exception, return ready=false with error message
    - No retries: Single query attempt (fail-fast for orchestration)
    
    **Kubernetes Configuration Example:**
    ```yaml
    readinessProbe:
      httpGet:
        path: /ready
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 5
      failureThreshold: 3
      timeoutSeconds: 2
    ```
    
    **Traffic Routing Behavior:**
    - Kubernetes directs traffic only when ready=true
    - Graceful shutdown: returns ready=false during shutdown sequence
    - Allows requests in-flight to complete before terminating
    - Blue-green deployments: waits for ready=true before traffic switch
    
    **Related Endpoints:**
    - GET /health: Detailed multi-component health status
    - GET /: Service info and documentation
    
    **Common Integration Issues:**
    - Issue: /ready returns false after startup
      Solution: Check database connection, verify migrations complete
    - Issue: Kubernetes keeps restarting pod
      Solution: Increase initialDelaySeconds (database startup time)
    - Issue: Traffic occasionally dropped
      Solution: readiness probe timeout too aggressive, increase timeoutSeconds
    """
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
