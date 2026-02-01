"""Service pour gérer les playlists."""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.playlist import Playlist, PlaylistTrack
from app.models.track import Track

logger = logging.getLogger(__name__)


class PlaylistService:
    """Service pour les opérations sur les playlists."""
    
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
            db: Session de base de données
            name: Nom de la playlist
            algorithm: Type d'algorithme ('manual', 'top_sessions', 'ai_generated')
            ai_prompt: Prompt IA si algorithm='ai_generated'
            track_ids: Liste des IDs de tracks à ajouter
        
        Returns:
            Playlist créée
        """
        playlist = Playlist(
            name=name,
            algorithm=algorithm,
            ai_prompt=ai_prompt,
            track_count=0
        )
        
        db.add(playlist)
        db.flush()  # Pour obtenir l'ID
        
        # Ajouter les tracks si fournis
        if track_ids:
            for position, track_id in enumerate(track_ids):
                playlist_track = PlaylistTrack(
                    playlist_id=playlist.id,
                    track_id=track_id,
                    position=position
                )
                db.add(playlist_track)
            
            playlist.track_count = len(track_ids)
        
        db.commit()
        db.refresh(playlist)
        
        logger.info(f"✅ Playlist créée: {name} ({playlist.track_count} tracks)")
        return playlist
    
    @staticmethod
    def get_playlist(db: Session, playlist_id: int) -> Optional[Playlist]:
        """Récupérer une playlist par son ID.
        
        Args:
            db: Session de base de données
            playlist_id: ID de la playlist
        
        Returns:
            Playlist ou None
        """
        return db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    @staticmethod
    def get_all_playlists(db: Session, skip: int = 0, limit: int = 100) -> List[Playlist]:
        """Récupérer toutes les playlists.
        
        Args:
            db: Session de base de données
            skip: Nombre d'éléments à sauter
            limit: Nombre maximum d'éléments
        
        Returns:
            Liste de playlists
        """
        return db.query(Playlist).order_by(desc(Playlist.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_playlist_tracks(db: Session, playlist_id: int) -> List[Track]:
        """Récupérer les tracks d'une playlist dans l'ordre.
        
        Args:
            db: Session de base de données
            playlist_id: ID de la playlist
        
        Returns:
            Liste de tracks ordonnés
        """
        playlist_tracks = (
            db.query(PlaylistTrack)
            .filter(PlaylistTrack.playlist_id == playlist_id)
            .order_by(PlaylistTrack.position)
            .all()
        )
        
        # Récupérer les tracks dans l'ordre
        tracks = []
        for pt in playlist_tracks:
            track = db.query(Track).filter(Track.id == pt.track_id).first()
            if track:
                tracks.append(track)
        
        return tracks
    
    @staticmethod
    def add_track_to_playlist(db: Session, playlist_id: int, track_id: int) -> bool:
        """Ajouter un track à une playlist.
        
        Args:
            db: Session de base de données
            playlist_id: ID de la playlist
            track_id: ID du track à ajouter
        
        Returns:
            True si succès, False sinon
        """
        try:
            # Vérifier que le track existe
            track = db.query(Track).filter(Track.id == track_id).first()
            if not track:
                logger.error(f"Track {track_id} non trouvé")
                return False
            
            # Obtenir la position suivante
            max_position = (
                db.query(PlaylistTrack)
                .filter(PlaylistTrack.playlist_id == playlist_id)
                .count()
            )
            
            # Ajouter le track
            playlist_track = PlaylistTrack(
                playlist_id=playlist_id,
                track_id=track_id,
                position=max_position
            )
            db.add(playlist_track)
            
            # Mettre à jour le compteur
            playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
            if playlist:
                playlist.track_count += 1
            
            db.commit()
            logger.info(f"✅ Track {track_id} ajouté à la playlist {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur ajout track à playlist: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def remove_track_from_playlist(db: Session, playlist_id: int, track_id: int) -> bool:
        """Retirer un track d'une playlist.
        
        Args:
            db: Session de base de données
            playlist_id: ID de la playlist
            track_id: ID du track à retirer
        
        Returns:
            True si succès, False sinon
        """
        try:
            playlist_track = (
                db.query(PlaylistTrack)
                .filter(
                    PlaylistTrack.playlist_id == playlist_id,
                    PlaylistTrack.track_id == track_id
                )
                .first()
            )
            
            if not playlist_track:
                logger.error(f"Track {track_id} non trouvé dans playlist {playlist_id}")
                return False
            
            # Supprimer le track
            db.delete(playlist_track)
            
            # Mettre à jour le compteur
            playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
            if playlist:
                playlist.track_count = max(0, playlist.track_count - 1)
            
            db.commit()
            logger.info(f"✅ Track {track_id} retiré de la playlist {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur retrait track de playlist: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def delete_playlist(db: Session, playlist_id: int) -> bool:
        """Supprimer une playlist.
        
        Args:
            db: Session de base de données
            playlist_id: ID de la playlist
        
        Returns:
            True si succès, False sinon
        """
        try:
            playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
            if not playlist:
                logger.error(f"Playlist {playlist_id} non trouvée")
                return False
            
            db.delete(playlist)
            db.commit()
            logger.info(f"✅ Playlist {playlist_id} supprimée")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur suppression playlist: {e}")
            db.rollback()
            return False
