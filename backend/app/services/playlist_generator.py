"""Générateur de playlists basées sur patterns d'écoute."""
from typing import List, Optional
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models import Track, ListeningHistory, Album, Artist
from app.services.external.ai_service import AIService

logger = logging.getLogger(__name__)


class PlaylistGenerator:
    """Générateur de playlists basées sur patterns d'écoute."""
    
    ALGORITHMS = [
        'top_sessions',
        'artist_correlations',
        'artist_flow',
        'time_based',
        'complete_albums',
        'rediscovery',
        'ai_generated'
    ]
    
    def __init__(self, db: Session, ai_service: AIService):
        self.db = db
        self.ai = ai_service
    
    async def generate(
        self, 
        algorithm: str, 
        max_tracks: int = 25,
        ai_prompt: Optional[str] = None
    ) -> List[int]:
        """Générer playlist selon algorithme choisi.
        
        Returns:
            Liste d'IDs de tracks
        """
        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"Algorithme invalide: {algorithm}")
        
        logger.info(f"Génération playlist: {algorithm} (max_tracks={max_tracks})")
        
        if algorithm == 'top_sessions':
            return await self._top_sessions(max_tracks)
        elif algorithm == 'artist_correlations':
            return await self._artist_correlations(max_tracks)
        elif algorithm == 'artist_flow':
            return await self._artist_flow(max_tracks)
        elif algorithm == 'time_based':
            return await self._time_based(max_tracks)
        elif algorithm == 'complete_albums':
            return await self._complete_albums(max_tracks)
        elif algorithm == 'rediscovery':
            return await self._rediscovery(max_tracks)
        elif algorithm == 'ai_generated':
            if not ai_prompt:
                raise ValueError("Prompt IA requis pour ai_generated")
            return await self._ai_generated(max_tracks, ai_prompt)
    
    async def _top_sessions(self, max_tracks: int) -> List[int]:
        """Pistes des sessions d'écoute les plus longues."""
        try:
            # Récupérer tout l'historique trié
            history = self.db.query(ListeningHistory).order_by(
                ListeningHistory.timestamp
            ).all()
            
            # Détecter sessions (gap < 30 min)
            sessions = []
            current_session = []
            last_timestamp = 0
            
            for entry in history:
                if last_timestamp and (entry.timestamp - last_timestamp) > 1800:
                    # Nouvelle session (gap > 30 min)
                    if current_session:
                        sessions.append(current_session)
                    current_session = []
                
                current_session.append(entry.track_id)
                last_timestamp = entry.timestamp
            
            if current_session:
                sessions.append(current_session)
            
            # Trier sessions par longueur
            sessions.sort(key=len, reverse=True)
            
            # Prendre tracks des sessions les plus longues
            track_ids = []
            for session in sessions:
                for track_id in session:
                    if track_id not in track_ids:  # Éviter doublons
                        track_ids.append(track_id)
                    if len(track_ids) >= max_tracks:
                        break
                if len(track_ids) >= max_tracks:
                    break
            
            return track_ids[:max_tracks]
            
        except Exception as e:
            logger.error(f"Erreur génération top_sessions: {e}")
            return []
    
    async def _artist_correlations(self, max_tracks: int) -> List[int]:
        """Artistes souvent écoutés ensemble."""
        try:
            # Récupérer l'historique
            history = self.db.query(ListeningHistory).order_by(
                ListeningHistory.timestamp
            ).all()
            
            # Créer sessions
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
            
            # Compter les paires d'artistes par session
            artist_pairs = Counter()
            for session in sessions:
                artists_in_session = set()
                for track_id in session:
                    track = self.db.query(Track).get(track_id)
                    if track and track.album and track.album.artists:
                        for artist in track.album.artists:
                            artists_in_session.add(artist.id)
                
                # Compter les paires
                artists_list = list(artists_in_session)
                for i, artist1 in enumerate(artists_list):
                    for artist2 in artists_list[i+1:]:
                        pair = tuple(sorted([artist1, artist2]))
                        artist_pairs[pair] += 1
            
            # Sélectionner tracks des artistes les plus corrélés
            track_ids = []
            for (artist1_id, artist2_id), count in artist_pairs.most_common(10):
                # Récupérer tracks de ces artistes
                tracks = self.db.query(Track).join(Album).join(Album.artists).filter(
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
            logger.error(f"Erreur génération artist_correlations: {e}")
            return []
    
    async def _artist_flow(self, max_tracks: int) -> List[int]:
        """Transitions naturelles entre artistes."""
        try:
            # Récupérer l'historique
            history = self.db.query(ListeningHistory).order_by(
                ListeningHistory.timestamp
            ).all()
            
            # Construire graphe de transitions
            transitions = defaultdict(Counter)
            for i in range(len(history) - 1):
                track1 = self.db.query(Track).get(history[i].track_id)
                track2 = self.db.query(Track).get(history[i+1].track_id)
                
                if track1 and track2 and track1.album and track2.album:
                    if track1.album.artists and track2.album.artists:
                        artist1 = track1.album.artists[0].id
                        artist2 = track2.album.artists[0].id
                        if artist1 != artist2:
                            transitions[artist1][artist2] += 1
            
            # Créer playlist en suivant les transitions
            track_ids = []
            current_artist = None
            
            # Commencer avec l'artiste le plus fréquent
            if transitions:
                current_artist = max(transitions.keys(), key=lambda a: sum(transitions[a].values()))
            
            while len(track_ids) < max_tracks and current_artist:
                # Ajouter un track de l'artiste actuel
                tracks = self.db.query(Track).join(Album).join(Album.artists).filter(
                    Artist.id == current_artist
                ).limit(3).all()
                
                for track in tracks:
                    if track.id not in track_ids:
                        track_ids.append(track.id)
                        break
                
                # Trouver l'artiste suivant
                if current_artist in transitions and transitions[current_artist]:
                    next_artist = transitions[current_artist].most_common(1)[0][0]
                    current_artist = next_artist
                else:
                    break
            
            return track_ids[:max_tracks]
            
        except Exception as e:
            logger.error(f"Erreur génération artist_flow: {e}")
            return []
    
    async def _time_based(self, max_tracks: int) -> List[int]:
        """Basé sur peak hours."""
        try:
            # Trouver l'heure la plus active
            history = self.db.query(ListeningHistory).all()
            
            hour_counts = Counter()
            for entry in history:
                dt = datetime.fromtimestamp(entry.timestamp)
                hour_counts[dt.hour] += 1
            
            peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else 18
            
            # Récupérer tracks écoutés à cette heure
            track_ids = []
            for entry in history:
                dt = datetime.fromtimestamp(entry.timestamp)
                if dt.hour == peak_hour and entry.track_id not in track_ids:
                    track_ids.append(entry.track_id)
                    if len(track_ids) >= max_tracks:
                        break
            
            return track_ids[:max_tracks]
            
        except Exception as e:
            logger.error(f"Erreur génération time_based: {e}")
            return []
    
    async def _complete_albums(self, max_tracks: int) -> List[int]:
        """Albums écoutés en entier."""
        try:
            # Compter les tracks par album dans l'historique
            history = self.db.query(ListeningHistory).all()
            
            album_track_counts = Counter()
            for entry in history:
                track = self.db.query(Track).get(entry.track_id)
                if track:
                    album_track_counts[track.album_id] += 1
            
            # Sélectionner albums avec le plus d'écoutes (>=5)
            track_ids = []
            for album_id, count in album_track_counts.most_common():
                if count >= 5:
                    tracks = self.db.query(Track).filter_by(album_id=album_id).all()
                    for track in tracks:
                        if track.id not in track_ids:
                            track_ids.append(track.id)
                        if len(track_ids) >= max_tracks:
                            break
                
                if len(track_ids) >= max_tracks:
                    break
            
            return track_ids[:max_tracks]
            
        except Exception as e:
            logger.error(f"Erreur génération complete_albums: {e}")
            return []
    
    async def _rediscovery(self, max_tracks: int) -> List[int]:
        """Pistes aimées mais pas écoutées récemment."""
        try:
            # Récupérer tracks aimés
            loved_tracks = self.db.query(ListeningHistory.track_id).filter_by(loved=True).distinct().all()
            loved_track_ids = [t[0] for t in loved_tracks]
            
            # Récupérer dernières écoutes (30 derniers jours)
            thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())
            recent_tracks = self.db.query(ListeningHistory.track_id).filter(
                ListeningHistory.timestamp >= thirty_days_ago
            ).distinct().all()
            recent_track_ids = {t[0] for t in recent_tracks}
            
            # Sélectionner tracks aimés mais pas récents
            track_ids = [tid for tid in loved_track_ids if tid not in recent_track_ids]
            
            return track_ids[:max_tracks]
            
        except Exception as e:
            logger.error(f"Erreur génération rediscovery: {e}")
            return []
    
    async def _ai_generated(self, max_tracks: int, prompt: str) -> List[int]:
        """Génération playlist par IA avec prompt personnalisé."""
        try:
            # Récupérer tracks disponibles
            tracks = self.db.query(Track).join(Album).join(Album.artists).limit(200).all()
            
            available_tracks = []
            for track in tracks:
                artists = [a.name for a in track.album.artists] if track.album and track.album.artists else []
                available_tracks.append({
                    'id': track.id,
                    'artist': ', '.join(artists) if artists else 'Unknown',
                    'title': track.title,
                    'album': track.album.title if track.album else 'Unknown'
                })
            
            # Appeler l'IA
            track_ids = await self.ai.generate_playlist_by_prompt(prompt, available_tracks)
            
            return track_ids[:max_tracks]
            
        except Exception as e:
            logger.error(f"Erreur génération ai_generated: {e}")
            return []
