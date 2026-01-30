"""Modèle Album (album musical)."""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Album(Base):
    """Modèle pour les albums musicaux."""
    
    __tablename__ = "albums"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    year = Column(Integer, nullable=True)
    support = Column(String(50), nullable=True)  # Vinyle, CD, Digital
    discogs_id = Column(String(100), unique=True, nullable=True)
    spotify_url = Column(String(500), nullable=True)
    discogs_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    artists = relationship("Artist", secondary="album_artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="album", cascade="all, delete-orphan")
    album_metadata = relationship("Metadata", back_populates="album", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Album(id={self.id}, title='{self.title}', year={self.year})>"
