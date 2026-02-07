"""Routes API pour les analytics avancées."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Optional

from app.database import get_db
from app.models import ListeningHistory, Track, Album, Artist, Metadata

router = APIRouter()


@router.get("/advanced-stats")
async def advanced_stats(
    start_date: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Statistiques avancées avec filtres temporels."""
    query = db.query(ListeningHistory).join(Track).join(Album)
    
    # Filtres dates
    if start_date:
        query = query.filter(ListeningHistory.date >= start_date)
    if end_date:
        query = query.filter(ListeningHistory.date <= end_date)
    
    history = query.all()
    
    if not history:
        raise HTTPException(status_code=404, detail="Pas de données pour cette période")
    
    # Compteurs
    artists_count = Counter()
    albums_count = Counter()
    genres_count = Counter()
    monthly_counts = Counter()
    mood_counts = Counter()
    
    total_duration_seconds = 0
    
    for entry in history:
        track = entry.track
        album = track.album
        
        # Artistes
        if album and album.artists:
            for artist in album.artists:
                artists_count[artist.name] += 1
        
        # Albums
        if album:
            albums_count[album.title] += 1
            
            # Métadonnées
            if album.album_metadata:
                metadata = album.album_metadata
                if metadata.labels:
                    try:
                        import json
                        labels = json.loads(metadata.labels)
                        if isinstance(labels, list):
                            for label in labels:
                                genres_count[label] += 1
                    except:
                        pass
                
                if metadata.ai_info:
                    # Extraire mood de la description IA
                    if 'énergie' in metadata.ai_info.lower():
                        mood_counts['energetic'] += 1
                    if 'calme' in metadata.ai_info.lower():
                        mood_counts['calm'] += 1
                    if 'mélanc' in metadata.ai_info.lower():
                        mood_counts['melancholic'] += 1
                    if 'joyeux' in metadata.ai_info.lower():
                        mood_counts['joyful'] += 1
        
        # Durée
        if track.duration_seconds:
            total_duration_seconds += track.duration_seconds
        
        # Mois
        dt = datetime.fromisoformat(entry.date)
        month_key = dt.strftime('%Y-%m')
        monthly_counts[month_key] += 1
    
    # Calculer moyennes
    unique_days = len(set(entry.date for entry in history))
    avg_per_day = len(history) / unique_days if unique_days > 0 else 0
    
    return {
        "period": {
            "start": start_date or "N/A",
            "end": end_date or "N/A",
            "total_days": unique_days,
            "total_tracks": len(history),
            "avg_per_day": round(avg_per_day, 2)
        },
        "top_artists": [
            {"name": name, "count": count}
            for name, count in artists_count.most_common(10)
        ],
        "top_albums": [
            {"title": title, "count": count}
            for title, count in albums_count.most_common(10)
        ],
        "top_genres": [
            {"genre": genre, "count": count}
            for genre, count in genres_count.most_common(10)
        ],
        "mood_distribution": dict(mood_counts) if mood_counts else {},
        "monthly_trend": dict(sorted(monthly_counts.items())),
        "total_hours": round(total_duration_seconds / 3600, 2) if total_duration_seconds > 0 else 0
    }


@router.get("/discovery-stats")
async def discovery_stats(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours à analyser"),
    db: Session = Depends(get_db)
):
    """Analyse des artistes et albums découverts récemment."""
    cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
    
    history = db.query(ListeningHistory).join(Track).join(Album).filter(
        ListeningHistory.date >= cutoff_date
    ).all()
    
    if not history:
        raise HTTPException(status_code=404, detail="Pas de données récentes")
    
    # Premier écoute par artiste
    first_listening = {}
    artist_first_count = defaultdict(lambda: None)
    
    sorted_history = sorted(history, key=lambda x: x.timestamp)
    
    for entry in sorted_history:
        track = entry.track
        if track.album and track.album.artists:
            for artist in track.album.artists:
                if artist.name not in artist_first_count:
                    artist_first_count[artist.name] = entry.date
    
    # Nouveaux artistes
    new_artists = [
        {"name": name, "first_listened": date}
        for name, date in sorted(artist_first_count.items(), key=lambda x: x[1], reverse=True)[:20]
    ]
    
    # Artistes réécoutés (sans être découvert dans cette période)
    all_artists = Counter()
    for entry in history:
        track = entry.track
        if track.album and track.album.artists:
            for artist in track.album.artists:
                all_artists[artist.name] += 1
    
    return {
        "period_days": days,
        "total_new_artists": len(artist_first_count),
        "new_artists": new_artists,
        "most_replayed": [
            {"name": name, "count": count}
            for name, count in all_artists.most_common(10)
        ]
    }


