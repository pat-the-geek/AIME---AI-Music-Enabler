"""Routes API pour l'historique d'écoute."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from collections import defaultdict, Counter
import math
import logging

from app.database import get_db
from app.models import ListeningHistory, Track, Album, Artist, Image, Metadata
from app.schemas import (
    ListeningHistoryResponse,
    ListeningHistoryListResponse,
    ListeningHistoryUpdate,
    TimelineResponse,
    StatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/haiku")
async def generate_haiku(
    days: int = Query(7, ge=1, le=365, description="Nombre de jours à analyser"),
    db: Session = Depends(get_db)
):
    """Générer un haïku basé sur l'historique d'écoute récent."""
    from app.services.ai_service import AIService
    from app.core.config import get_settings
    from datetime import timedelta
    
    settings = get_settings()
    secrets = settings.secrets
    euria_config = secrets.get('euria', {})
    
    ai_service = AIService(
        url=euria_config.get('url'),
        bearer=euria_config.get('bearer')
    )
    
    # Analyser l'historique récent
    cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
    recent_history = db.query(ListeningHistory).join(Track).join(Album).join(Album.artists).filter(
        ListeningHistory.timestamp >= cutoff_timestamp
    ).all()
    
    if not recent_history:
        raise HTTPException(status_code=404, detail="Pas d'historique d'écoute récent")
    
    # Extraire données
    artists = Counter()
    albums = Counter()
    for entry in recent_history:
        track = entry.track
        album = track.album
        if album and album.artists:
            for artist in album.artists:
                artists[artist.name] += 1
        if album:
            albums[album.title] += 1
    
    listening_data = {
        'top_artists': [name for name, _ in artists.most_common(5)],
        'top_albums': [title for title, _ in albums.most_common(5)],
        'total_tracks': len(recent_history),
        'days': days
    }
    
    haiku = await ai_service.generate_haiku(listening_data)
    
    return {
        "haiku": haiku,
        "period_days": days,
        "total_tracks": len(recent_history),
        "top_artists": listening_data['top_artists'],
        "top_albums": listening_data['top_albums']
    }


@router.get("/patterns")
async def listening_patterns(
    db: Session = Depends(get_db)
):
    """Analyser les patterns d'écoute."""
    history = db.query(ListeningHistory).join(Track).join(Album).join(Album.artists).all()
    
    if not history:
        raise HTTPException(status_code=404, detail="Pas d'historique d'écoute")
    
    # Patterns par heure
    hourly_patterns = Counter()
    for entry in history:
        dt = datetime.fromtimestamp(entry.timestamp)
        hourly_patterns[dt.hour] += 1
    
    # Patterns par jour de la semaine
    weekday_patterns = Counter()
    weekday_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    for entry in history:
        dt = datetime.fromtimestamp(entry.timestamp)
        weekday_patterns[weekday_names[dt.weekday()]] += 1
    
    # Détection de sessions d'écoute
    sorted_history = sorted(history, key=lambda x: x.timestamp)
    sessions = []
    current_session = []
    last_timestamp = 0
    
    for entry in sorted_history:
        if last_timestamp and (entry.timestamp - last_timestamp) > 1800:  # 30 min gap
            if len(current_session) >= 3:
                sessions.append({
                    'track_count': len(current_session),
                    'start_time': datetime.fromtimestamp(current_session[0]).isoformat(),
                    'duration_minutes': (current_session[-1] - current_session[0]) // 60
                })
            current_session = []
        current_session.append(entry.timestamp)
        last_timestamp = entry.timestamp
    
    if len(current_session) >= 3:
        sessions.append({
            'track_count': len(current_session),
            'start_time': datetime.fromtimestamp(current_session[0]).isoformat(),
            'duration_minutes': (current_session[-1] - current_session[0]) // 60
        })
    
    # Artistes par corrélation (qui sont souvent écoutés ensemble)
    artist_pairs = Counter()
    sorted_by_time = sorted(history, key=lambda x: x.timestamp)
    
    for i in range(len(sorted_by_time) - 1):
        entry1 = sorted_by_time[i]
        entry2 = sorted_by_time[i + 1]
        
        # Si écoutés dans la même session (< 30 min)
        if entry2.timestamp - entry1.timestamp < 1800:
            track1 = entry1.track
            track2 = entry2.track
            
            if track1.album and track1.album.artists and track2.album and track2.album.artists:
                artist1 = track1.album.artists[0].name
                artist2 = track2.album.artists[0].name
                
                if artist1 != artist2:
                    pair = tuple(sorted([artist1, artist2]))
                    artist_pairs[pair] += 1
    
    # Top corrélations
    top_correlations = [
        {"artist1": pair[0], "artist2": pair[1], "count": count}
        for pair, count in artist_pairs.most_common(10)
    ]
    
    # Temps moyen d'écoute par jour
    daily_listening = Counter()
    for entry in history:
        dt = datetime.fromtimestamp(entry.timestamp)
        date_str = dt.strftime('%Y-%m-%d')
        daily_listening[date_str] += 1
    
    avg_tracks_per_day = sum(daily_listening.values()) / len(daily_listening) if daily_listening else 0
    
    return {
        "total_tracks": len(history),
        "hourly_patterns": dict(sorted(hourly_patterns.items())),
        "weekday_patterns": weekday_patterns,
        "peak_hour": hourly_patterns.most_common(1)[0][0] if hourly_patterns else None,
        "peak_weekday": weekday_patterns.most_common(1)[0][0] if weekday_patterns else None,
        "listening_sessions": {
            "total_sessions": len(sessions),
            "avg_tracks_per_session": sum(s['track_count'] for s in sessions) / len(sessions) if sessions else 0,
            "longest_sessions": sorted(sessions, key=lambda x: x['track_count'], reverse=True)[:5]
        },
        "artist_correlations": top_correlations,
        "daily_average": round(avg_tracks_per_day, 1),
        "unique_days": len(daily_listening)
    }


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
    # Convertir la date en timestamps Unix (meilleure performance et précision)
    from datetime import datetime as dt_module
    
    # Début du jour à 00:00
    start_dt = dt_module.strptime(f"{date} 00:00", "%Y-%m-%d %H:%M")
    start_timestamp = int(start_dt.timestamp())
    
    # Fin du jour à 23:59
    end_dt = dt_module.strptime(f"{date} 23:59", "%Y-%m-%d %H:%M")
    end_timestamp = int(end_dt.timestamp())
    
    logger.debug(f"📅 Timeline query: date={date}, start_ts={start_timestamp}, end_ts={end_timestamp}")
    
    history = db.query(ListeningHistory).filter(
        ListeningHistory.timestamp >= start_timestamp,
        ListeningHistory.timestamp <= end_timestamp
    ).order_by(ListeningHistory.timestamp.desc()).all()
    
    logger.debug(f"📊 Found {len(history)} entries for timeline date {date}")
    
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
            "year": album.year if album else None,
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
    
    # Convertir les clés d'heure en chaînes de caractères (JSON exige des clés string)
    hours_dict = {str(hour): tracks for hour, tracks in hours.items()}
    
    return TimelineResponse(
        date=date,
        hours=hours_dict,
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
    from datetime import datetime as dt_module
    
    query = db.query(ListeningHistory)
    
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
