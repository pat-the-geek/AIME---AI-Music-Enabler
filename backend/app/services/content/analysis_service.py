"""Service pour analyser les patterns d'écoute et statistiques."""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict, Counter
from sqlalchemy.orm import Session

from app.models import ListeningHistory, Album, Artist, Image

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service pour analyser les patterns et statistiques d'écoute."""
    
    @staticmethod
    def analyze_listening_patterns(db: Session) -> Dict[str, Any]:
        """
        Analyser les patterns d'écoute (horaires, jours de semaine, corrélations).
        
        Args:
            db: Session base de données
            
        Returns:
            Dict avec patterns d'écoute détaillés
        """
        history = db.query(ListeningHistory).join(
            ListeningHistory.track
        ).join(Album).join(Album.artists).all()
        
        if not history:
            raise ValueError("Pas d'historique d'écoute")
        
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
        
        # Corrélations artistes
        artist_pairs = Counter()
        sorted_by_time = sorted(history, key=lambda x: x.timestamp)
        
        for i in range(len(sorted_by_time) - 1):
            entry1 = sorted_by_time[i]
            entry2 = sorted_by_time[i + 1]
            
            if entry2.timestamp - entry1.timestamp < 1800:
                track1 = entry1.track
                track2 = entry2.track
                
                if (track1.album and track1.album.artists and 
                    track2.album and track2.album.artists):
                    artist1 = track1.album.artists[0].name
                    artist2 = track2.album.artists[0].name
                    
                    if artist1 != artist2:
                        pair = tuple(sorted([artist1, artist2]))
                        artist_pairs[pair] += 1
        
        top_correlations = [
            {"artist1": pair[0], "artist2": pair[1], "count": count}
            for pair, count in artist_pairs.most_common(10)
        ]
        
        # Temps moyen par jour
        daily_listening = Counter()
        for entry in history:
            dt = datetime.fromtimestamp(entry.timestamp)
            date_str = dt.strftime('%Y-%m-%d')
            daily_listening[date_str] += 1
        
        avg_tracks_per_day = sum(daily_listening.values()) / len(daily_listening) if daily_listening else 0
        
        return {
            "total_tracks": len(history),
            "hourly_patterns": dict(sorted(hourly_patterns.items())),
            "weekday_patterns": dict(weekday_patterns),
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
    
    @staticmethod
    def detect_sessions(
        db: Session,
        min_gap: int = 1800
    ) -> Dict[str, Any]:
        """
        Détecter les sessions d'écoute continues.
        
        Args:
            db: Session base de données
            min_gap: Gap minimum entre sessions en secondes (default: 1800 = 30 min)
            
        Returns:
            Dict avec sessions détectées
        """
        history = db.query(ListeningHistory).order_by(
            ListeningHistory.timestamp
        ).all()
        
        sessions = []
        current_session = []
        last_timestamp = 0
        
        for entry in history:
            if last_timestamp and (entry.timestamp - last_timestamp) > min_gap:
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
            "average_session_length": sum(len(s) for s in sessions) / len(sessions) if sessions else 0,
            "sessions": sessions[:10]  # Top 10
        }
    
    @staticmethod
    def get_timeline_stats(
        db: Session,
        date: str
    ) -> Dict[str, Any]:
        """
        Obtenir les statistiques pour une jour spécifique.
        
        Args:
            db: Session base de données
            date: Date au format YYYY-MM-DD
            
        Returns:
            Dict avec stats du jour
        """
        # Convertir la date en timestamps Unix
        start_dt = datetime.strptime(f"{date} 00:00", "%Y-%m-%d %H:%M")
        start_timestamp = int(start_dt.timestamp())
        
        end_dt = datetime.strptime(f"{date} 23:59", "%Y-%m-%d %H:%M")
        end_timestamp = int(end_dt.timestamp())
        
        history = db.query(ListeningHistory).filter(
            ListeningHistory.timestamp >= start_timestamp,
            ListeningHistory.timestamp <= end_timestamp
        ).all()
        
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
        
        return {
            "date": date,
            "total_tracks": len(history),
            "unique_artists": len(unique_artists),
            "unique_albums": len(unique_albums),
            "peak_hour": peak_hour,
            "hourly_breakdown": dict(sorted(hour_counts.items()))
        }
    
    @staticmethod
    def get_listening_stats(
        db: Session,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtenir les statistiques d'écoute pour une période.
        
        Args:
            db: Session base de données
            start_date: Date début au format YYYY-MM-DD (optionnel)
            end_date: Date fin au format YYYY-MM-DD (optionnel)
            
        Returns:
            Dict avec statistiques d'écoute
        """
        query = db.query(ListeningHistory)
        
        if start_date:
            start_dt = datetime.strptime(f"{start_date} 00:00", "%Y-%m-%d %H:%M")
            start_timestamp = int(start_dt.timestamp())
            query = query.filter(ListeningHistory.timestamp >= start_timestamp)
        
        if end_date:
            end_dt = datetime.strptime(f"{end_date} 23:59", "%Y-%m-%d %H:%M")
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
        
        return {
            "total_tracks": len(history),
            "unique_artists": len(unique_artists),
            "unique_albums": len(unique_albums),
            "peak_hour": peak_hour,
            "total_duration_seconds": total_duration if total_duration > 0 else None,
            "start_date": start_date,
            "end_date": end_date
        }
