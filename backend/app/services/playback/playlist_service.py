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
        """
        Create a new playlist with optional initial tracks.

        Creates a new Playlist record in the database and automatically adds
        provided tracks with sequential positioning. Supports both manual playlists
        and AI-generated playlists with algorithm specifications.

        Args:
            db: SQLAlchemy database session for transaction management.
            name: Playlist name (displayed to users).
            algorithm: Generation algorithm type. Defaults to "manual".
                Valid values: 'manual', 'top_sessions', 'artist_correlations',
                'artist_flow', 'time_based', 'complete_albums', 'rediscovery',
                'ai_generated'
            ai_prompt: Optional AI generation prompt. Required if algorithm='ai_generated',
                ignored otherwise.
            track_ids: Optional list of track IDs to add initially. TrackIDs will be
                assigned sequential positions starting from 1.

        Returns:
            Playlist: The newly created Playlist object with:
                - id: Auto-generated database ID
                - name: The provided name
                - algorithm: The algorithm type
                - track_count: Count of tracks added (length of track_ids or 0)
                - created_at: Current timestamp
                - PlaylistTrack records created for each track

        Example:
            >>> db_session = get_db()
            >>> playlist = PlaylistService.create_playlist(
            ...     db_session,
            ...     name="My Favorite Artists",
            ...     algorithm="manual",
            ...     track_ids=[1, 5, 12, 18]
            ... )
            >>> print(f"Created playlist: {playlist.name} with {playlist.track_count} tracks")
            Created playlist: My Favorite Artists with 4 tracks

        Database Operations:
            - Single INSERT into Playlist table
            - N INSERTs into PlaylistTrack table (one per track_id)
            - Single COMMIT operation

        Logging:
            - Logs INFO with playlist name and track count on creation
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
        """
        List all playlists with pagination.

        Retrieves all playlists from the database, sorted by creation date
        (newest first). Pagination is supported via skip/limit parameters.

        Args:
            db: SQLAlchemy database session for query execution.
            skip: Number of playlists to skip (for pagination). Defaults to 0.
            limit: Maximum number of playlists to return. Defaults to 100.
                Recommended max: 1000 for performance reasons.

        Returns:
            List[Playlist]: Playlist objects sorted by created_at descending.
                Empty list if no playlists exist or if skip >= total count.

        Example:
            >>> db_session = get_db()
            >>> playlists = PlaylistService.list_playlists(db_session, skip=0, limit=10)
            >>> for p in playlists:
            ...     print(f"{p.name}: {p.track_count} tracks")
            My Favorites: 25 tracks
            Workout Mix: 30 tracks

        Performance Notes:
            - Uses ORDER BY created_at DESC for consistency
            - Single query with OFFSET and LIMIT clauses
            - Recommended to cache for frequently accessed endpoint
        """
        return db.query(Playlist).order_by(desc(Playlist.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_playlist(db: Session, playlist_id: int) -> Optional[Playlist]:
        """
        Retrieve a single playlist by ID.

        Fetches a specific playlist from the database by its unique ID.
        Returns None if the playlist does not exist.

        Args:
            db: SQLAlchemy database session for query execution.
            playlist_id: The database ID of the playlist to retrieve.

        Returns:
            Playlist: The playlist object if found, or None if not found.
                Includes all basic metadata but NOT tracks (use get_playlist_tracks).

        Example:
            >>> db_session = get_db()
            >>> playlist = PlaylistService.get_playlist(db_session, playlist_id=42)
            >>> if playlist:
            ...     print(f"Found: {playlist.name}")
            ... else:
            ...     print("Playlist not found")

        Performance Notes:
            - Single indexed query on playlist_id
            - Does not load related tracks
        """
        return db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    @staticmethod
    def get_playlist_tracks(db: Session, playlist_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all tracks in a playlist with metadata and statistics.

        Fetches all tracks in a playlist ordered by position, and calculates
        aggregate statistics including total duration, unique artist count,
        and unique album count.

        Args:
            db: SQLAlchemy database session for query execution.
            playlist_id: The database ID of the playlist whose tracks to retrieve.

        Returns:
            Dict containing:
                - tracks (List[Dict]): List of track entries, each with:
                    - track_id (int): Track ID
                    - position (int): Position in playlist (1-indexed)
                    - title (str): Track title
                    - artist (str): Comma-separated artist names
                    - album (str): Album title or "Unknown"
                    - duration_seconds (int|null): Track duration in seconds
                - total_duration_seconds (int|null): Total playlist duration,
                  or None if all tracks lack duration data
                - unique_artists (int): Count of distinct artists in playlist
                - unique_albums (int): Count of distinct albums in playlist

        Example:
            >>> db_session = get_db()
            >>> playlist_data = PlaylistService.get_playlist_tracks(db_session, 42)
            >>> print(f"Playlist has {len(playlist_data['tracks'])} tracks")
            >>> print(f"Total duration: {playlist_data['total_duration_seconds']}s")
            >>> print(f"Artists: {playlist_data['unique_artists']}")
            Playlist has 15 tracks
            Total duration: 3600s
            Artists: 5

        Performance Notes:
            - Fetches all tracks in single query with positioned ordering
            - Aggregates artist/album by collecting in memory (scales to ~1000 tracks)
            - Consider caching for frequently accessed playlists
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
        """
        Add a track to an existing playlist.

        Adds a single track to a playlist at the next available position
        (automatically increments track_count). Validates that the track exists
        before adding.

        Args:
            db: SQLAlchemy database session for transaction management.
            playlist_id: The database ID of the playlist to add to.
            track_id: The database ID of the track to add.

        Returns:
            bool: True if track was successfully added, False otherwise.
                Returns False if:
                - track_id does not exist
                - Database error during add

        Example:
            >>> db_session = get_db()
            >>> success = PlaylistService.add_track(db_session, playlist_id=42, track_id=105)
            >>> if success:
            ...     print("Track added successfully")
            ... else:
            ...     print("Failed to add track")

        Side Effects:
            - Increments the playlist.track_count field
            - Creates a new PlaylistTrack record at next sequential position

        Error Handling:
            - Logs errors and rolls back transaction on failure
            - Silent failure (returns False, doesn't raise)

        Logging:
            - Logs ERROR if track not found or database error occurs
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
        """
        Remove a track from a playlist.

        Removes a specific track from a playlist and decrements the track_count.
        If the track is not in the playlist, returns False without error.

        Args:
            db: SQLAlchemy database session for transaction management.
            playlist_id: The database ID of the playlist to remove from.
            track_id: The database ID of the track to remove.

        Returns:
            bool: True if track was successfully removed, False if:
                - Track is not in the playlist
                - Database error during removal

        Example:
            >>> db_session = get_db()
            >>> success = PlaylistService.remove_track(db_session, 42, 105)
            >>> if success:
            ...     print("Track removed")

        Side Effects:
            - Decrements playlist.track_count by 1 (minimum 0)
            - Deletes PlaylistTrack record

        Error Handling:
            - Logs errors and rolls back transaction
            - Returns False on any error (no exceptions raised)

        Logging:
            - Logs ERROR if database error occurs
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
        """
        Permanently delete an entire playlist and all its track associations.

        Removes a playlist and all associated PlaylistTrack records from the
        database. This is a destructive operation.

        Args:
            db: SQLAlchemy database session for transaction management.
            playlist_id: The database ID of the playlist to delete.

        Returns:
            bool: True if playlist was successfully deleted, False if:
                - playlist_id does not exist
                - Database error during deletion

        Example:
            >>> db_session = get_db()
            >>> success = PlaylistService.delete_playlist(db_session, playlist_id=42)
            >>> if success:
            ...     print("Playlist deleted")

        Side Effects:
            - Deletes Playlist record
            - Deletes all associated PlaylistTrack records (cascade)
            - Operation cannot be reversed without database backup

        Error Handling:
            - Logs errors and rolls back transaction
            - Returns False on error (no exceptions raised)

        Logging:
            - Logs INFO on successful deletion
            - Logs ERROR on database failure
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
        """
        Export a playlist in a specific file format.

        Exports all tracks in a playlist to a specified format suitable for
        external applications, backup, or sharing. Supports multiple standard
        and custom formats.

        Args:
            db: SQLAlchemy database session for query execution.
            playlist_id: The database ID of the playlist to export.
            format: Export format. Valid values:
                - 'm3u': M3U extended format (media player compatible)
                - 'json': JSON format (programmatic access)
                - 'csv': CSV format (spreadsheet compatible)
                - 'txt': Plain text format (human-readable)

        Returns:
            Optional[Dict]: Dictionary with export data, or None if playlist not found.
                Structure varies by format:

                M3U format:
                {
                    "format": "m3u",
                    "content": "#EXTM3U\n#EXTINF:180,..."
                }

                JSON format:
                {
                    "format": "json",
                    "content": {
                        "name": "Playlist Name",
                        "algorithm": "manual",
                        "created_at": "2024-02-15T...",
                        "tracks": [...]
                    }
                }

                CSV/TXT formats: string in "content" field

        Example:
            >>> db_session = get_db()
            >>> export = PlaylistService.export_playlist(db_session, 42, format='json')
            >>> if export:
            ...     json_data = json.loads(json.dumps(export['content']))
            ...     print(f"Exported {len(json_data['tracks'])} tracks")

        Format Details:
            - M3U: Standard for media players, includes duration and artist
            - JSON: Fully structured, preserves all metadata
            - CSV: Spreadsheet-friendly, comma-separated artist names
            - TXT: Simple numbered list, human-readable

        Performance Notes:
            - Fetches all tracks in playlist into memory
            - Processing time scales linearly with track count
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
        """
        Generate a playlist using one of several generation algorithms.

        Creates a list of track IDs by applying a specified generation algorithm.
        Supports multiple strategies for building playlists from listening history,
        artist correlations, and AI-based generation.

        Args:
            db: SQLAlchemy database session for data access.
            ai_service: AIService instance for 'ai_generated' algorithm.
                Ignored for other algorithms.
            algorithm: Generation algorithm to use. Valid values:
                - 'manual': No generation (returns empty list)
                - 'top_sessions': Tracks from longest listening sessions
                - 'artist_correlations': Artists frequently played together
                - 'artist_flow': Natural artist transitions from history
                - 'time_based': Tracks from peak listening hours
                - 'complete_albums': Full albums that were played throughly
                - 'rediscovery': Loved tracks not recently played
                - 'ai_generated': AI-generated via prompt (requires ai_prompt)
            max_tracks: Maximum number of tracks to generate. Defaults to 25.
                All algorithms respect this limit.
            ai_prompt: Optional prompt for AI generation. Required when
                algorithm='ai_generated'. Example: "Play upbeat electronic music"

        Returns:
            List[int]: List of track IDs in recommended order.
                Empty list if algorithm fails or generates no tracks.
                Maximum length = max_tracks.

        Raises:
            ValueError: If algorithm is not recognized.
                Message: "Algorithme invalide: {algorithm}"
            ValueError: If ai_prompt is missing for 'ai_generated' algorithm.
                Message: "Prompt IA requis pour ai_generated"

        Example:
            >>> db_session = get_db()
            >>> ai_service = AIService(...)
            >>> track_ids = await PlaylistService.generate_playlist(
            ...     db_session,
            ...     ai_service,
            ...     algorithm='top_sessions',
            ...     max_tracks=25
            ... )
            >>> print(f"Generated {len(track_ids)} tracks")

        Algorithm Details:
            - top_sessions: Groups history by 30-minute gaps, sorts by session
              length, yields all tracks from longest sessions
            - artist_correlations: Builds artist pairs from sessions, selects
              top correlations and yields their tracks
            - artist_flow: Uses Markov-like transitions between artists
            - time_based: Filters by peak listening hour
            - complete_albums: Finds albums with 5+ plays, yields full albums
            - rediscovery: Returns loved tracks not played in 30 days
            - ai_generated: Uses AIService.generate_playlist_by_prompt()

        Performance Notes:
            - Async method; must be awaited
            - Algorithms without AI are synchronous within async context
            - Full listening history loaded for analysis (memory scaling)
            - May timeout for very large collections (>10k tracks)

        Error Handling:
            - Returns empty list on algorithm error (no exceptions)
            - Logs errors for debugging

        Logging:
            - Logs INFO when generation starts
            - Logs ERROR if algorithm fails
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
        """
        Generate playlist from longest listening sessions.

        Analyzes listening history to identify continuous listening sessions
        (separated by gaps >30 minutes) and selects tracks from the longest
        sessions first. Useful for discovering cohesive listening patterns.

        Args:
            db: SQLAlchemy database session.
            max_tracks: Maximum tracks to return.

        Returns:
            List[int]: Track IDs from longest sessions, up to max_tracks.
                Empty list if no listening history or database error.

        Implementation:
            - Session gap threshold: 1800 seconds (30 minutes)
            - Sessions sorted by length (longest first)
            - Duplicates removed when building result

        Logging:
            - Logs ERROR if query fails
        """
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
        """
        Generate playlist of loved but recently-unplayed tracks.

        Identifies tracks that have been marked as "loved" (in listening history)
        but haven't been played in the last 30 days. Useful for resurface favorite
        tracks that may have been forgotten.

        Args:
            db: SQLAlchemy database session.
            max_tracks: Maximum tracks to return.

        Returns:
            List[int]: Track IDs of loved but recent-unplayed tracks.
                Empty list if no matches or database error.

        Time Window:
            - Recent = last 30 days
            - Tracks excluded from result if played within this window

        Logging:
            - Logs ERROR if query fails
        """
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
        """
        Generate playlist using AI-based generation from a text prompt.

        Uses an AIService instance to generate track recommendations based on
        a natural language prompt. Samples from available tracks and uses the
        AI service to generate a ranked list matching the prompt.

        Args:
            db: SQLAlchemy database session.
            ai_service: Configured AIService instance for generation.
            max_tracks: Maximum tracks to return.
            prompt: Natural language prompt describing desired playlist.
                Example: "Upbeat electronic music for coding"

        Returns:
            List[int]: Track IDs selected by AI, up to max_tracks.
                Empty list if AI request fails or no matches.

        Implementation:
            - Samples 200 tracks from database with artists/albums
            - Sends to AIService.generate_playlist_by_prompt()
            - Returns ranked results truncated to max_tracks

        Error Handling:
            - Logs ERROR and returns empty list on exception
            - No exceptions raised

        Performance:
            - Async method; must be awaited
            - AI service latency 2-10 seconds typical
        """
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
