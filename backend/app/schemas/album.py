"""Schémas Pydantic pour les albums."""
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, List, Any


class AlbumBase(BaseModel):
    """Schéma de base pour un album."""
    title: str = Field(..., max_length=500, description="Titre de l'album")
    year: Optional[int] = Field(None, ge=0, le=2100, description="Année de sortie (0 si inconnue)")
    support: Optional[str] = Field(None, max_length=50, description="Support (Vinyle, CD, Digital)")
    discogs_id: Optional[str] = Field(None, max_length=100, description="ID Discogs")
    spotify_url: Optional[str] = Field(None, max_length=500, description="URL Spotify")
    discogs_url: Optional[str] = Field(None, max_length=500, description="URL Discogs")


class AlbumCreate(AlbumBase):
    """Schéma pour créer un album."""
    artist_ids: List[int] = Field(..., min_length=1, description="IDs des artistes")


class AlbumUpdate(BaseModel):
    """Schéma pour mettre à jour un album."""
    title: Optional[str] = Field(None, max_length=500)
    year: Optional[int] = Field(None, ge=0, le=2100)
    support: Optional[str] = Field(None, max_length=50)
    discogs_id: Optional[str] = Field(None, max_length=100)
    spotify_url: Optional[str] = Field(None, max_length=500)
    discogs_url: Optional[str] = Field(None, max_length=500)
    artist_ids: Optional[List[int]] = None


class AlbumResponse(AlbumBase):
    """Schéma de réponse pour un album."""
    id: int
    artists: List[str] = Field(default_factory=list, description="Noms des artistes")
    images: List[str] = Field(default_factory=list, description="URLs des images")
    ai_info: Optional[str] = Field(None, description="Description IA")
    created_at: datetime
    updated_at: datetime
    
    @model_validator(mode='before')
    @classmethod
    def map_ai_description(cls, data: Any) -> Any:
        """Mapper ai_description de la BD vers ai_info dans l'API."""
        if isinstance(data, dict):
            # Si ai_description existe mais pas ai_info, copier la valeur
            if 'ai_description' in data and 'ai_info' not in data:
                data['ai_info'] = data.get('ai_description')
        return data
    
    class Config:
        from_attributes = True
        populate_by_name = True


class AlbumDetail(AlbumResponse):
    """Détail complet d'un album."""
    resume: Optional[str] = None
    labels: Optional[List[str]] = None
    film_title: Optional[str] = None
    film_year: Optional[int] = None
    film_director: Optional[str] = None
    artist_images: dict = Field(default_factory=dict, description="Images des artistes (nom -> URL)")
    
    class Config:
        from_attributes = True


class AlbumListResponse(BaseModel):
    """Réponse paginée pour la liste d'albums."""
    items: List[AlbumResponse]
    total: int
    page: int
    page_size: int
    pages: int
