"""Routes API pour le contrôle Roon."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.config import get_settings
from app.api.v1.services import get_roon_service as get_roon_service_singleton

router = APIRouter()


# ============================================================================
# Schémas Pydantic
# ============================================================================

class RoonPlayRequest(BaseModel):
    """Requête pour jouer un track sur Roon."""
    zone_name: str
    track_title: str
    artist: str
    album: Optional[str] = None


class RoonControlRequest(BaseModel):
    """Requête pour contrôler la lecture."""
    zone_name: str
    control: str  # play, pause, stop, next, previous


class RoonPlayTrackByIdRequest(BaseModel):
    """Requête pour jouer un track par son ID (depuis la base de données)."""
    zone_name: str
    track_id: int


class RoonPlayPlaylistRequest(BaseModel):
    """Requête pour jouer une playlist entière sur Roon."""
    zone_name: str
    playlist_id: int


# ============================================================================
# Helpers
# ============================================================================

def is_roon_enabled() -> bool:
    """Vérifier si le contrôle Roon est activé."""
    settings = get_settings()
    roon_control_config = settings.app_config.get('roon_control', {})
    return roon_control_config.get('enabled', False)


def check_roon_enabled():
    """Vérifier si Roon est activé, sinon lever une exception."""
    if not is_roon_enabled():
        raise HTTPException(
            status_code=403,
            detail="Le contrôle Roon n'est pas activé. Activez-le dans config/app.json (roon_control.enabled)"
        )


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/status")
async def get_roon_status():
    """Vérifier si le contrôle Roon est activé et disponible."""
    enabled = is_roon_enabled()
    
    if not enabled:
        return {
            "enabled": False,
            "available": False,
            "message": "Contrôle Roon désactivé"
        }
    
    # Vérifier la configuration Roon
    settings = get_settings()
    roon_config = settings.secrets.get('roon', {})
    
    if not roon_config.get('server'):
        return {
            "enabled": True,
            "available": False,
            "message": "Roon non configuré (serveur manquant)"
        }
    
    # Utiliser le singleton pour éviter de créer plusieurs connexions
    try:
        roon_service = get_roon_service_singleton()
        if roon_service is None:
            return {
                "enabled": True,
                "available": False,
                "message": "Roon non configuré (serveur manquant)"
            }
        
        connected = roon_service.is_connected()
        
        return {
            "enabled": True,
            "available": connected,
            "message": "Roon disponible" if connected else "Impossible de se connecter à Roon"
        }
    except Exception as e:
        return {
            "enabled": True,
            "available": False,
            "message": f"Erreur: {str(e)}"
        }


def get_roon_service():
    """Obtenir l'instance singleton du service Roon."""
    roon_service = get_roon_service_singleton()
    
    if roon_service is None:
        raise HTTPException(status_code=503, detail="Roon non configuré")
    
    if not roon_service.is_connected():
        raise HTTPException(status_code=503, detail="Impossible de se connecter à Roon")
    
    return roon_service


