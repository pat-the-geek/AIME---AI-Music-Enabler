"""Routes API pour la génération de magazines musicaux."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.database import get_db
from app.services.magazine_generator_service import MagazineGeneratorService
from app.services.magazine_edition_service import MagazineEditionService
from app.services.external.ai_service import AIService
from app.services.spotify_service import SpotifyService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/generate")
async def generate_magazine(db: Session = Depends(get_db)):
    """Générer un magazine musical complet avec 5 pages."""
    try:
        # Initialiser le service IA
        settings = get_settings()
        secrets = settings.secrets
        euria_config = secrets.get('euria', {})
        spotify_config = secrets.get('spotify', {})
        
        logger.info(f"📖 Initialisation Magazine - Euria config: {bool(euria_config)}")
        
        ai_service = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer')
        )
        
        spotify_service = SpotifyService(
            client_id=spotify_config.get('client_id'),
            client_secret=spotify_config.get('client_secret')
        )
        
        # Générer le magazine
        magazine_service = MagazineGeneratorService(db, ai_service, spotify_service)
        magazine = await magazine_service.generate_magazine()
        
        logger.info(f"✅ Magazine généré: {magazine['id']}")
        return magazine
        
    except Exception as e:
        logger.error(f"❌ Erreur génération magazine: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur génération magazine: {str(e)}")


@router.get("/refresh-status")
async def get_magazine_refresh_status(db: Session = Depends(get_db)):
    """Récupérer le statut actuel du rafraîchissement des albums en arrière-plan."""
    try:
        # Initialiser le service IA (simple instanciation pour accéder à la méthode)
        settings = get_settings()
        secrets = settings.secrets
        euria_config = secrets.get('euria', {})
        spotify_config = secrets.get('spotify', {})
        
        ai_service = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer')
        )
        
        spotify_service = SpotifyService(
            client_id=spotify_config.get('client_id'),
            client_secret=spotify_config.get('client_secret')
        )
        
        magazine_service = MagazineGeneratorService(db, ai_service, spotify_service)
        status = magazine_service.get_refresh_status()
        
        return {
            "success": True,
            "refresh_status": status,
            "message": f"Albums en cours d'amélioration: {status['currently_processing'] or 'Aucun'}"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur statut rafraîchissement: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur statut: {str(e)}")


@router.post("/regenerate")
async def regenerate_magazine(db: Session = Depends(get_db)):
    """Regénérer un nouveau magazine (alias pour generate)."""
    return await generate_magazine(db)


@router.get("/editions")
async def list_editions(limit: int = 50, db: Session = Depends(get_db)):
    """
    Lister toutes les éditions de magazines disponibles.
    
    Args:
        limit: Nombre maximum d'éditions à retourner (défaut: 50)
    
    Returns:
        Liste des métadonnées des éditions
    """
    try:
        edition_service = MagazineEditionService(db)
        editions = edition_service.list_editions(limit=limit)
        
        logger.info(f"📚 Liste de {len(editions)} éditions retournée")
        return {
            "count": len(editions),
            "editions": editions
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du listage des éditions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur listage éditions: {str(e)}")


@router.get("/editions/random")
async def get_random_edition(db: Session = Depends(get_db)):
    """
    Récupérer une édition aléatoire parmi les disponibles.
    
    Returns:
        Édition complète de magazine
    """
    try:
        edition_service = MagazineEditionService(db)
        edition = edition_service.get_random_edition()
        
        if not edition:
            raise HTTPException(status_code=404, detail="Aucune édition disponible")
        
        logger.info(f"🎲 Édition aléatoire {edition['id']} retournée")
        return edition
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération aléatoire: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur récupération aléatoire: {str(e)}")


@router.get("/editions/{edition_id}")
async def get_edition(edition_id: str, db: Session = Depends(get_db)):
    """
    Récupérer une édition spécifique par son ID.
    
    Args:
        edition_id: ID de l'édition (format: 2026-02-03-001)
    
    Returns:
        Édition complète de magazine
    """
    try:
        edition_service = MagazineEditionService(db)
        edition = edition_service.load_edition(edition_id)
        
        if not edition:
            raise HTTPException(status_code=404, detail=f"Édition {edition_id} non trouvée")
        
        logger.info(f"📖 Édition {edition_id} retournée")
        return edition
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération de l'édition: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur récupération édition: {str(e)}")


@router.post("/editions/generate-batch")
async def generate_batch(count: int = 10, delay_minutes: int = 30, db: Session = Depends(get_db)):
    """
    Générer un lot d'éditions (utilisé par le scheduler).
    
    Args:
        count: Nombre d'éditions à générer (défaut: 10)
        delay_minutes: Délai entre chaque génération en minutes (défaut: 30)
    
    Returns:
        Liste des IDs des éditions générées
    """
    try:
        edition_service = MagazineEditionService(db)
        generated_ids = await edition_service.generate_daily_batch(count=count, delay_minutes=delay_minutes)
        
        logger.info(f"✅ Lot de {len(generated_ids)} éditions généré")
        return {
            "generated_count": len(generated_ids),
            "edition_ids": generated_ids
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération du lot: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur génération lot: {str(e)}")
