"""Modèle Track (piste musicale)."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Track(Base):
    """Modèle pour les pistes musicales."""
    
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    album_id = Column(Integer, ForeignKey('albums.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(500), nullable=False)
    track_number = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    spotify_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    album = relationship("Album", back_populates="tracks")
    listening_history = relationship("ListeningHistory", back_populates="track", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Track(id={self.id}, title='{self.title}')>"
