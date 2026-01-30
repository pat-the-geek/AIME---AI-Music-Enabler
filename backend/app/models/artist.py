"""Modèle Artist (artiste musical)."""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Artist(Base):
    """Modèle pour les artistes musicaux."""
    
    __tablename__ = "artists"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    spotify_id = Column(String(100), nullable=True)
    lastfm_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    images = relationship("Image", back_populates="artist", cascade="all, delete-orphan")
    albums = relationship("Album", secondary="album_artist", back_populates="artists")
    
    def __repr__(self):
        return f"<Artist(id={self.id}, name='{self.name}')>"
