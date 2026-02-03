"""Routes API pour la génération de magazines musicaux."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.services.magazine_generator_service import MagazineGeneratorService
from app.services.ai_service import AIService
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
        
        logger.info(f"📖 Initialisation Magazine - Euria config: {bool(euria_config)}")
        
        ai_service = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer')
        )
        
        # Générer le magazine
        magazine_service = MagazineGeneratorService(db, ai_service)
        magazine = await magazine_service.generate_magazine()
        
        logger.info(f"✅ Magazine généré: {magazine['id']}")
        return magazine
        
    except Exception as e:
        logger.error(f"❌ Erreur génération magazine: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur génération magazine: {str(e)}")


@router.post("/regenerate")
async def regenerate_magazine(db: Session = Depends(get_db)):
    """Regénérer un nouveau magazine (alias pour generate)."""
    return await generate_magazine(db)
