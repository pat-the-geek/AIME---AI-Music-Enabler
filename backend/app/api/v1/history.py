"""Routes API pour l'historique d'écoute."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from collections import defaultdict, Counter
import math

from app.database import get_db
from app.models import ListeningHistory, Track, Album, Artist, Image, Metadata
from app.schemas import (
    ListeningHistoryResponse,
    ListeningHistoryListResponse,
    ListeningHistoryUpdate,
    TimelineResponse,
    StatsResponse,
)

router = APIRouter()


@router.get("/tracks", response_model=ListeningHistoryListResponse)
async def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    source: Optional[str] = Query(None),
    loved: Optional[bool] = Query(None),
    artist: Optional[str] = Query(None),
    album: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Journal chronologique d'écoute."""
    query = db.query(ListeningHistory).join(Track).join(Album).join(Album.artists)
    
    # Filtres
    if source:
        query = query.filter(ListeningHistory.source == source)
    if loved is not None:
        query = query.filter(ListeningHistory.loved == loved)
    if artist:
        query = query.filter(Artist.name.ilike(f"%{artist}%"))
    if album:
        query = query.filter(Album.title.ilike(f"%{album}%"))
    if start_date:
        query = query.filter(ListeningHistory.date >= start_date)
    if end_date:
        query = query.filter(ListeningHistory.date <= end_date)
    
    # Tri chronologique inversé
    query = query.order_by(ListeningHistory.timestamp.desc())
    
    # Total
    total = query.count()
    
    # Pagination
    offset = (page - 1) * page_size
    history = query.offset(offset).limit(page_size).all()
    
    # Formater
    items = []
    for entry in history:
        track = entry.track
        album = track.album
        artists = [a.name for a in album.artists] if album and album.artists else []
        
        # Images
        artist_image = None
        if album and album.artists:
            artist_images = db.query(Image).filter(
                Image.artist_id == album.artists[0].id,
                Image.image_type == 'artist'
            ).first()
            if artist_images:
                artist_image = artist_images.url
        
        album_image = None
        album_lastfm_image = None
        if album:
            album_images = db.query(Image).filter(
                Image.album_id == album.id,
                Image.image_type == 'album'
            ).all()
            for img in album_images:
                if img.source == 'spotify':
                    album_image = img.url
                elif img.source == 'lastfm':
                    album_lastfm_image = img.url
        
        # Info IA
        ai_info = None
        if album and album.album_metadata:
            ai_info = album.album_metadata.ai_info
        
        items.append(ListeningHistoryResponse(
            id=entry.id,
            timestamp=entry.timestamp,
            date=entry.date,
            artist=', '.join(artists),
            title=track.title,
            album=album.title if album else "Unknown",
            album_id=album.id if album else None,
            track_id=track.id if track else None,
            loved=entry.loved,
            source=entry.source,
            artist_image=artist_image,
            album_image=album_image,
            album_lastfm_image=album_lastfm_image,
            spotify_url=album.spotify_url if album else None,
            discogs_url=album.discogs_url if album else None,
            ai_info=ai_info
        ))
    
    return ListeningHistoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.post("/tracks/{track_id}/love")
