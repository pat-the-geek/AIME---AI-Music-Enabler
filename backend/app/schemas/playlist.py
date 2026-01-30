"""Schémas Pydantic pour les playlists."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class PlaylistAlgorithm(str, Enum):
    """Algorithmes de génération de playlists."""
    TOP_SESSIONS = "top_sessions"
    ARTIST_CORRELATIONS = "artist_correlations"
    ARTIST_FLOW = "artist_flow"
    TIME_BASED = "time_based"
    COMPLETE_ALBUMS = "complete_albums"
    REDISCOVERY = "rediscovery"
    AI_GENERATED = "ai_generated"


class PlaylistGenerate(BaseModel):
    """Schéma pour générer une playlist."""
    algorithm: PlaylistAlgorithm = Field(..., description="Algorithme de génération")
    max_tracks: int = Field(default=25, ge=5, le=50, description="Nombre maximum de tracks")
    ai_prompt: Optional[str] = Field(None, max_length=1000, description="Prompt pour l'IA (si algorithm=ai_generated)")
    name: Optional[str] = Field(None, max_length=255, description="Nom personnalisé de la playlist")


class PlaylistTrackResponse(BaseModel):
    """Track dans une playlist."""
    track_id: int
    position: int
    title: str
    artist: str
    album: str
    duration_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True


class PlaylistResponse(BaseModel):
    """Réponse pour une playlist."""
    id: int
    name: str
    algorithm: str
    ai_prompt: Optional[str] = None
    track_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlaylistDetailResponse(PlaylistResponse):
    """Détail complet d'une playlist."""
    tracks: List[PlaylistTrackResponse]
    total_duration_seconds: Optional[int] = None
    unique_artists: int
    unique_albums: int
    
    class Config:
        from_attributes = True


class PlaylistExportFormat(str, Enum):
    """Formats d'export."""
    M3U = "m3u"
    JSON = "json"
    CSV = "csv"
    TXT = "txt"
