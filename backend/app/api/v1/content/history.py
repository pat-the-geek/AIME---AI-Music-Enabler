"""Routes API pour l'historique d'écoute."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import math
import logging

from app.database import get_db
from app.models import ListeningHistory, Track, Album, Artist, Image
from app.schemas import (
    ListeningHistoryResponse,
    ListeningHistoryListResponse,
    ListeningHistoryUpdate,
    TimelineResponse,
    StatsResponse,
)
from app.services.content import HaikuService, AnalysisService
from app.services.external.ai_service import AIService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/haiku")
async def generate_haiku(
    days: int = Query(7, ge=1, le=365, description="Nombre de jours à analyser"),
    db: Session = Depends(get_db)
):
    """Générer un haïku basé sur l'historique d'écoute récent."""
    try:
        settings = get_settings()
        secrets = settings.secrets
        euria_config = secrets.get('euria', {})
        
        ai_service = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer')
        )
        
        result = await HaikuService.generate_haiku(db, ai_service, days)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur haiku: {e}")
        raise HTTPException(status_code=500, detail="Erreur génération haïku")


@router.get("/patterns")
async def listening_patterns(
    db: Session = Depends(get_db)
):
    """Analyser les patterns d'écoute."""
    try:
        patterns = AnalysisService.analyze_listening_patterns(db)
        return patterns
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur patterns: {e}")
        raise HTTPException(status_code=500, detail="Erreur analyse patterns")



@router.get("/tracks", response_model=ListeningHistoryListResponse)
async def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    source: Optional[str] = Query(None),
    loved: Optional[bool] = Query(None),
    artist: Optional[str] = Query(None),
    album: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Journal chronologique d'écoute."""
    from datetime import datetime as dt_module
    
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
        # Convertir date YYYY-MM-DD en timestamp Unix (début du jour)
        start_dt = dt_module.strptime(f"{start_date} 00:00", "%Y-%m-%d %H:%M")
        start_timestamp = int(start_dt.timestamp())
        query = query.filter(ListeningHistory.timestamp >= start_timestamp)
    if end_date:
        # Convertir date YYYY-MM-DD en timestamp Unix (fin du jour)
        end_dt = dt_module.strptime(f"{end_date} 23:59", "%Y-%m-%d %H:%M")
        end_timestamp = int(end_dt.timestamp())
        query = query.filter(ListeningHistory.timestamp <= end_timestamp)
    
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
            year=album.year if album else None,
            album_id=album.id if album else None,
            track_id=track.id if track else None,
            loved=entry.loved,
            source=entry.source,
            artist_image=artist_image,
            album_image=album_image,
            album_lastfm_image=album_lastfm_image,
            spotify_url=album.spotify_url if album else None,
            apple_music_url=album.apple_music_url if album else None,
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
    try:
        # Récupérer les entrées d'historique pour la date
        start_dt = datetime.strptime(f"{date} 00:00", "%Y-%m-%d %H:%M")
        start_timestamp = int(start_dt.timestamp())
        
        end_dt = datetime.strptime(f"{date} 23:59", "%Y-%m-%d %H:%M")
        end_timestamp = int(end_dt.timestamp())
        
        logger.debug(f"📅 Timeline query: date={date}, start_ts={start_timestamp}, end_ts={end_timestamp}")
        
        history = db.query(ListeningHistory).filter(
            ListeningHistory.timestamp >= start_timestamp,
            ListeningHistory.timestamp <= end_timestamp
        ).order_by(ListeningHistory.timestamp.desc()).all()
        
        logger.debug(f"📊 Found {len(history)} entries for timeline date {date}")
        
        # Organiser par heure
        from collections import defaultdict
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
                "year": album.year if album else None,
                "album_id": album.id if album else None,
                "loved": entry.loved,
                "album_image": album_image,
                "album_lastfm_image": album_lastfm_image,
                "spotify_url": album.spotify_url if album else None,
                "apple_music_url": album.apple_music_url if album else None,
                "discogs_url": album.discogs_url if album else None
            })
        
        # Obtenir stats via AnalysisService
        stats_data = AnalysisService.get_timeline_stats(db, date)
        
        # Convertir les clés d'heure en chaînes de caractères (JSON exige des clés string)
        hours_dict = {str(hour): tracks for hour, tracks in hours.items()}
        
        return TimelineResponse(
            date=date,
            hours=hours_dict,
            stats={
                "total_tracks": stats_data['total_tracks'],
                "unique_artists": stats_data['unique_artists'],
                "unique_albums": stats_data['unique_albums'],
                "peak_hour": stats_data['peak_hour']
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur timeline: {e}")
        raise HTTPException(status_code=500, detail="Erreur timeline")



@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Statistiques d'écoute."""
    try:
        stats = AnalysisService.get_listening_stats(db, start_date, end_date)
        return stats
    except Exception as e:
        logger.error(f"Erreur stats: {e}")
        raise HTTPException(status_code=500, detail="Erreur stats")



@router.get("/sessions")
async def detect_sessions(
    min_gap: int = Query(1800, description="Gap minimum entre sessions (secondes)"),
    db: Session = Depends(get_db)
):
    """Détecter les sessions d'écoute continues."""
    try:
        sessions = AnalysisService.detect_sessions(db, min_gap)
        return sessions
    except Exception as e:
        logger.error(f"Erreur sessions: {e}")
        raise HTTPException(status_code=500, detail="Erreur détection sessions")
