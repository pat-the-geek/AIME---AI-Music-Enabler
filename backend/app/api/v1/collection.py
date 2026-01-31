"""API endpoints pour la collection d'albums."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import math

from app.database import get_db
from app.models import Album, Artist, Image, Metadata, album_artist
from app.schemas import (
    AlbumCreate,
    AlbumUpdate,
    AlbumResponse,
    AlbumDetail,
    AlbumListResponse,
)

router = APIRouter()


@router.get("/albums", response_model=AlbumListResponse)
async def list_albums(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(30, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title or artist"),
    support: Optional[str] = Query(None, description="Filter by support (Vinyle, CD, Digital)"),
    year: Optional[int] = Query(None, description="Filter by year"),
    is_soundtrack: Optional[bool] = Query(None, description="Filter soundtracks"),
    db: Session = Depends(get_db)
):
    """Liste des albums avec pagination et filtres."""
    query = db.query(Album)
    
    # Recherche
    if search:
        query = query.join(Album.artists).filter(
            (Album.title.ilike(f"%{search}%")) | (Artist.name.ilike(f"%{search}%"))
        )
    
    # Filtres
    if support:
        query = query.filter(Album.support == support)
    
    if year:
        query = query.filter(Album.year == year)
    
    if is_soundtrack is not None:
        query = query.outerjoin(Album.album_metadata).filter(
            Metadata.film_title.isnot(None) if is_soundtrack else Metadata.film_title.is_(None)
        )
    
    # Total
    total = query.count()
    
    # Pagination
    offset = (page - 1) * page_size
    albums = query.offset(offset).limit(page_size).all()
    
    # Formater la réponse
    items = []
    for album in albums:
        try:
            # Récupérer les noms d'artistes
            artists = [a.name for a in album.artists] if album.artists else []
            
            # Récupérer les images
            images = [img.url for img in album.images] if album.images else []
            
            # Récupérer l'info IA
            ai_info = None
            if album.album_metadata:
                ai_info = album.album_metadata.ai_info
            
            items.append(AlbumResponse(
                id=album.id,
                title=album.title,
                year=album.year,
                support=album.support,
                discogs_id=album.discogs_id,
                spotify_url=album.spotify_url,
                discogs_url=album.discogs_url,
                artists=artists,
                images=images,
                ai_info=ai_info,
                created_at=album.created_at,
                updated_at=album.updated_at
            ))
        except Exception as e:
            # Log mais continue avec les autres albums
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur formatage album {album.id}: {e}")
            continue
    
    return AlbumListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/albums/{album_id}", response_model=AlbumDetail)
async def get_album(
    album_id: int,
    db: Session = Depends(get_db)
):
    """Détail d'un album."""
    album = db.query(Album).filter(Album.id == album_id).first()
    
    if not album:
        raise HTTPException(status_code=404, detail="Album non trouvé")
    
    # Formater la réponse
    artists = [a.name for a in album.artists]
    images = [img.url for img in album.images]
    
    ai_info = None
    resume = None
    labels = None
    film_title = None
    film_year = None
    film_director = None
    
    if album.album_metadata:
        ai_info = album.album_metadata.ai_info
        resume = album.album_metadata.resume
        labels = album.album_metadata.labels.split(',') if album.album_metadata.labels else None
        film_title = album.album_metadata.film_title
        film_year = album.album_metadata.film_year
        film_director = album.album_metadata.film_director
    
    return AlbumDetail(
        id=album.id,
        title=album.title,
        year=album.year,
        support=album.support,
        discogs_id=album.discogs_id,
        spotify_url=album.spotify_url,
        discogs_url=album.discogs_url,
        artists=artists,
        images=images,
        ai_info=ai_info,
        resume=resume,
        labels=labels,
        film_title=film_title,
        film_year=film_year,
        film_director=film_director,
        created_at=album.created_at,
        updated_at=album.updated_at
    )


