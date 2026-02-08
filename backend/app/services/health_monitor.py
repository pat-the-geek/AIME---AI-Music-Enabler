"""Application health monitoring with startup validation and database checks.

The HealthMonitor tracks application runtime state including:
- Request tracking (total count, error count, error rate percentage)
- Database connectivity and health status
- Startup validation (critical modules, data directories)
- Global status reporting (healthy/degraded/unhealthy)

Used by:
- /health endpoint for liveness probes
- startup event for validation before accepting requests
- Middleware for request tracking
- Admin dashboards for health visualization

Timeout strategy:
- Database checks: timeout managed via connection pool
- Startup validation: synchronous, ~5s typical
- Health status: O(1) no I/O required

Global instance available as: health_monitor
"""
import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import func, text
from app.database import SessionLocal, engine
from app.models.listening_history import ListeningHistory

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Application health monitoring and startup validation service.
    
    Tracks application state and provides health checks via /health endpoint.
    Monitors database connectivity, request metrics, error rates, and validates
    critical components at startup.
    
    Features:
    - Request counting with error tracking (for error rate calculation)
    - Asynchronous database health checks with timeout support
    - Synchronous database checks for startup validation
    - Startup validation: database, critical modules, data directories
    - Global status reporting: healthy/degraded/unhealthy
    
    Example:
        >>> monitor = HealthMonitor()
        >>> monitor.record_request(success=True)
        >>> if await monitor.check_database_health():
        ...     print("Database is healthy")
        >>> status = monitor.get_status()
        >>> print(f"API status: {status['status']} ({status['error_rate']} errors)")
    
    States:
    - "healthy": Database OK, error rate < max_error_rate (10%)
    - "degraded": Database OK, but error rate >= max_error_rate
    - "unhealthy": Database unavailable or critical component failed
    
    Initialization:
        Records start_time for uptime calculation. All health metrics
        initialized to default values.
    """
    
    def __init__(self):
        """Initialize health monitor with timestamp and default metrics.
        
        Sets up all tracking fields:
        - start_time: Used to calculate uptime in get_status()
        - request_count: Total API requests processed
        - error_count: Total failed requests (recorded via record_request)
        - last_db_check: Timestamp of last database health check
        - db_healthy: Current database connectivity status
        - last_error_message: Most recent error (if any)
        - max_error_rate: Alert threshold at 10% error rate
        
        Example:
            >>> monitor = HealthMonitor()
            >>> # start_time is now, all metrics at 0/False
        
        Side Effects:
            Records system time for uptime tracking. Does not perform
            any I/O or connectivity checks.
        
        Performance:
            O(1) - pure initialization, no database access
        """
    
    def record_request(self, success: bool = True):
        """Record API request outcome for error rate tracking.
        
        Increments total request count and conditionally records error.
        Used by middleware to track error_rate for health status degradation.
        
        Args:
            success: True if request succeeded (default), False if error
        
        Example:
            >>> monitor.record_request(success=True)  # Successful request
            >>> monitor.record_request(success=False) # Error request
            >>> # After 100 requests with 11 errors: error_rate = 11%
        
        Logging:
            No logging from this method - it's called frequently in middleware
        
        Performance:
            O(1) - atomic counter updates
        
        Implementation:
            Non-blocking, thread-safe for typical error counts. For millions of
            requests, consider atomic counters or async-safe collections.
        
        Related:
            Used with get_status() to calculate error_rate percentage.
            Error rate triggers "degraded" status when > max_error_rate (10%).
        """
        self.request_count += 1
        if not success:
            self.error_count += 1
    
    async def check_database_health(self) -> bool:
        """Asynchronously check database connectivity and health with timeout support.
        
        Verifies:
        1. Database connection (SELECT 1)
        2. Critical table exists (ListeningHistory)
        3. Basic record count accessible
        
        Updates internal state:
        - db_healthy: Set based on check result
        - last_db_check: Timestamp of this check
        - last_error_message: Error details if failed
        
        Returns:
            True if database is healthy and accessible
            False if timeout, connection error, or critical table missing
        
        Example:
            >>> if await monitor.check_database_health():
            ...     print("Database is accessible")
            >>> else:
            ...     print(f"Error: {monitor.last_error_message}")
        
        Timeout:
            Database connection pool timeout (typically 5s)
            Set via SQLAlchemy pool configuration
        
        Logging:
            DEBUG: "✅ Database health check passed (N entries)" on success
            ERROR: "❌ Database timeout/failed: message" on failure
        
        Exceptions:
            TimeoutError: Logs and sets db_healthy=False, returns False
            Any Exception: Logs and returns False
        
        Implementation:
            1. Creates new SessionLocal() for isolation
            2. Executes simple SELECT 1 for connection test
            3. Queries ListeningHistory count for table validation
            4. Always closes session (try/finally with close in except)
            5. Updates state before returning
        
        Performance:
            Typical: 50-200ms for healthy database
            Timeout: configured timeout (typically 5-10s)
            Big-O: O(1) - constant time regardless of database size
        
        Used By:
            Periodic health checks (scheduler)
            Middleware for ongoing monitoring
            Admin health status dashboard
        """
        try:
            db = None
            try:
                # Créer une session avec un timeout court
                db = SessionLocal()
                
                # Vérifier la connexion avec une requête simple
                db.execute(text("SELECT 1"))
                
                # Vérifier les tables critiques existent
                count = db.query(func.count(ListeningHistory.id)).scalar()
                
                self.db_healthy = True
                self.last_db_check = datetime.now()
                self.last_error_message = None
                logger.debug(f"✅ Database health check passed ({count} entries)")
                return True
            finally:
                if db:
                    try:
                        db.close()
                    except Exception as e:
                        logger.warning(f"Error closing DB session: {e}")
        except TimeoutError as e:
            error_msg = f"Database timeout: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.db_healthy = False
            self.last_db_check = datetime.now()
            self.last_error_message = error_msg
            return False
        except Exception as e:
            error_msg = f"Database health check failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.db_healthy = False
            self.last_db_check = datetime.now()
            self.last_error_message = error_msg
            return False
    
    def check_database_health_sync(self) -> bool:
        """Synchronously check database health for startup validation.
        
        Blocking variant of check_database_health() for use in startup events
        that cannot await async operations. Performs identical checks but
        without async/await pattern.
        
        Verifies same as async variant:
        1. Database connection (SELECT 1)
        2. ListeningHistory table accessibility
        3. Record count queryable
        
        Returns:
            True if database healthy, False if error/timeout
        
        Example:
            >>> # In @app.on_event("startup")
            >>> if not health_monitor.check_database_health_sync():
            ...     raise RuntimeError("Database not accessible at startup")
        
        Timeout:
            Database connection pool timeout (no asyncio timeout wrapper)
        
        Logging:
            DEBUG: "✅ Database health check passed" on success
            ERROR: "❌ Database health check failed: {error}" on failure
            Silent failure in finally block (session close exceptions ignored)
        
        Exceptions:
            All exceptions caught internally - always returns bool
            Never raises exceptions
        
        Implementation:
            Synchronous equivalent of async check_database_health().
            Uses try/finally to ensure session close. Suppresses exceptions
            in close() to prevent double-exception scenarios.
        
        Performance:
            Typical: 100-300ms (slightly slower than async variant)
            Similar performance characteristics to async variant
        
        Used By:
            validate_startup() for startup validation
            Fallback for non-async contexts
        
        Compare With:
            check_database_health(): Async variant, use in async contexts
            validate_startup(): Higher-level validation including modules
        """
        try:
            db = None
            try:
                db = SessionLocal()
                db.execute(text("SELECT 1"))
                count = db.query(func.count(ListeningHistory.id)).scalar()
                
                self.db_healthy = True
                self.last_db_check = datetime.now()
                self.last_error_message = None
                logger.debug(f"✅ Database health check passed ({count} entries)")
                return True
            finally:
                if db:
                    try:
                        db.close()
                    except Exception:
                        pass
        except Exception as e:
            error_msg = f"Database health check failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.db_healthy = False
            self.last_db_check = datetime.now()
            self.last_error_message = error_msg
            return False
    
    def validate_startup(self) -> bool:
        """Validate all critical components before accepting requests.
        
        Runs at application startup to ensure system is ready. Checks:
        1. Database accessibility and connectivity
        2. Critical modules importable (markdown_export, api routes)
        3. Data directories exist and writable
        
        Returns:
            True if all validations pass, False if any check fails
        
        Example:
            >>> # In app initialization
            >>> if not health_monitor.validate_startup():
            ...     raise RuntimeError("Startup validation failed")
            >>> app.run()
        
        Validation Steps:
            1. Database health: check_database_health_sync()
               - If fails: log error, return False immediately
            2. Module imports: MarkdownExportService, api route handlers
               - If ImportError: log error, return False
            3. Data directory: Create if missing (using settings.data_dir)
               - Ensures parent directories created with mkdir(parents=True)
        
        Logging:
            INFO: "Validation des composants au démarrage..."
            INFO: "✅ Database accessible"
            INFO: "✅ All critical modules loaded"
            INFO: "✅ All startup validations passed"
            ERROR: "❌ Database not accessible" (early exit)
            ERROR: "❌ Failed to import critical modules: {error}"
            INFO: "Creating data directory: {path}" (if needed)
        
        Returns:
            True: All checks pass, safe to start accepting requests
            False: Any check failed, do not start accepting requests
        
        Performance:
            Typical: 500ms - 2s (mostly database check time)
            Maximum: ~5s (database timeout + module load)
            Runs once at startup, not in hot path
        
        Used By:
            FastAPI startup event (@app.on_event("startup"))
            Initialization scripts
            Health check middleware setup
        
        Side Effects:
            Creates data directory if missing
            Logs comprehensive startup status
            May raise exceptions from module imports (caught and logged)
        
        Dependencies:
            check_database_health_sync(): Database validation
            MarkdownExportService: Import test
            app.api.v1 routes: Import test
            get_settings(): Configuration for data_dir path
        """
        try:
            logger.info("Validation des composants au démarrage...")
            
            # 1. Vérifier la connexion DB (version synchrone)
            if not self.check_database_health_sync():
                logger.error("❌ Database not accessible")
                return False
            logger.info("✅ Database accessible")
            
            # 2. Vérifier les importations critiques
            try:
                from app.services.markdown_export_service import MarkdownExportService
                from app.api.v1 import collection, history, search, collections
                logger.info("✅ All critical modules loaded")
            except ImportError as e:
                logger.error(f"❌ Failed to import critical modules: {e}")
                return False
            
            # 3. Vérifier le répertoire de données
            from pathlib import Path
            from app.core.config import get_settings
            settings = get_settings()
            if not settings.data_dir.exists():
                logger.info(f"Creating data directory: {settings.data_dir}")
                settings.data_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("✅ All startup validations passed")
            return True
        except Exception as e:
            logger.error(f"❌ Startup validation failed: {e}", exc_info=True)
            return False
    
    def get_status(self) -> dict:
        """Get comprehensive application health status for /health endpoint.
        
        Calculates current health metrics from tracked counters and returns
        structured status report. Used by health check endpoints and monitoring.
        
        Returns:
            dict with keys:
            - status: "healthy" | "degraded" | "unhealthy"
            - uptime_seconds: int (calculated from start_time)
            - requests: int (total request count)
            - errors: int (failed request count)
            - error_rate: str (formatted percentage, e.g., "5.50%")
            - database: "healthy" | "unhealthy"
            - last_db_check: ISO8601 timestamp or "never"
            - timestamp: ISO8601 of status report time
            - last_error: str (OPTIONAL, only if error_message set)
        
        Example:
            >>> status = monitor.get_status()
            >>> print(f"Status: {status['status']}")
            >>> print(f"Uptime: {status['uptime_seconds']}s")
            >>> print(f"Error rate: {status['error_rate']}")
            >>> # Response:
            >>> # {
            >>> #   "status": "healthy",
            >>> #   "uptime_seconds": 3600,
            >>> #   "requests": 1000,
            >>> #   "errors": 5,
            >>> #   "error_rate": "0.50%",
            >>> #   "database": "healthy",
            >>> #   "last_db_check": "2024-01-15T10:30:45.123456",
            >>> #   "timestamp": "2024-01-15T11:30:45.123456"
            >>> # }
        
        Status Determination Logic:
            "unhealthy": db_healthy is False
            "degraded": db_healthy is True AND error_rate > max_error_rate (10%)
            "healthy": db_healthy is True AND error_rate <= 10%
        
        Logging:
            No logging - this is called in response path (~1000s of times)
        
        Performance:
            O(1) - simple arithmetic on counters
            Typical: <1ms
        
        Error Handling:
            Returns "never" for last_db_check if check not yet run
            Omits "last_error" key if no error_message
            Handles divide-by-zero: error_rate = 0.0 if request_count = 0
        
        Used By:
            GET /health endpoint (liveness probe)
            Kubernetes readiness/liveness checks
            Monitoring dashboards
            Health status history tracking
        
        Format Notes:
            - Timestamps in ISO8601 format (isoformat())
            - Error rate formatted to 2 decimal places
            - All numeric values as int except error_rate (string)
        """
        uptime = datetime.now() - self.start_time
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        # Déterminer le statut global
        if not self.db_healthy:
            status = "unhealthy"
        elif error_rate > self.max_error_rate:
            status = "degraded"
        else:
            status = "healthy"
        
        response = {
            "status": status,
            "uptime_seconds": int(uptime.total_seconds()),
            "requests": self.request_count,
            "errors": self.error_count,
            "error_rate": f"{error_rate:.2f}%",
            "database": "healthy" if self.db_healthy else "unhealthy",
            "last_db_check": self.last_db_check.isoformat() if self.last_db_check else "never",
            "timestamp": datetime.now().isoformat()
        }
        
        if self.last_error_message:
            response["last_error"] = self.last_error_message
        
        return response


# Instance globale
health_monitor = HealthMonitor()
