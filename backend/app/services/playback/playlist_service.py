"""Service unifié pour la gestion des playlists et génération dynamique."""
import logging
from typing import List, Optional, Dict, Any
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import Playlist, PlaylistTrack, Track, Album, Artist, ListeningHistory
from app.services.external.ai_service import AIService

logger = logging.getLogger(__name__)


class PlaylistService:
    """Service unifié pour les opérations playlists et génération."""
    
    ALGORITHMS = [
        'top_sessions',
        'artist_correlations',
        'artist_flow',
        'time_based',
        'complete_albums',
        'rediscovery',
        'ai_generated'
    ]
    
    @staticmethod
    def create_playlist(
        db: Session,
        name: str,
        algorithm: str = "manual",
        ai_prompt: Optional[str] = None,
        track_ids: Optional[List[int]] = None
    ) -> Playlist:
        """Créer une nouvelle playlist.
        
        Args:
            db: Session base de données
            name: Nom de la playlist
            algorithm: Type d'algorithme ('manual', 'top_sessions', etc.)
            ai_prompt: Prompt IA si algorithm='ai_generated'
            track_ids: Liste des IDs de tracks
            
        Returns:
            Playlist créée
        """
        playlist = Playlist(
            name=name,
            algorithm=algorithm,
            ai_prompt=ai_prompt,
            track_count=len(track_ids) if track_ids else 0
        )
        
        db.add(playlist)
        db.flush()
        
        if track_ids:
            for position, track_id in enumerate(track_ids, start=1):
                playlist_track = PlaylistTrack(
                    playlist_id=playlist.id,
                    track_id=track_id,
                    position=position
                )
                db.add(playlist_track)
        
        db.commit()
        db.refresh(playlist)
        
        logger.info(f"✅ Playlist créée: {name} ({playlist.track_count} tracks)")
        return playlist
    
    @staticmethod
    def list_playlists(db: Session, skip: int = 0, limit: int = 100) -> List[Playlist]:
        """Récupérer toutes les playlists.
        
        Args:
            db: Session base de données
            skip: Nombre d'éléments à sauter
            limit: Nombre maximum d'éléments
            
        Returns:
            Liste de playlists
        """
        return db.query(Playlist).order_by(desc(Playlist.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_playlist(db: Session, playlist_id: int) -> Optional[Playlist]:
        """Récupérer une playlist par son ID.
        
        Args:
            db: Session base de données
            playlist_id: ID de la playlist
            
        Returns:
            Playlist ou None
        """
        return db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    @staticmethod
    def get_playlist_tracks(db: Session, playlist_id: int) -> List[Dict[str, Any]]:
        """Récupérer les tracks d'une playlist avec détails.
        
        Args:
            db: Session base de données
            playlist_id: ID de la playlist
            
        Returns:
            Liste des tracks avec métadonnées
        """
        playlist_tracks = db.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist_id
        ).order_by(PlaylistTrack.position).all()
        
        tracks = []
        total_duration = 0
        unique_artists = set()
        unique_albums = set()
        
        for pt in playlist_tracks:
            track = pt.track
            album = track.album
            artists = [a.name for a in album.artists] if album and album.artists else []
            
            if artists:
                unique_artists.update(artists)
            if album:
                unique_albums.add(album.title)
            
            if track.duration_seconds:
                total_duration += track.duration_seconds
            
            tracks.append({
                "track_id": track.id,
                "position": pt.position,
                "title": track.title,
                "artist": ', '.join(artists),
                "album": album.title if album else "Unknown",
                "duration_seconds": track.duration_seconds
            })
        
        return {
            "tracks": tracks,
            "total_duration_seconds": total_duration if total_duration > 0 else None,
            "unique_artists": len(unique_artists),
            "unique_albums": len(unique_albums)
        }
    
    @staticmethod
    def add_track(db: Session, playlist_id: int, track_id: int) -> bool:
        """Ajouter un track à une playlist.
        
        Args:
            db: Session base de données
            playlist_id: ID de la playlist
            track_id: ID du track
            
        Returns:
            True si succès
        """
        try:
            track = db.query(Track).filter(Track.id == track_id).first()
            if not track:
                logger.error(f"Track {track_id} non trouvé")
                return False
            
            max_position = db.query(PlaylistTrack).filter(
                PlaylistTrack.playlist_id == playlist_id
            ).count()
            
            playlist_track = PlaylistTrack(
                playlist_id=playlist_id,
                track_id=track_id,
                position=max_position
            )
            db.add(playlist_track)
            
            playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
            if playlist:
                playlist.track_count += 1
            
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Erreur ajout track: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def remove_track(db: Session, playlist_id: int, track_id: int) -> bool:
        """Retirer un track d'une playlist.
        
        Args:
            db: Session base de données
            playlist_id: ID de la playlist
            track_id: ID du track
            
        Returns:
            True si succès
        """
        try:
            playlist_track = db.query(PlaylistTrack).filter(
                PlaylistTrack.playlist_id == playlist_id,
                PlaylistTrack.track_id == track_id
            ).first()
            
            if not playlist_track:
                return False
            
            db.delete(playlist_track)
            
            playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
            if playlist:
                playlist.track_count = max(0, playlist.track_count - 1)
            
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Erreur retrait track: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def delete_playlist(db: Session, playlist_id: int) -> bool:
        """Supprimer une playlist.
        
        Args:
            db: Session base de données
            playlist_id: ID de la playlist
            
        Returns:
            True si succès
        """
        try:
            playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
            if not playlist:
                return False
            
            db.delete(playlist)
            db.commit()
            logger.info(f"✅ Playlist {playlist_id} supprimée")
            return True
        except Exception as e:
            logger.error(f"Erreur suppression playlist: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def export_playlist(db: Session, playlist_id: int, format: str) -> Optional[Dict[str, Any]]:
        """Exporter une playlist dans différents formats.
        
        Args:
            db: Session base de données
            playlist_id: ID de la playlist
            format: Format d'export ('m3u', 'json', 'csv', 'txt')
            
        Returns:
            Dict avec format et contenu
        """
        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist:
            return None
        
        playlist_tracks = db.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist_id
        ).order_by(PlaylistTrack.position).all()
        
        if format == 'm3u':
            lines = ["#EXTM3U"]
            for pt in playlist_tracks:
                track = pt.track
                album = track.album
                artists = [a.name for a in album.artists] if album and album.artists else ["Unknown"]
                lines.append(f"#EXTINF:{track.duration_seconds or 0},{', '.join(artists)} - {track.title}")
                lines.append("")
            
            return {"format": "m3u", "content": "\n".join(lines)}
        
        elif format == 'json':
            tracks = []
            for pt in playlist_tracks:
                track = pt.track
                album = track.album
                artists = [a.name for a in album.artists] if album and album.artists else []
                
                tracks.append({
                    "position": pt.position,
                    "title": track.title,
                    "artist": ', '.join(artists),
                    "album": album.title if album else "Unknown",
                    "duration_seconds": track.duration_seconds
                })
            
            return {
                "format": "json",
                "content": {
                    "name": playlist.name,
                    "algorithm": playlist.algorithm,
                    "created_at": playlist.created_at.isoformat(),
                    "tracks": tracks
                }
            }
        
        elif format == 'csv':
            lines = ["Position,Artist,Title,Album,Duration"]
            for pt in playlist_tracks:
                track = pt.track
                album = track.album
                artists = [a.name for a in album.artists] if album and album.artists else ["Unknown"]
                
                lines.append(
                    f"{pt.position},\"{', '.join(artists)}\",\"{track.title}\","
                    f"\"{album.title if album else 'Unknown'}\",{track.duration_seconds or 0}"
                )
            
            return {"format": "csv", "content": "\n".join(lines)}
        
        elif format == 'txt':
            lines = [f"Playlist: {playlist.name}", f"Algorithm: {playlist.algorithm}", ""]
            for pt in playlist_tracks:
                track = pt.track
                album = track.album
                artists = [a.name for a in album.artists] if album and album.artists else ["Unknown"]
                
                lines.append(f"{pt.position}. {', '.join(artists)} - {track.title} ({album.title if album else 'Unknown'})")
            
            return {"format": "txt", "content": "\n".join(lines)}
        
        return None
    
    @staticmethod
    async def generate_playlist(
        db: Session,
        ai_service: AIService,
        algorithm: str,
        max_tracks: int = 25,
        ai_prompt: Optional[str] = None
    ) -> List[int]:
        """Générer une playlist selon un algorithme.
        
        Args:
            db: Session base de données
            ai_service: Service IA pour ai_generated
            algorithm: Type d'algorithme ('top_sessions', 'ai_generated', etc.)
            max_tracks: Nombre de tracks à générer
            ai_prompt: Prompt IA si algorithm='ai_generated'
            
        Returns:
            Liste d'IDs de tracks
        """
        if algorithm not in PlaylistService.ALGORITHMS:
            raise ValueError(f"Algorithme invalide: {algorithm}")
        
        logger.info(f"Génération playlist: {algorithm} (max_tracks={max_tracks})")
        
        if algorithm == 'top_sessions':
            return PlaylistService._generate_top_sessions(db, max_tracks)
        elif algorithm == 'artist_correlations':
            return PlaylistService._generate_artist_correlations(db, max_tracks)
        elif algorithm == 'artist_flow':
            return PlaylistService._generate_artist_flow(db, max_tracks)
        elif algorithm == 'time_based':
            return PlaylistService._generate_time_based(db, max_tracks)
        elif algorithm == 'complete_albums':
            return PlaylistService._generate_complete_albums(db, max_tracks)
        elif algorithm == 'rediscovery':
            return PlaylistService._generate_rediscovery(db, max_tracks)
        elif algorithm == 'ai_generated':
            if not ai_prompt:
                raise ValueError("Prompt IA requis pour ai_generated")
            return await PlaylistService._generate_ai_generated(db, ai_service, max_tracks, ai_prompt)
        
        return []
    
    @staticmethod
    def _generate_top_sessions(db: Session, max_tracks: int) -> List[int]:
        """Générer playlist des sessions les plus longues."""
        try:
            history = db.query(ListeningHistory).order_by(ListeningHistory.timestamp).all()
            
            sessions = []
            current_session = []
            last_timestamp = 0
            
            for entry in history:
                if last_timestamp and (entry.timestamp - last_timestamp) > 1800:
                    if current_session:
                        sessions.append(current_session)
                    current_session = []
                
                current_session.append(entry.track_id)
                last_timestamp = entry.timestamp
            
            if current_session:
                sessions.append(current_session)
            
            sessions.sort(key=len, reverse=True)
            
            track_ids = []
            for session in sessions:
                for track_id in session:
                    if track_id not in track_ids:
                        track_ids.append(track_id)
                    if len(track_ids) >= max_tracks:
                        break
                if len(track_ids) >= max_tracks:
                    break
            
            return track_ids[:max_tracks]
        except Exception as e:
            logger.error(f"Erreur top_sessions: {e}")
            return []
    
    @staticmethod
    def _generate_artist_correlations(db: Session, max_tracks: int) -> List[int]:
        """Générer playlist d'artistes souvent écoutés ensemble."""
        try:
            history = db.query(ListeningHistory).order_by(ListeningHistory.timestamp).all()
            
            sessions = []
            current_session = []
            last_timestamp = 0
            
            for entry in history:
                if last_timestamp and (entry.timestamp - last_timestamp) > 1800:
                    if current_session:
                        sessions.append(current_session)
                    current_session = []
                current_session.append(entry.track_id)
                last_timestamp = entry.timestamp
            
            if current_session:
                sessions.append(current_session)
            
            artist_pairs = Counter()
            for session in sessions:
                artists_in_session = set()
                for track_id in session:
                    track = db.query(Track).get(track_id)
                    if track and track.album and track.album.artists:
                        for artist in track.album.artists:
                            artists_in_session.add(artist.id)
                
                artists_list = list(artists_in_session)
                for i, artist1 in enumerate(artists_list):
                    for artist2 in artists_list[i+1:]:
                        pair = tuple(sorted([artist1, artist2]))
                        artist_pairs[pair] += 1
            
            track_ids = []
            for (artist1_id, artist2_id), count in artist_pairs.most_common(10):
                tracks = db.query(Track).join(Album).join(Album.artists).filter(
                    Artist.id.in_([artist1_id, artist2_id])
                ).limit(max_tracks).all()
                
                for track in tracks:
                    if track.id not in track_ids:
                        track_ids.append(track.id)
                    if len(track_ids) >= max_tracks:
                        break
                
                if len(track_ids) >= max_tracks:
                    break
            
            return track_ids[:max_tracks]
        except Exception as e:
            logger.error(f"Erreur artist_correlations: {e}")
            return []
    
    @staticmethod
    def _generate_artist_flow(db: Session, max_tracks: int) -> List[int]:
        """Générer playlist avec transitions naturelles d'artistes."""
        try:
            history = db.query(ListeningHistory).order_by(ListeningHistory.timestamp).all()
            
            transitions = defaultdict(Counter)
            for i in range(len(history) - 1):
                track1 = db.query(Track).get(history[i].track_id)
                track2 = db.query(Track).get(history[i+1].track_id)
                
                if track1 and track2 and track1.album and track2.album:
                    if track1.album.artists and track2.album.artists:
                        artist1 = track1.album.artists[0].id
                        artist2 = track2.album.artists[0].id
                        if artist1 != artist2:
                            transitions[artist1][artist2] += 1
            
            track_ids = []
            current_artist = max(transitions.keys(), key=lambda a: sum(transitions[a].values())) if transitions else None
            
            while len(track_ids) < max_tracks and current_artist:
                tracks = db.query(Track).join(Album).join(Album.artists).filter(
                    Artist.id == current_artist
                ).limit(3).all()
                
                for track in tracks:
                    if track.id not in track_ids:
                        track_ids.append(track.id)
                        break
                
                if current_artist in transitions and transitions[current_artist]:
                    next_artist = transitions[current_artist].most_common(1)[0][0]
                    current_artist = next_artist
                else:
                    break
            
            return track_ids[:max_tracks]
        except Exception as e:
            logger.error(f"Erreur artist_flow: {e}")
            return []
    
    @staticmethod
    def _generate_time_based(db: Session, max_tracks: int) -> List[int]:
        """Générer playlist basée sur peak hours."""
        try:
            history = db.query(ListeningHistory).all()
            
            hour_counts = Counter()
            for entry in history:
                dt = datetime.fromtimestamp(entry.timestamp)
                hour_counts[dt.hour] += 1
            
            peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else 18
            
            track_ids = []
            for entry in history:
                dt = datetime.fromtimestamp(entry.timestamp)
                if dt.hour == peak_hour and entry.track_id not in track_ids:
                    track_ids.append(entry.track_id)
                    if len(track_ids) >= max_tracks:
                        break
            
            return track_ids[:max_tracks]
        except Exception as e:
            logger.error(f"Erreur time_based: {e}")
            return []
    
    @staticmethod
    def _generate_complete_albums(db: Session, max_tracks: int) -> List[int]:
        """Générer playlist d'albums écoutés en entier."""
        try:
            history = db.query(ListeningHistory).all()
            
            album_track_counts = Counter()
            for entry in history:
                track = db.query(Track).get(entry.track_id)
                if track:
                    album_track_counts[track.album_id] += 1
            
            track_ids = []
            for album_id, count in album_track_counts.most_common():
                if count >= 5:
                    tracks = db.query(Track).filter_by(album_id=album_id).all()
                    for track in tracks:
                        if track.id not in track_ids:
                            track_ids.append(track.id)
                        if len(track_ids) >= max_tracks:
                            break
                
                if len(track_ids) >= max_tracks:
                    break
            
            return track_ids[:max_tracks]
        except Exception as e:
            logger.error(f"Erreur complete_albums: {e}")
            return []
    
    @staticmethod
    def _generate_rediscovery(db: Session, max_tracks: int) -> List[int]:
        """Générer playlist de pistes aimées mais pas récentes."""
        try:
            loved_tracks = db.query(ListeningHistory.track_id).filter_by(loved=True).distinct().all()
            loved_track_ids = [t[0] for t in loved_tracks]
            
            thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())
            recent_tracks = db.query(ListeningHistory.track_id).filter(
                ListeningHistory.timestamp >= thirty_days_ago
            ).distinct().all()
            recent_track_ids = {t[0] for t in recent_tracks}
            
            track_ids = [tid for tid in loved_track_ids if tid not in recent_track_ids]
            
            return track_ids[:max_tracks]
        except Exception as e:
            logger.error(f"Erreur rediscovery: {e}")
            return []
    
    @staticmethod
    async def _generate_ai_generated(
        db: Session,
        ai_service: AIService,
        max_tracks: int,
        prompt: str
    ) -> List[int]:
        """Générer playlist par IA avec prompt."""
        try:
            tracks = db.query(Track).join(Album).join(Album.artists).limit(200).all()
            
            available_tracks = []
            for track in tracks:
                artists = [a.name for a in track.album.artists] if track.album and track.album.artists else []
                available_tracks.append({
                    'id': track.id,
                    'artist': ', '.join(artists) if artists else 'Unknown',
                    'title': track.title,
                    'album': track.album.title if track.album else 'Unknown'
                })
            
            track_ids = await ai_service.generate_playlist_by_prompt(prompt, available_tracks)
            
            return track_ids[:max_tracks]
        except Exception as e:
            logger.error(f"Erreur ai_generated: {e}")
            return []