@router.get("/zones")
async def get_zones():
    """Récupérer les zones Roon disponibles."""
    check_roon_enabled()  # Vérifier que Roon est activé
    
    try:
        roon_service = get_roon_service()
        zones = roon_service.get_zones()
        
        return {
            "zones": [
                {
                    "zone_id": zone_id,
                    "name": zone_info.get("display_name", "Unknown"),
                    "state": zone_info.get("state", "unknown")
                }
                for zone_id, zone_info in zones.items()
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")


@router.get("/now-playing")
async def get_now_playing():
    """Récupérer le morceau en cours de lecture."""
    check_roon_enabled()  # Vérifier que Roon est activé
    
    try:
        roon_service = get_roon_service()
        now_playing = roon_service.get_now_playing()
        
        if not now_playing:
            return {"message": "Aucune lecture en cours"}
        
        return now_playing
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")


@router.post("/play")
async def play_track(request: RoonPlayRequest):
    """Démarrer la lecture d'un track sur Roon."""
    check_roon_enabled()  # Vérifier que Roon est activé
    
    try:
        roon_service = get_roon_service()
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(request.zone_name)
        if not zone_id:
            zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{request.zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Démarrer la lecture
        success = roon_service.play_track(
            zone_or_output_id=zone_id,
            track_title=request.track_title,
            artist=request.artist,
            album=request.album
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors du démarrage de la lecture sur Roon. "
                       "Vérifiez que l'artiste et l'album sont présents dans votre bibliothèque Roon."
            )
        
        return {
            "message": f"Lecture démarrée: {request.track_title} - {request.artist}",
            "zone": request.zone_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")


@router.post("/control")
async def control_playback(request: RoonControlRequest):
    """Contrôler la lecture (play, pause, stop, next, previous)."""
    check_roon_enabled()  # Vérifier que Roon est activé
    
    try:
        roon_service = get_roon_service()
        
        # Vérifier la commande
        valid_controls = ['play', 'pause', 'stop', 'next', 'previous']
        if request.control not in valid_controls:
            raise HTTPException(
                status_code=400,
                detail=f"Contrôle invalide. Valeurs acceptées: {', '.join(valid_controls)}"
            )
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(request.zone_name)
        if not zone_id:
            zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{request.zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Exécuter la commande
        success = roon_service.playback_control(zone_id, request.control)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Erreur exécution commande '{request.control}'")
        
        return {
            "message": f"Commande '{request.control}' exécutée",
            "zone": request.zone_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")


@router.post("/pause-all")
async def pause_all():
    """Mettre en pause toutes les zones."""
    check_roon_enabled()  # Vérifier que Roon est activé
    
    try:
        roon_service = get_roon_service()
        success = roon_service.pause_all()
        
        if not success:
            raise HTTPException(status_code=500, detail="Erreur pause globale")
        
        return {"message": "Toutes les zones mises en pause"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Roon: {str(e)}")


@router.post("/play-track")
async def play_track_by_id(request: RoonPlayTrackByIdRequest):
    """Jouer un track depuis la base de données AIME sur Roon.
    
    Cette fonction facilite la lecture d'un track depuis l'interface web
    en utilisant directement l'ID du track dans la base de données.
    """
    check_roon_enabled()  # Vérifier que Roon est activé
    
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models import Track, Album, Artist
    
    # Créer une session de base de données
    db: Session = SessionLocal()
    
    try:
        # Récupérer le track depuis la base
        track = db.query(Track).filter(Track.id == request.track_id).first()
        if not track:
            raise HTTPException(status_code=404, detail=f"Track {request.track_id} non trouvé")
        
        # Récupérer l'album et les artistes
        album = db.query(Album).filter(Album.id == track.album_id).first()
        if not album:
            raise HTTPException(status_code=404, detail="Album non trouvé pour ce track")
        
        # Récupérer les artistes de l'album
        artists = [a.name for a in album.artists] if album.artists else ["Unknown"]
        artist_name = ", ".join(artists)
        
        # Initialiser Roon
        roon_service = get_roon_service()
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(request.zone_name)
        if not zone_id:
            zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{request.zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Démarrer la lecture
        success = roon_service.play_track(
            zone_or_output_id=zone_id,
            track_title=track.title,
            artist=artist_name,
            album=album.title
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors du démarrage de la lecture sur Roon. "
                       "Vérifiez que l'artiste et l'album sont présents dans votre bibliothèque Roon."
            )
        
        return {
            "message": f"Lecture démarrée: {track.title} - {artist_name}",
            "track": {
                "id": track.id,
                "title": track.title,
                "artist": artist_name,
                "album": album.title
            },
            "zone": request.zone_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        db.close()


@router.post("/play-playlist")
async def play_playlist(request: RoonPlayPlaylistRequest):
    """Jouer une playlist entière sur Roon.
    
    Cette fonction permet de démarrer la lecture d'une playlist
    en jouant le premier track, puis les suivants automatiquement.
    """
    check_roon_enabled()  # Vérifier que Roon est activé
    
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models import Playlist, PlaylistTrack, Track, Album
    
    db: Session = SessionLocal()
    
    try:
        # Récupérer la playlist
        playlist = db.query(Playlist).filter(Playlist.id == request.playlist_id).first()
        if not playlist:
            raise HTTPException(status_code=404, detail=f"Playlist {request.playlist_id} non trouvée")
        
        # Récupérer les tracks de la playlist
        playlist_tracks = db.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == request.playlist_id
        ).order_by(PlaylistTrack.position).all()
        
        if not playlist_tracks:
            raise HTTPException(status_code=400, detail="La playlist est vide")
        
        # Récupérer le premier track
        first_track_id = playlist_tracks[0].track_id
        first_track = db.query(Track).filter(Track.id == first_track_id).first()
        
        if not first_track:
            raise HTTPException(status_code=404, detail="Premier track non trouvé")
        
        # Récupérer l'album et les artistes
        album = db.query(Album).filter(Album.id == first_track.album_id).first()
        if not album:
            raise HTTPException(status_code=404, detail="Album non trouvé")
        
        artists = [a.name for a in album.artists] if album.artists else ["Unknown"]
        artist_name = ", ".join(artists)
        
        # Initialiser Roon
        roon_service = get_roon_service()
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(request.zone_name)
        if not zone_id:
            zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{request.zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Démarrer la lecture du premier track
        success = roon_service.play_track(
            zone_or_output_id=zone_id,
            track_title=first_track.title,
            artist=artist_name,
            album=album.title
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors du démarrage de la lecture sur Roon. "
                       "Vérifiez que l'artiste et l'album sont présents dans votre bibliothèque Roon."
            )
        
        # Ajouter les autres tracks à la queue
        queued_count = 0
        for i in range(1, len(playlist_tracks)):
            track_id = playlist_tracks[i].track_id
            track = db.query(Track).filter(Track.id == track_id).first()
            if track:
                track_album = db.query(Album).filter(Album.id == track.album_id).first()
                track_artists = [a.name for a in track_album.artists] if (track_album and track_album.artists) else ["Unknown"]
                track_artist_name = ", ".join(track_artists)
                
                # Ajouter à la queue
                if roon_service.queue_tracks(
                    zone_or_output_id=zone_id,
                    track_title=track.title,
                    artist=track_artist_name,
                    album=track_album.title if track_album else None
                ):
                    queued_count += 1
        
        return {
            "message": f"Lecture de la playlist démarrée: {playlist.name}",
            "playlist": {
                "id": playlist.id,
                "name": playlist.name,
                "track_count": len(playlist_tracks)
            },
            "now_playing": {
                "title": first_track.title,
                "artist": artist_name,
                "album": album.title
            },
            "queue": {
                "total_tracks": len(playlist_tracks),
                "queued_tracks": queued_count,
                "message": f"{queued_count} tracks supplémentaires en attente"
            },
            "zone": request.zone_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        db.close()


@router.get("/debug/playlist/{playlist_id}")
async def debug_playlist(playlist_id: int):
    """Afficher les infos d'une playlist pour diagnostic."""
    check_roon_enabled()
    
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models import Playlist, PlaylistTrack, Track, Album
    
    db: Session = SessionLocal()
    
    try:
        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist:
            raise HTTPException(status_code=404, detail=f"Playlist {playlist_id} non trouvée")
        
        playlist_tracks = db.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist_id
        ).order_by(PlaylistTrack.position).all()
        
        tracks_info = []
        for pt in playlist_tracks:
            track = db.query(Track).filter(Track.id == pt.track_id).first()
            if track:
                album = db.query(Album).filter(Album.id == track.album_id).first()
                artists = [a.name for a in album.artists] if (album and album.artists) else ["Unknown"]
                
                tracks_info.append({
                    "position": pt.position,
                    "track_id": track.id,
                    "title": track.title,
                    "artist": ", ".join(artists),
                    "album": album.title if album else "Unknown"
                })
        
        return {
            "playlist": {
                "id": playlist.id,
                "name": playlist.name,
                "algorithm": playlist.algorithm
            },
            "track_count": len(tracks_info),
            "tracks": tracks_info[:5]  # Montrer les 5 premiers tracks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        db.close()


class RoonPlaybackControlRequest(BaseModel):
    """Requête pour contrôler la lecture."""
    zone_name: str
    control: str  # play, pause, stop, next, previous


@router.post("/control")
async def control_playback(request: RoonPlaybackControlRequest):
    """Contrôler la lecture sur une zone Roon."""
    check_roon_enabled()
    
    try:
        roon_service = get_roon_service()
        
        # Récupérer l'ID de la zone
        zone_id = roon_service.get_zone_by_name(request.zone_name)
        if not zone_id:
            zones = roon_service.get_zones()
            zone_names = [z.get('display_name', 'Unknown') for z in zones.values()]
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{request.zone_name}' non trouvée. Zones disponibles: {', '.join(zone_names)}"
            )
        
        # Valider la commande
        valid_controls = ["play", "pause", "stop", "next", "previous"]
        if request.control.lower() not in valid_controls:
            raise HTTPException(
                status_code=400,
                detail=f"Commande invalide: {request.control}. Valides: {', '.join(valid_controls)}"
            )
        
        # Exécuter la commande
        success = roon_service.playback_control(zone_id, request.control.lower())
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'exécution de {request.control}")
        
        return {
            "message": f"Commande exécutée: {request.control}",
            "zone": request.zone_name,
            "control": request.control
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

