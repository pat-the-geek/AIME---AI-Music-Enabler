"""Modèle Album (album musical)."""
from sqlalchemy import Column, Integer, String, DateTime, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.database import Base


class AlbumSource(PyEnum):
    """Source d'origine de l'album."""
    DISCOGS = "discogs"      # Collection Discogs
    LASTFM = "lastfm"        # Importé depuis Last.fm (historique d'écoute)
    ROON = "roon"            # Importé depuis Roon (historique d'écoute)
    SPOTIFY = "spotify"      # Importé depuis Spotify
    MANUAL = "manual"        # Ajouté manuellement


class Album(Base):
    """Modèle pour les albums musicaux."""
    
    __tablename__ = "albums"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    year = Column(Integer, nullable=True)
    support = Column(String(50), nullable=True)  # Vinyle, CD, Digital, ou autre selon la source
    source = Column(String(20), nullable=False, default="manual", index=True)  # Source d'origine
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
    
    def is_collection_album(self) -> bool:
        """Vérifier si c'est un album de collection Discogs."""
        return self.source == "discogs"
    
    def is_valid_support(self) -> bool:
        """Vérifier que le support est valide pour la source."""
        if self.source == "discogs":
            # Pour Discogs, accepter uniquement Vinyle, CD, Digital ou NULL
            valid_supports = {None, "Vinyle", "CD", "Digital", "Vinyl", "Cassette"}
            return self.support in valid_supports
        # Pour les autres sources, tous les supports sont acceptés
        return True
    
    def __repr__(self):
        return f"<Album(id={self.id}, title='{self.title}', source='{self.source}', year={self.year})>"
