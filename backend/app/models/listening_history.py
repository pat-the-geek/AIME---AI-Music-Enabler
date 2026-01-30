"""Modèle ListeningHistory (historique d'écoute)."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ListeningHistory(Base):
    """Modèle pour l'historique d'écoute."""
    
    __tablename__ = "listening_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey('tracks.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(Integer, nullable=False, index=True)  # Unix timestamp
    date = Column(String(20), nullable=False, index=True)  # Format: YYYY-MM-DD HH:MM
    source = Column(String(20), nullable=False, index=True)  # 'roon' ou 'lastfm'
    loved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    track = relationship("Track", back_populates="listening_history")
    
    __table_args__ = (
        Index('idx_history_timestamp', 'timestamp'),
        Index('idx_history_source', 'source'),
        Index('idx_history_date', 'date'),
    )
    
    def __repr__(self):
        return f"<ListeningHistory(id={self.id}, track_id={self.track_id}, date='{self.date}')>"
