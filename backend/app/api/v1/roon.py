"""Routes API pour le contrôle Roon."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.roon_service import RoonService
from app.core.config import get_settings

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


# ============================================================================
# Endpoints
# ============================================================================

def get_roon_service() -> RoonService:
    """Initialiser le service Roon."""
    settings = get_settings()
    roon_config = settings.secrets.get('roon', {})
    
    if not roon_config.get('server'):
        raise HTTPException(status_code=503, detail="Roon non configuré")
    
    roon_service = RoonService(
        server=roon_config.get('server'),
        token=roon_config.get('token')
    )
    
    if not roon_service.is_connected():
        raise HTTPException(status_code=503, detail="Impossible de se connecter à Roon")
    
    return roon_service


@router.get("/zones")
async def get_zones():
    """Récupérer les zones Roon disponibles."""
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
            raise HTTPException(status_code=500, detail="Erreur démarrage lecture")
        
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
