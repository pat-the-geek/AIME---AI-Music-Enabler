"""Routes API pour la recherche globale."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Album, Artist, Track

router = APIRouter()


@router.get("")
async def search(
    q: str = Query(..., min_length=2, description="Requête de recherche"),
    type: Optional[str] = Query(None, description="Type (album, artist, track)"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Recherche globale."""
    results = {
        "query": q,
        "albums": [],
        "artists": [],
        "tracks": []
    }
    
    # Recherche albums
    if type is None or type == "album":
        albums = db.query(Album).filter(
            Album.title.ilike(f"%{q}%")
        ).limit(limit).all()
        
        results["albums"] = [
            {
                "id": a.id,
                "title": a.title,
                "year": a.year,
                "artists": [artist.name for artist in a.artists]
            }
            for a in albums
        ]
    
    # Recherche artistes
    if type is None or type == "artist":
        artists = db.query(Artist).filter(
            Artist.name.ilike(f"%{q}%")
        ).limit(limit).all()
        
        results["artists"] = [
            {
                "id": a.id,
                "name": a.name,
                "spotify_id": a.spotify_id
            }
            for a in artists
        ]
    
    # Recherche tracks
    if type is None or type == "track":
        tracks = db.query(Track).filter(
            Track.title.ilike(f"%{q}%")
        ).limit(limit).all()
        
        results["tracks"] = [
            {
                "id": t.id,
                "title": t.title,
                "album": t.album.title if t.album else "Unknown",
                "artists": [a.name for a in t.album.artists] if t.album and t.album.artists else []
            }
            for t in tracks
        ]
    
    return results


@router.get("/search")
async def search_with_query_param(
    query: str = Query(..., min_length=2, description="Requête de recherche"),
    type: Optional[str] = Query(None, description="Type (album, artist, track)"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Endpoint de recherche avec paramètre 'query'."""
    results = {
        "query": query,
        "albums": [],
        "artists": [],
        "tracks": []
    }
    
    # Recherche albums
    if type is None or type == "album":
        albums = db.query(Album).filter(
            Album.title.ilike(f"%{query}%")
        ).limit(limit).all()
        
        results["albums"] = [
            {
                "id": a.id,
                "title": a.title,
                "year": a.year,
                "artists": [artist.name for artist in a.artists]
            }
            for a in albums
        ]
    
    # Recherche artistes
    if type is None or type == "artist":
        artists = db.query(Artist).filter(
            Artist.name.ilike(f"%{query}%")
        ).limit(limit).all()
        
        results["artists"] = [
            {
                "id": a.id,
                "name": a.name,
                "spotify_id": a.spotify_id
            }
            for a in artists
        ]
    
    # Recherche tracks
    if type is None or type == "track":
        tracks = db.query(Track).filter(
            Track.title.ilike(f"%{query}%")
        ).limit(limit).all()
        
        results["tracks"] = [
            {
                "id": t.id,
                "title": t.title,
                "album": t.album.title if t.album else "Unknown",
                "artists": [a.name for a in t.album.artists] if t.album and t.album.artists else []
            }
            for t in tracks
        ]
    
    return results

