"""Moniteur de santé pour l'application AIME."""
import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import func
from app.database import SessionLocal
from app.models.listening_history import ListeningHistory

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Moniteur de santé de l'application."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        self.last_db_check = None
        self.db_healthy = True
    
    def record_request(self, success: bool = True):
        """Enregistrer une requête."""
        self.request_count += 1
        if not success:
            self.error_count += 1
    
    async def check_database_health(self) -> bool:
        """Vérifier la santé de la base de données."""
        try:
            db = SessionLocal()
            # Simple query pour vérifier la connexion
            count = db.query(func.count(ListeningHistory.id)).scalar()
            db.close()
            
            self.db_healthy = True
            self.last_db_check = datetime.now()
            logger.debug(f"Database health check passed ({count} entries)")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self.db_healthy = False
            self.last_db_check = datetime.now()
            return False
    
    def get_status(self) -> dict:
        """Obtenir le statut global de santé."""
        uptime = datetime.now() - self.start_time
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            "status": "healthy" if self.db_healthy and error_rate < 5 else "degraded" if error_rate < 10 else "unhealthy",
            "uptime_seconds": int(uptime.total_seconds()),
            "requests": self.request_count,
            "errors": self.error_count,
            "error_rate": f"{error_rate:.2f}%",
            "database": "healthy" if self.db_healthy else "unhealthy",
            "last_db_check": self.last_db_check.isoformat() if self.last_db_check else None,
            "timestamp": datetime.now().isoformat()
        }


# Instance globale
health_monitor = HealthMonitor()
