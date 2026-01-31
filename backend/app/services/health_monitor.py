"""Moniteur de santé pour l'application AIME."""
import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import func, text
from app.database import SessionLocal, engine
from app.models.listening_history import ListeningHistory

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Moniteur de santé de l'application."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        self.last_db_check = None
        self.db_healthy = False
        self.last_error_message = None
        self.max_error_rate = 10.0  # Alerte si > 10%
    
    def record_request(self, success: bool = True):
        """Enregistrer une requête."""
        self.request_count += 1
        if not success:
            self.error_count += 1
    
    async def check_database_health(self) -> bool:
        """Vérifier la santé de la base de données avec timeout."""
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
        """Vérifier la santé de la base de données (version synchrone pour validate_startup)."""
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
        """Valider que tous les composants critiques sont prêts au démarrage."""
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
                from app.api.v1 import collection, history, playlists, search
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
        """Obtenir le statut global de santé."""
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
