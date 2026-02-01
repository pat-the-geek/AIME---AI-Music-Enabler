"""Modèle pour la persistance des états des services."""
from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime, timezone
from app.database import Base


class ServiceState(Base):
    """État de persistance des services background (trackers, scheduler)."""
    
    __tablename__ = 'service_states'
    
    service_name = Column(String, primary_key=True)  # 'tracker', 'roon_tracker', 'scheduler'
    is_active = Column(Boolean, default=False, nullable=False)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<ServiceState(service_name='{self.service_name}', is_active={self.is_active}, last_updated={self.last_updated})>"
