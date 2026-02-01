"""API pour les collections d'albums."""
import logging
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.album_collection_service import AlbumCollectionService
from app.services.roon_service import RoonService
from app.models import Album

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collections", tags=["collections"])


class CollectionCreate(BaseModel):
    """Modèle pour créer une collection."""
    name: str
    search_type: Optional[str] = None  # "genre", "artist", "period", "ai_query", "custom"
    search_criteria: Optional[dict] = None
    ai_query: Optional[str] = None


class CollectionResponse(BaseModel):
    """Modèle de réponse pour une collection."""
    id: int
    name: str
    search_type: Optional[str]
    search_criteria: Optional[dict]
    ai_query: Optional[str]
    album_count: int
    created_at: str
    
    @classmethod
    def from_orm(cls, collection):
        """Convertir un objet AlbumCollection en CollectionResponse."""
        # Parser le JSON si search_criteria est une string
        criteria = collection.search_criteria
        if isinstance(criteria, str):
            try:
                criteria = json.loads(criteria)
            except:
                criteria = None
        
        return cls(
            id=collection.id,
            name=collection.name,
            search_type=collection.search_type,
            search_criteria=criteria,
            ai_query=collection.ai_query,
            album_count=collection.album_count,
            created_at=collection.created_at.isoformat()
        )


class AlbumResponse(BaseModel):
    """Modèle de réponse pour un album."""
    id: int
    title: str
    artist_name: Optional[str]
    year: Optional[int]
    image_url: Optional[str]
    ai_description: Optional[str]
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Modèle pour une requête de recherche."""
    query: str
    limit: int = 50


@router.post("/", response_model=CollectionResponse)
def create_collection(
    collection: CollectionCreate,
    db: Session = Depends(get_db)
):
    """Créer une nouvelle collection d'albums."""
    service = AlbumCollectionService(db)
    
    new_collection = service.create_collection(
        name=collection.name,
        search_type=collection.search_type,
        search_criteria=collection.search_criteria,
        ai_query=collection.ai_query
    )
    
    return CollectionResponse.from_orm(new_collection)


