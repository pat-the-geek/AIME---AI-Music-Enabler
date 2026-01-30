"""Routes API pour les playlists."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Playlist, PlaylistTrack, Track, Album, Artist
from app.schemas import (
    PlaylistGenerate,
    PlaylistResponse,
    PlaylistDetailResponse,
    PlaylistTrackResponse,
    PlaylistExportFormat,
)
from app.services.playlist_generator import PlaylistGenerator
from app.services.ai_service import AIService
from app.core.config import get_settings

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
    playlists = db.query(Playlist).order_by(Playlist.created_at.desc()).all()
    
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


@router.post("/generate", response_model=PlaylistResponse, status_code=201)
async def generate_playlist(
    data: PlaylistGenerate,
    db: Session = Depends(get_db)
):
    """Générer une nouvelle playlist."""
    # Créer le générateur
    ai_service = get_ai_service()
    generator = PlaylistGenerator(db, ai_service)
    
    # Générer les track IDs
    try:
        track_ids = await generator.generate(
            algorithm=data.algorithm.value,
            max_tracks=data.max_tracks,
            ai_prompt=data.ai_prompt
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not track_ids:
        raise HTTPException(status_code=400, detail="Impossible de générer la playlist")
    
    # Créer nom si non fourni
    name = data.name if data.name else f"Playlist {data.algorithm.value}"
    
    # Créer la playlist
    playlist = Playlist(
        name=name,
        algorithm=data.algorithm.value,
        ai_prompt=data.ai_prompt,
        track_count=len(track_ids)
    )
    db.add(playlist)
    db.flush()
    
    # Ajouter les tracks
    for position, track_id in enumerate(track_ids, start=1):
        playlist_track = PlaylistTrack(
            playlist_id=playlist.id,
            track_id=track_id,
            position=position
        )
        db.add(playlist_track)
    
    db.commit()
    db.refresh(playlist)
    
    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        algorithm=playlist.algorithm,
        ai_prompt=playlist.ai_prompt,
        track_count=playlist.track_count,
        created_at=playlist.created_at
    )


@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
async def get_playlist(
    playlist_id: int,
    db: Session = Depends(get_db)
):
    """Détail d'une playlist."""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist non trouvée")
    
    # Récupérer les tracks
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
        
        tracks.append(PlaylistTrackResponse(
            track_id=track.id,
            position=pt.position,
            title=track.title,
            artist=', '.join(artists),
            album=album.title if album else "Unknown",
            duration_seconds=track.duration_seconds
        ))
    
    return PlaylistDetailResponse(
        id=playlist.id,
        name=playlist.name,
        algorithm=playlist.algorithm,
        ai_prompt=playlist.ai_prompt,
        track_count=playlist.track_count,
        created_at=playlist.created_at,
        tracks=tracks,
        total_duration_seconds=total_duration if total_duration > 0 else None,
        unique_artists=len(unique_artists),
        unique_albums=len(unique_albums)
    )


@router.delete("/{playlist_id}", status_code=204)
async def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db)
):
    """Supprimer une playlist."""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist non trouvée")
    
    db.delete(playlist)
    db.commit()
    
    return None


@router.get("/{playlist_id}/export")
async def export_playlist(
    playlist_id: int,
    format: PlaylistExportFormat,
    db: Session = Depends(get_db)
):
    """Exporter une playlist."""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist non trouvée")
    
    # Récupérer les tracks
    playlist_tracks = db.query(PlaylistTrack).filter(
        PlaylistTrack.playlist_id == playlist_id
    ).order_by(PlaylistTrack.position).all()
    
    if format == PlaylistExportFormat.M3U:
        lines = ["#EXTM3U"]
        for pt in playlist_tracks:
            track = pt.track
            album = track.album
            artists = [a.name for a in album.artists] if album and album.artists else ["Unknown"]
            lines.append(f"#EXTINF:{track.duration_seconds or 0},{', '.join(artists)} - {track.title}")
            lines.append("")  # Placeholder pour le chemin fichier
        
        return {"format": "m3u", "content": "\n".join(lines)}
    
    elif format == PlaylistExportFormat.JSON:
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
    
    elif format == PlaylistExportFormat.CSV:
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
    
    elif format == PlaylistExportFormat.TXT:
        lines = [f"Playlist: {playlist.name}", f"Algorithm: {playlist.algorithm}", ""]
        for pt in playlist_tracks:
            track = pt.track
            album = track.album
            artists = [a.name for a in album.artists] if album and album.artists else ["Unknown"]
            
            lines.append(f"{pt.position}. {', '.join(artists)} - {track.title} ({album.title if album else 'Unknown'})")
        
        return {"format": "txt", "content": "\n".join(lines)}
