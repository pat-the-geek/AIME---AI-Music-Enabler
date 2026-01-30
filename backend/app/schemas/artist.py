"""Schémas Pydantic pour les artistes."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ArtistBase(BaseModel):
    """Schéma de base pour un artiste."""
    name: str = Field(..., max_length=255, description="Nom de l'artiste")
    spotify_id: Optional[str] = Field(None, max_length=100, description="ID Spotify")
    lastfm_url: Optional[str] = Field(None, max_length=500, description="URL Last.fm")


class ArtistCreate(ArtistBase):
    """Schéma pour créer un artiste."""
    pass


class ArtistUpdate(BaseModel):
    """Schéma pour mettre à jour un artiste."""
    name: Optional[str] = Field(None, max_length=255)
    spotify_id: Optional[str] = Field(None, max_length=100)
    lastfm_url: Optional[str] = Field(None, max_length=500)


class ArtistResponse(ArtistBase):
    """Schéma de réponse pour un artiste."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ArtistWithImage(ArtistResponse):
    """Artiste avec image principale."""
    image_url: Optional[str] = None
    
    class Config:
        from_attributes = True