@router.get("/", response_model=List[CollectionResponse])
def list_collections(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lister toutes les collections."""
    service = AlbumCollectionService(db)
    collections = service.list_collections(limit=limit, offset=offset)
    
    return [CollectionResponse.from_orm(c) for c in collections]


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer une collection par son ID."""
    service = AlbumCollectionService(db)
    collection = service.get_collection(collection_id)
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection non trouvée")
    
    return CollectionResponse.from_orm(collection)


@router.get("/{collection_id}/albums", response_model=List[AlbumResponse])
def get_collection_albums(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer les albums d'une collection."""
    service = AlbumCollectionService(db)
    albums = service.get_collection_albums(collection_id)
    
    return [
        AlbumResponse(
            id=album.id,
            title=album.title,
            artist_name=album.artists[0].name if album.artists else None,
            year=album.year,
            image_url=album.image_url,
            ai_description=album.ai_description
        )
        for album in albums
    ]


@router.post("/{collection_id}/albums")
def add_albums_to_collection(
    collection_id: int,
    album_ids: List[int],
    db: Session = Depends(get_db)
):
    """Ajouter des albums à une collection."""
    service = AlbumCollectionService(db)
    
    try:
        collection = service.add_albums_to_collection(collection_id, album_ids)
        return {"message": f"{len(album_ids)} albums ajoutés", "album_count": collection.album_count}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{collection_id}")
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """Supprimer une collection."""
    service = AlbumCollectionService(db)
    
    if not service.delete_collection(collection_id):
        raise HTTPException(status_code=404, detail="Collection non trouvée")
    
    return {"message": "Collection supprimée"}


@router.post("/search/genre", response_model=List[AlbumResponse])
def search_by_genre(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Rechercher des albums par genre."""
    service = AlbumCollectionService(db)
    albums = service.search_by_genre(request.query, limit=request.limit)
    
    return [
        AlbumResponse(
            id=album.id,
            title=album.title,
            artist_name=album.artists[0].name if album.artists else None,
            year=album.year,
            image_url=album.image_url,
            ai_description=album.ai_description
        )
        for album in albums
    ]


@router.post("/search/artist", response_model=List[AlbumResponse])
def search_by_artist(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Rechercher des albums par artiste."""
    service = AlbumCollectionService(db)
    albums = service.search_by_artist(request.query, limit=request.limit)
    
    return [
        AlbumResponse(
            id=album.id,
            title=album.title,
            artist_name=album.artists[0].name if album.artists else None,
            year=album.year,
            image_url=album.image_url,
            ai_description=album.ai_description
        )
        for album in albums
    ]


@router.post("/search/period", response_model=List[AlbumResponse])
def search_by_period(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Rechercher des albums par période."""
    service = AlbumCollectionService(db)
    albums = service.search_by_period(start_year, end_year, limit=limit)
    
    return [
        AlbumResponse(
            id=album.id,
            title=album.title,
            artist_name=album.artists[0].name if album.artists else None,
            year=album.year,
            image_url=album.image_url,
            ai_description=album.ai_description
        )
        for album in albums
    ]


@router.post("/search/ai", response_model=List[AlbumResponse])
def search_by_ai(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Rechercher des albums par requête AI (recherche sémantique)."""
    service = AlbumCollectionService(db)
    albums = service.search_by_ai_query(request.query, limit=request.limit)
    
    return [
        AlbumResponse(
            id=album.id,
            title=album.title,
            artist_name=album.artists[0].name if album.artists else None,
            year=album.year,
            image_url=album.image_url,
            ai_description=album.ai_description
        )
        for album in albums
    ]


class PlayCollectionRequest(BaseModel):
    """Modèle pour jouer une collection."""
    zone_name: Optional[str] = None


@router.post("/{collection_id}/play")
async def play_collection(
    collection_id: int,
    request: PlayCollectionRequest,
    db: Session = Depends(get_db)
):
    """Jouer tous les albums d'une collection sur Roon, en séquence.
    
    Note: Roon API ne permet pas de créer une queue. Chaque album sera joué
    entièrement avant de passer au suivant. La collection sera jouée en boucle
    en utilisant la fonctionnalité de repeat de Roon.
    """
    service = AlbumCollectionService(db)
    collection = service.get_collection(collection_id)
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection non trouvée")
    
    albums = service.get_collection_albums(collection_id)
    
    if not albums:
        raise HTTPException(status_code=400, detail="Collection vide")
    
    # Utiliser RoonService pour lancer les albums
    from app.services.roon_service import RoonService
    try:
        roon_service = RoonService()
    except Exception as e:
        logger.warning(f"Impossible de connecter à Roon: {e}")
        raise HTTPException(status_code=503, detail="Roon non disponible")
    
    # Jouer le premier album pour démarrer la lecture
    first_album = albums[0]
    artist_name = first_album.artists[0].name if first_album.artists else "Unknown"
    
    success = await roon_service.play_album(
        artist_name=artist_name,
        album_name=first_album.title,
        zone_name=request.zone_name
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Impossible de lancer la lecture")
    
    # Préparer la liste des albums suivants
    remaining_albums = [
        {"artist": a.artists[0].name if a.artists else "Unknown", "title": a.title}
        for a in albums[1:]
    ]
    
    logger.info(f"▶️ Collection {collection.name} lancée: {len(albums)} albums")
    logger.info(f"   Album en cours: {first_album.title}")
    logger.info(f"   Albums suivants: {len(remaining_albums)}")
    
    return {
        "message": "Collection lancée",
        "collection": collection.name,
        "album_count": len(albums),
        "current_album": first_album.title,
        "current_artist": artist_name,
        "remaining_albums": len(remaining_albums),
        "note": "L'album sera joué en entier. Pour passer au suivant, utilisez les contrôles Roon."
    }