async def toggle_love(
    track_id: int,
    db: Session = Depends(get_db)
):
    """Marquer/démarquer un track comme favori."""
    entries = db.query(ListeningHistory).filter(
        ListeningHistory.track_id == track_id
    ).all()
    
    if not entries:
        raise HTTPException(status_code=404, detail="Track non trouvé dans l'historique")
    
    # Toggle loved
    new_loved = not entries[0].loved
    for entry in entries:
        entry.loved = new_loved
    
    db.commit()
    
    return {"track_id": track_id, "loved": new_loved}


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    date: str = Query(..., description="Date au format YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Timeline horaire pour une journée."""
    start_date = f"{date} 00:00"
    end_date = f"{date} 23:59"
    
    history = db.query(ListeningHistory).filter(
        ListeningHistory.date >= start_date,
        ListeningHistory.date <= end_date
    ).order_by(ListeningHistory.timestamp).all()
    
    # Organiser par heure
    hours = defaultdict(list)
    for entry in history:
        dt = datetime.fromtimestamp(entry.timestamp)
        hour = dt.hour
        
        track = entry.track
        album = track.album
        artists = [a.name for a in album.artists] if album and album.artists else []
        
        # Récupérer images album
        album_image = None
        album_lastfm_image = None
        if album:
            album_images = db.query(Image).filter(
                Image.album_id == album.id,
                Image.image_type == 'album'
            ).all()
            for img in album_images:
                if img.source == 'spotify':
                    album_image = img.url
                elif img.source == 'lastfm':
                    album_lastfm_image = img.url
        
        hours[hour].append({
            "id": entry.id,
            "time": dt.strftime("%H:%M"),
            "artist": ', '.join(artists),
            "title": track.title,
            "album": album.title if album else "Unknown",
            "album_id": album.id if album else None,
            "loved": entry.loved,
            "album_image": album_image,
            "album_lastfm_image": album_lastfm_image,
            "spotify_url": album.spotify_url if album else None,
            "discogs_url": album.discogs_url if album else None
        })
    
    # Statistiques
    unique_artists = set()
    unique_albums = set()
    hour_counts = Counter()
    
    for entry in history:
        track = entry.track
        if track.album:
            if track.album.artists:
                unique_artists.update([a.name for a in track.album.artists])
            unique_albums.add(track.album.title)
        
        dt = datetime.fromtimestamp(entry.timestamp)
        hour_counts[dt.hour] += 1
    
    peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else None
    
    return TimelineResponse(
        date=date,
        hours=dict(hours),
        stats={
            "total_tracks": len(history),
            "unique_artists": len(unique_artists),
            "unique_albums": len(unique_albums),
            "peak_hour": peak_hour
        }
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Statistiques d'écoute."""
    query = db.query(ListeningHistory)
    
    if start_date:
        query = query.filter(ListeningHistory.date >= start_date)
    if end_date:
        query = query.filter(ListeningHistory.date <= end_date)
    
    history = query.all()
    
    unique_artists = set()
    unique_albums = set()
    hour_counts = Counter()
    total_duration = 0
    
    for entry in history:
        track = entry.track
        if track.album:
            if track.album.artists:
                unique_artists.update([a.name for a in track.album.artists])
            unique_albums.add(track.album.title)
        
        if track.duration_seconds:
            total_duration += track.duration_seconds
        
        dt = datetime.fromtimestamp(entry.timestamp)
        hour_counts[dt.hour] += 1
    
    peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else None
    
    return StatsResponse(
        total_tracks=len(history),
        unique_artists=len(unique_artists),
        unique_albums=len(unique_albums),
        peak_hour=peak_hour,
        total_duration_seconds=total_duration if total_duration > 0 else None
    )


@router.get("/sessions")
async def detect_sessions(
    min_gap: int = Query(1800, description="Gap minimum entre sessions (secondes)"),
    db: Session = Depends(get_db)
):
    """Détecter les sessions d'écoute continues."""
    history = db.query(ListeningHistory).order_by(
        ListeningHistory.timestamp
    ).all()
    
    sessions = []
    current_session = []
    last_timestamp = 0
    
    for entry in history:
        if last_timestamp and (entry.timestamp - last_timestamp) > min_gap:
            # Nouvelle session
            if current_session:
                sessions.append(current_session)
            current_session = []
        
        current_session.append({
            "id": entry.id,
            "timestamp": entry.timestamp,
            "date": entry.date
        })
        last_timestamp = entry.timestamp
    
    if current_session:
        sessions.append(current_session)
    
    # Trier par longueur
    sessions.sort(key=len, reverse=True)
    
    return {
        "total_sessions": len(sessions),
        "longest_session": len(sessions[0]) if sessions else 0,
        "sessions": sessions[:10]  # Top 10
    }
