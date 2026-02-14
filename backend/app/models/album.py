"""Modèle Album (album musical)."""
from sqlalchemy import Column, Integer, String, DateTime, Enum, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.database import Base


class AlbumSource(PyEnum):
    """Source d'origine de l'album."""
    DISCOGS = "discogs"      # Collection Discogs
    LASTFM = "lastfm"        # Importé depuis Last.fm (historique d'écoute)
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
    apple_music_url = Column(String(500), nullable=True)
    discogs_url = Column(String(500), nullable=True)
    genre = Column(String(200), nullable=True, index=True)  # Genre musical principal
    image_url = Column(String(1000), nullable=True)  # URL de la couverture
    ai_description = Column(String(2000), nullable=True)  # Description générée par AI
    ai_style = Column(String(500), nullable=True)  # Style/ambiance généré par AI
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    artists = relationship("Artist", secondary="album_artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="album", cascade="all, delete-orphan")
    album_metadata = relationship("Metadata", back_populates="album", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_albums_discogs_id', 'discogs_id'),
        Index('idx_albums_spotify_url', 'spotify_url'),
        Index('idx_albums_apple_music_url', 'apple_music_url'),
        Index('idx_albums_discogs_url', 'discogs_url'),
        Index('idx_albums_source_created', 'source', 'created_at'),
        Index('idx_albums_title_source', 'title', 'source'),
        Index('idx_albums_year', 'year'),
    )
    
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
    
    def is_valid_apple_music_url(self) -> bool:
        """Vérifier que l'URL Apple Music est compatible avec window.open()."""
        if not self.apple_music_url:
            return True  # None est acceptable
        
        # Importer ici pour éviter une import circulaire
        from app.services.apple_music_service import AppleMusicService
        return AppleMusicService.is_compatible_url(self.apple_music_url)
    
    def __repr__(self):
        return f"<Album(id={self.id}, title='{self.title}', source='{self.source}', year={self.year})>"
