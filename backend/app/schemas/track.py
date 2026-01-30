"""Schémas Pydantic pour les tracks."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TrackBase(BaseModel):
    """Schéma de base pour une track."""
    title: str = Field(..., max_length=500, description="Titre de la track")
    track_number: Optional[int] = Field(None, ge=1, description="Numéro de piste")
    duration_seconds: Optional[int] = Field(None, ge=0, description="Durée en secondes")
    spotify_id: Optional[str] = Field(None, max_length=100, description="ID Spotify")


class TrackCreate(TrackBase):
    """Schéma pour créer une track."""
    album_id: int = Field(..., description="ID de l'album")


class TrackUpdate(BaseModel):
    """Schéma pour mettre à jour une track."""
    title: Optional[str] = Field(None, max_length=500)
    track_number: Optional[int] = Field(None, ge=1)
    duration_seconds: Optional[int] = Field(None, ge=0)
    spotify_id: Optional[str] = Field(None, max_length=100)


class TrackResponse(TrackBase):
    """Schéma de réponse pour une track."""
    id: int
    album_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
