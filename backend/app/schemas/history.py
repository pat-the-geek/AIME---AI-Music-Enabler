"""Schémas Pydantic pour l'historique d'écoute."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ListeningHistoryBase(BaseModel):
    """Schéma de base pour l'historique."""
    timestamp: int = Field(..., description="Unix timestamp")
    date: str = Field(..., max_length=20, description="Date au format YYYY-MM-DD HH:MM")
    source: str = Field(..., max_length=20, description="Source (roon, lastfm)")
    loved: bool = Field(default=False, description="Favori")


class ListeningHistoryCreate(ListeningHistoryBase):
    """Schéma pour créer une entrée d'historique."""
    track_id: int = Field(..., description="ID de la track")


class ListeningHistoryUpdate(BaseModel):
    """Schéma pour mettre à jour une entrée."""
    loved: Optional[bool] = None


class ListeningHistoryResponse(BaseModel):
    """Schéma de réponse pour l'historique."""
    id: int
    timestamp: int
    date: str
    artist: str
    title: str
    album: str
    album_id: Optional[int] = None
    track_id: Optional[int] = None
    loved: bool
    source: str
    artist_image: Optional[str] = None
    album_image: Optional[str] = None
    album_lastfm_image: Optional[str] = None
    spotify_url: Optional[str] = None
    discogs_url: Optional[str] = None
    ai_info: Optional[str] = None
    
    class Config:
        from_attributes = True


class ListeningHistoryListResponse(BaseModel):
    """Réponse paginée pour l'historique."""
    items: List[ListeningHistoryResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TimelineResponse(BaseModel):
    """Réponse pour la timeline horaire."""
    date: str
    hours: dict  # Clé: heure (6-23), Valeur: liste de tracks
    stats: dict  # total_tracks, unique_artists, unique_albums, peak_hour


class StatsResponse(BaseModel):
    """Statistiques d'écoute."""
    total_tracks: int
    unique_artists: int
    unique_albums: int
    peak_hour: Optional[int] = None
    total_duration_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True
