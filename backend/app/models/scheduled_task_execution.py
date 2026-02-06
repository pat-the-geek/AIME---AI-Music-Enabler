"""Modèle pour la persistance des exécutions des tâches du scheduler."""
from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone
from app.database import Base


class ScheduledTaskExecution(Base):
    """Enregistrement des exécutions des tâches scheduler."""
    
    __tablename__ = 'scheduled_task_executions'
    
    task_id = Column(String, primary_key=True)  # ID unique de la tâche (ex: 'daily_enrichment')
    task_name = Column(String, nullable=False)  # Nom lisible (ex: '💾 Export JSON')
    last_executed = Column(DateTime(timezone=True), nullable=True)  # Dernière exécution
    last_status = Column(String, default='pending', nullable=False)  # 'success', 'error', 'pending'
    next_run_time = Column(DateTime(timezone=True), nullable=True)  # Prochaine exécution planifiée
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<ScheduledTaskExecution(task_id='{self.task_id}', last_executed={self.last_executed}, last_status='{self.last_status}')>"
