"""Routes API pour les playlists."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Playlist, PlaylistTrack, Track, Album, Artist
from app.schemas import (
    PlaylistCreate,
    PlaylistGenerate,
    PlaylistResponse,
    PlaylistDetailResponse,
    PlaylistTrackResponse,
    PlaylistExportFormat,
)
from app.services.playlist_generator import PlaylistGenerator
from app.services.ai_service import AIService
from app.core.config import get_settings
from app.api.v1.services import get_roon_service

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


@router.post("", response_model=PlaylistResponse, status_code=201)
async def create_playlist(
    data: PlaylistCreate,
    db: Session = Depends(get_db)
):
    """Créer une nouvelle playlist manuelle."""
    # Créer la playlist
    playlist = Playlist(
        name=data.name,
        algorithm="manual",
        ai_prompt=None,
        track_count=len(data.track_ids)
    )
    db.add(playlist)
    db.flush()
    
    # Ajouter les tracks
    for position, track_id in enumerate(data.track_ids, start=1):
        # Vérifier que le track existe
        track = db.query(Track).filter(Track.id == track_id).first()
        if not track:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Track {track_id} non trouvé")
        
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


# ============================================================================
# Routes Contrôle Roon
# ============================================================================

@router.post("/{playlist_id}/play-on-roon")
async def play_playlist_on_roon(
    playlist_id: int,
    zone_name: str,
    db: Session = Depends(get_db)
):
    """Jouer une playlist sur Roon.
    
    Args:
        playlist_id: ID de la playlist
        zone_name: Nom de la zone Roon (ex: "Living Room")
        
    Returns:
        Statut de la lecture
    """
    # Vérifier que Roon est activé
    settings = get_settings()
    roon_control_config = settings.app_config.get('roon_control', {})
    if not roon_control_config.get('enabled', False):
        raise HTTPException(
            status_code=403,
            detail="Le contrôle Roon n'est pas activé"
        )
    
    # Récupérer la playlist
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist non trouvée")
    
    # Récupérer les tracks
    playlist_tracks = (
        db.query(PlaylistTrack)
        .filter(PlaylistTrack.playlist_id == playlist_id)
        .order_by(PlaylistTrack.position)
        .all()
    )
    
    if not playlist_tracks:
        raise HTTPException(status_code=400, detail="Playlist vide")
    
    # Initialiser Roon avec le singleton
    try:
        roon_service = get_roon_service()
        
        if roon_service is None:
            raise HTTPException(status_code=503, detail="Roon non configuré")
        
        if not roon_service.is_connected():
            raise HTTPException(status_code=503, detail="Impossible de se connecter à Roon")
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(zone_name)
        if not zone_id:
            available_zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in available_zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Jouer le premier track
        first_pt = playlist_tracks[0]
        first_track = first_pt.track
        album = first_track.album
        
        if not album:
            raise HTTPException(status_code=400, detail="Album non trouvé pour le premier track")
        
        artists = [a.name for a in album.artists] if album.artists else ["Unknown"]
        artist_name = ", ".join(artists)
        
        success = roon_service.play_track(
            zone_or_output_id=zone_id,
            track_title=first_track.title,
            artist=artist_name,
            album=album.title
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Erreur démarrage lecture sur Roon")
        
        return {
            "message": f"Playlist '{playlist.name}' en lecture sur {zone_name}",
            "playlist_id": playlist_id,
            "track_count": len(playlist_tracks),
            "first_track": first_track.title,
            "zone": zone_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")