@router.post("/albums", response_model=AlbumResponse, status_code=201)
async def create_album(
    album_data: AlbumCreate,
    db: Session = Depends(get_db)
):
    """Créer un nouvel album."""
    # Vérifier que les artistes existent
    artists = db.query(Artist).filter(Artist.id.in_(album_data.artist_ids)).all()
    
    if len(artists) != len(album_data.artist_ids):
        raise HTTPException(status_code=400, detail="Un ou plusieurs artistes non trouvés")
    
    # Créer l'album
    album = Album(
        title=album_data.title,
        year=album_data.year,
        support=album_data.support,
        discogs_id=album_data.discogs_id,
        spotify_url=album_data.spotify_url,
        discogs_url=album_data.discogs_url
    )
    album.artists = artists
    
    db.add(album)
    db.commit()
    db.refresh(album)
    
    return AlbumResponse(
        id=album.id,
        title=album.title,
        year=album.year,
        support=album.support,
        discogs_id=album.discogs_id,
        spotify_url=album.spotify_url,
        discogs_url=album.discogs_url,
        artists=[a.name for a in album.artists],
        images=[],
        ai_info=None,
        created_at=album.created_at,
        updated_at=album.updated_at
    )


@router.put("/albums/{album_id}", response_model=AlbumResponse)
async def update_album(
    album_id: int,
    album_data: AlbumUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un album."""
    album = db.query(Album).filter(Album.id == album_id).first()
    
    if not album:
        raise HTTPException(status_code=404, detail="Album non trouvé")
    
    # Mettre à jour les champs
    if album_data.title is not None:
        album.title = album_data.title
    if album_data.year is not None:
        album.year = album_data.year
    if album_data.support is not None:
        album.support = album_data.support
    if album_data.discogs_id is not None:
        album.discogs_id = album_data.discogs_id
    if album_data.spotify_url is not None:
        album.spotify_url = album_data.spotify_url
    if album_data.discogs_url is not None:
        album.discogs_url = album_data.discogs_url
    
    if album_data.artist_ids is not None:
        artists = db.query(Artist).filter(Artist.id.in_(album_data.artist_ids)).all()
        if len(artists) != len(album_data.artist_ids):
            raise HTTPException(status_code=400, detail="Un ou plusieurs artistes non trouvés")
        album.artists = artists
    
    db.commit()
    db.refresh(album)
    
    return AlbumResponse(
        id=album.id,
        title=album.title,
        year=album.year,
        support=album.support,
        discogs_id=album.discogs_id,
        spotify_url=album.spotify_url,
        discogs_url=album.discogs_url,
        artists=[a.name for a in album.artists],
        images=[img.url for img in album.images],
        ai_info=album.album_metadata.ai_info if album.album_metadata else None,
        created_at=album.created_at,
        updated_at=album.updated_at
    )


@router.patch("/albums/{album_id}")
async def patch_album(
    album_id: int,
    patch_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Mettre à jour partiellement un album (ex: URL Spotify)."""
    album = db.query(Album).filter(Album.id == album_id).first()
    
    if not album:
        raise HTTPException(status_code=404, detail="Album non trouvé")
    
    # Mettre à jour uniquement les champs fournis
    if 'spotify_url' in patch_data:
        album.spotify_url = patch_data['spotify_url']
    
    db.commit()
    db.refresh(album)
    
    return {
        "id": album.id,
        "spotify_url": album.spotify_url,
        "message": "Album mis à jour"
    }


@router.delete("/albums/{album_id}", status_code=204)
async def delete_album(
    album_id: int,
    db: Session = Depends(get_db)
):
    """Supprimer un album."""
    album = db.query(Album).filter(Album.id == album_id).first()
    
    if not album:
        raise HTTPException(status_code=404, detail="Album non trouvé")
    
    db.delete(album)
    db.commit()
    
    return None


@router.get("/artists", response_model=List[dict])
async def list_artists(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Liste des artistes."""
    artists = db.query(Artist).limit(limit).all()
    
    result = []
    for artist in artists:
        # Récupérer l'image
        image_url = None
        if artist.images:
            image_url = artist.images[0].url
        
        result.append({
            "id": artist.id,
            "name": artist.name,
            "spotify_id": artist.spotify_id,
            "image_url": image_url
        })
    
    return result


@router.get("/stats")
async def get_collection_stats(
    db: Session = Depends(get_db)
):
    """Statistiques de la collection."""
    total_albums = db.query(Album).count()
    total_artists = db.query(Artist).count()
    
    # Par support
    supports = db.query(Album.support, db.func.count(Album.id)).group_by(Album.support).all()
    
    # Soundtracks
    soundtracks = db.query(Metadata).filter(Metadata.film_title.isnot(None)).count()
    
    return {
        "total_albums": total_albums,
        "total_artists": total_artists,
        "by_support": {s[0] or "Unknown": s[1] for s in supports},
        "soundtracks": soundtracks
    }
