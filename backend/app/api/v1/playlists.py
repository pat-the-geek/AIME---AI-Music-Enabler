"""Routes API pour les playlists."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import (
    PlaylistCreate,
    PlaylistGenerate,
    PlaylistResponse,
    PlaylistDetailResponse,
    PlaylistExportFormat,
)
from app.services.playback import PlaylistService, RoonPlaybackService
from app.services.external.ai_service import AIService
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_ai_service():
    """Obtenir le service IA."""
    settings = get_settings()
    secrets = settings.secrets
    euria_config = secrets.get('euria', {})
    
    return AIService(
        url=euria_config.get('url'),
        bearer=euria_config.get('bearer'),
        max_attempts=euria_config.get('max_attempts', 5),
        default_error_message=euria_config.get('default_error_message', 'Aucune information disponible')
    )


@router.get("", response_model=List[PlaylistResponse])
async def list_playlists(
    db: Session = Depends(get_db)
):
    """Liste des playlists."""
    try:
        playlists = PlaylistService.list_playlists(db)
        return [
            PlaylistResponse(
                id=p.id,
                name=p.name,
                algorithm=p.algorithm,
                ai_prompt=p.ai_prompt,
                track_count=p.track_count,
                created_at=p.created_at
            )
            for p in playlists
        ]
    except Exception as e:
        logger.error(f"Erreur liste playlists: {e}")
        raise HTTPException(status_code=500, detail="Erreur liste playlists")


@router.post("", response_model=PlaylistResponse, status_code=201)
async def create_playlist(
    data: PlaylistCreate,
    db: Session = Depends(get_db)
):
    """Créer une nouvelle playlist manuelle."""
    try:
        playlist = PlaylistService.create_playlist(
            db, data.name, "manual", None, data.track_ids
        )
        
        return PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            algorithm=playlist.algorithm,
            ai_prompt=playlist.ai_prompt,
            track_count=playlist.track_count,
            created_at=playlist.created_at
        )
    except Exception as e:
        logger.error(f"Erreur création playlist: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate", response_model=PlaylistResponse, status_code=201)
async def generate_playlist(
    data: PlaylistGenerate,
    db: Session = Depends(get_db)
):
    """Générer une nouvelle playlist."""
    try:
        ai_service = get_ai_service()
        
        track_ids = await PlaylistService.generate_playlist(
            db, ai_service, data.algorithm.value, data.max_tracks, data.ai_prompt
        )
        
        if not track_ids:
            raise HTTPException(status_code=400, detail="Impossible de générer la playlist")
        
        name = data.name if data.name else f"Playlist {data.algorithm.value}"
        
        playlist = PlaylistService.create_playlist(
            db, name, data.algorithm.value, data.ai_prompt, track_ids
        )
        
        return PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            algorithm=playlist.algorithm,
            ai_prompt=playlist.ai_prompt,
            track_count=playlist.track_count,
            created_at=playlist.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur génération playlist: {e}")
        raise HTTPException(status_code=500, detail="Erreur génération")


@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
async def get_playlist(
    playlist_id: int,
    db: Session = Depends(get_db)
):
    """Détail d'une playlist."""
    try:
        playlist = PlaylistService.get_playlist(db, playlist_id)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist non trouvée")
        
        tracks_data = PlaylistService.get_playlist_tracks(db, playlist_id)
        
        return PlaylistDetailResponse(
            id=playlist.id,
            name=playlist.name,
            algorithm=playlist.algorithm,
            ai_prompt=playlist.ai_prompt,
            track_count=playlist.track_count,
            created_at=playlist.created_at,
            tracks=tracks_data["tracks"],
            total_duration_seconds=tracks_data["total_duration_seconds"],
            unique_artists=tracks_data["unique_artists"],
            unique_albums=tracks_data["unique_albums"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération playlist: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération")


@router.delete("/{playlist_id}", status_code=204)
async def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db)
):
    """Supprimer une playlist."""
    try:
        success = PlaylistService.delete_playlist(db, playlist_id)
        if not success:
            raise HTTPException(status_code=404, detail="Playlist non trouvée")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression playlist: {e}")
        raise HTTPException(status_code=500, detail="Erreur suppression")


@router.get("/{playlist_id}/export")
async def export_playlist(
    playlist_id: int,
    format: PlaylistExportFormat,
    db: Session = Depends(get_db)
):
    """Exporter une playlist."""
    try:
        result = PlaylistService.export_playlist(db, playlist_id, format.value)
        if not result:
            raise HTTPException(status_code=404, detail="Playlist non trouvée")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur export playlist: {e}")
        raise HTTPException(status_code=500, detail="Erreur export")


@router.post("/{playlist_id}/play-on-roon")
async def play_playlist_on_roon(
    playlist_id: int,
    zone_name: str,
    db: Session = Depends(get_db)
):
    """Jouer une playlist sur Roon."""
    try:
        settings = get_settings()
        roon_control_config = settings.app_config.get('roon_control', {})
        if not roon_control_config.get('enabled', False):
            raise HTTPException(status_code=403, detail="Le contrôle Roon n'est pas activé")
        
        result = RoonPlaybackService.play_playlist_on_roon(db, playlist_id, zone_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur playback Roon: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")