@router.get("/comparison")
async def compare_periods(
    period1_start: str = Query(..., description="Période 1: date début (YYYY-MM-DD)"),
    period1_end: str = Query(..., description="Période 1: date fin (YYYY-MM-DD)"),
    period2_start: str = Query(..., description="Période 2: date début (YYYY-MM-DD)"),
    period2_end: str = Query(..., description="Période 2: date fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Comparer deux périodes d'écoute."""
    
    def get_period_stats(start_date, end_date):
        query = db.query(ListeningHistory).join(Track).join(Album).filter(
            ListeningHistory.date >= start_date,
            ListeningHistory.date <= end_date
        )
        
        history = query.all()
        
        artists = Counter()
        for entry in history:
            track = entry.track
            if track.album and track.album.artists:
                for artist in track.album.artists:
                    artists[artist.name] += 1
        
        return {
            "total_tracks": len(history),
            "unique_artists": len(artists),
            "days": len(set(e.date for e in history)),
            "top_artists": [name for name, _ in artists.most_common(5)]
        }
    
    period1 = get_period_stats(period1_start, period1_end)
    period2 = get_period_stats(period2_start, period2_end)
    
    # Calcul différences
    track_diff = period2["total_tracks"] - period1["total_tracks"]
    artist_diff = period2["unique_artists"] - period1["unique_artists"]
    
    return {
        "period1": {
            "range": f"{period1_start} to {period1_end}",
            **period1
        },
        "period2": {
            "range": f"{period2_start} to {period2_end}",
            **period2
        },
        "changes": {
            "tracks_difference": track_diff,
            "tracks_change_percent": round((track_diff / period1["total_tracks"] * 100), 1) if period1["total_tracks"] > 0 else 0,
            "artists_difference": artist_diff,
            "activity_intensity": "increased" if track_diff > 0 else "decreased"
        }
    }


@router.get("/listening-heatmap")
async def listening_heatmap(
    days: int = Query(90, ge=1, le=365, description="Nombre de jours"),
    db: Session = Depends(get_db)
):
    """Heatmap d'écoute par heure et jour."""
    cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
    
    history = db.query(ListeningHistory).filter(
        ListeningHistory.date >= cutoff_date
    ).all()
    
    # Matrice heure x jour
    heatmap = {}
    for entry in history:
        dt = datetime.fromisoformat(entry.date)
        weekday = dt.strftime('%A')
        hour = datetime.fromtimestamp(entry.timestamp).hour
        
        key = f"{weekday}_{hour}"
        heatmap[key] = heatmap.get(key, 0) + 1
    
    # Formater pour Recharts
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    data = []
    
    for hour in range(24):
        row = {"hour": f"{hour}:00"}
        for weekday in weekdays:
            key = f"{weekday}_{hour}"
            row[weekday] = heatmap.get(key, 0)
        data.append(row)
    
    return {
        "period_days": days,
        "data": data,
        "max_value": max(heatmap.values()) if heatmap else 0
    }


@router.get("/mood-timeline")
async def mood_timeline(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Timeline des moods par jour."""
    cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
    
    history = db.query(ListeningHistory).join(Track).join(Album).filter(
        ListeningHistory.date >= cutoff_date
    ).all()
    
    # Mood par jour
    daily_moods = defaultdict(lambda: Counter())
    
    for entry in history:
        track = entry.track
        album = track.album
        
        if album and album.album_metadata:
            metadata = album.album_metadata
            mood = "neutral"
            
            if metadata.ai_info:
                ai_info_lower = metadata.ai_info.lower()
                if 'énergie' in ai_info_lower or 'energetic' in ai_info_lower:
                    mood = "energetic"
                elif 'calme' in ai_info_lower or 'calm' in ai_info_lower:
                    mood = "calm"
                elif 'mélanc' in ai_info_lower or 'melancholic' in ai_info_lower:
                    mood = "melancholic"
                elif 'joyeux' in ai_info_lower or 'joyful' in ai_info_lower:
                    mood = "joyful"
            
            daily_moods[entry.date][mood] += 1
    
    # Formater
    timeline = []
    for date in sorted(daily_moods.keys()):
        moods = daily_moods[date]
        total = sum(moods.values())
        timeline.append({
            "date": date,
            "energetic": moods.get('energetic', 0),
            "calm": moods.get('calm', 0),
            "melancholic": moods.get('melancholic', 0),
            "joyful": moods.get('joyful', 0),
            "neutral": moods.get('neutral', 0),
            "total": total
        })
    
    return {
        "period_days": days,
        "data": timeline
    }
