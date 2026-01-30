"""Modèle Playlist (playlists générées)."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Playlist(Base):
    """Modèle pour les playlists générées."""
    
    __tablename__ = "playlists"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    algorithm = Column(String(50), nullable=False)  # 'top_sessions', 'ai_generated', etc.
    ai_prompt = Column(Text, nullable=True)  # Si algorithm='ai_generated'
    track_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    tracks = relationship("PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Playlist(id={self.id}, name='{self.name}', algorithm='{self.algorithm}')>"


class PlaylistTrack(Base):
    """Modèle pour les tracks dans les playlists."""
    
    __tablename__ = "playlist_tracks"
    
    playlist_id = Column(Integer, ForeignKey('playlists.id', ondelete='CASCADE'), primary_key=True)
    track_id = Column(Integer, ForeignKey('tracks.id', ondelete='CASCADE'), primary_key=True)
    position = Column(Integer, nullable=False)
    
    # Relations
    playlist = relationship("Playlist", back_populates="tracks")
    track = relationship("Track")
    
    def __repr__(self):
        return f"<PlaylistTrack(playlist_id={self.playlist_id}, track_id={self.track_id}, pos={self.position})>"
