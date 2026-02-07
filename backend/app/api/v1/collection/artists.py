"""Routes API pour les artistes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db
from app.services.artist_article_service import ArtistArticleService
from app.services.external.ai_service import AIService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/list")
async def list_artists(
    search: str = Query(None, description="Recherche par nom"),
    limit: int = Query(50, description="Nombre maximum d'artistes"),
    db: Session = Depends(get_db)
):
    """Liste tous les artistes disponibles."""
    try:
        from app.models import Artist, Image
        from sqlalchemy.orm import joinedload
        
        query = db.query(Artist).options(joinedload(Artist.images))
        
        if search:
            query = query.filter(Artist.name.ilike(f"%{search}%"))
        
        artists = query.order_by(Artist.name).limit(limit).all()
        
        return {
            "count": len(artists),
            "artists": [
                {
                    "id": artist.id,
                    "name": artist.name,
                    "spotify_id": artist.spotify_id,
                    "image_url": artist.images[0].url if artist.images else None
                }
                for artist in artists
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur liste artistes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur liste artistes: {str(e)}")


@router.get("/{artist_id}/article")
async def generate_artist_article(
    artist_id: int,
    db: Session = Depends(get_db)
):
    """Génère un article long (3000 mots) sur un artiste avec IA."""
    try:
        # Initialiser les services
        settings = get_settings()
        secrets = settings.secrets
        euria_config = secrets.get('euria', {})
        
        ai_service = AIService(
            url=euria_config.get('url'),
            bearer=euria_config.get('bearer')
        )
        
        article_service = ArtistArticleService(db, ai_service)
        
        # Générer l'article
        logger.info(f"📝 Génération article pour artiste {artist_id}")
        article = await article_service.generate_article(artist_id)
        
        logger.info(f"✅ Article généré: {len(article['content'])} caractères")
        return article
        
    except Exception as e:
        logger.error(f"❌ Erreur génération article artiste: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur génération article: {str(e)}")


@router.get("/{artist_id}/article/stream")
async def stream_artist_article(
    artist_id: int,
    db: Session = Depends(get_db)
):
    """Génère un article long (3000 mots) sur un artiste avec streaming SSE."""
    from fastapi.responses import StreamingResponse
    
    async def generate_stream():
        try:
            # Initialiser les services
            settings = get_settings()
            secrets = settings.secrets
            euria_config = secrets.get('euria', {})
            
            ai_service = AIService(
                url=euria_config.get('url'),
                bearer=euria_config.get('bearer')
            )
            
            article_service = ArtistArticleService(db, ai_service)
            
            # Envoyer les métadonnées d'abord
            logger.info(f"📝 Streaming article pour artiste {artist_id}")
            
            # Récupérer les métadonnées de l'artiste
            from app.models import Artist, Album
            from sqlalchemy.orm import joinedload
            
            artist = db.query(Artist).options(
                joinedload(Artist.albums),
                joinedload(Artist.images)
            ).filter(Artist.id == artist_id).first()
            
            if not artist:
                yield f"data: {{\"error\": \"Artiste non trouvé\"}}\n\n"
                return
            
            albums = db.query(Album).join(Album.artists).filter(
                Artist.id == artist_id
            ).order_by(Album.year.desc().nullslast()).limit(20).all()
            
            # Envoyer les métadonnées
            import json
            metadata = {
                "type": "metadata",
                "artist_name": artist.name,
                "artist_image_url": artist.images[0].url if artist.images else None,
                "albums_count": len(albums)
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Streamer le contenu de l'article
            async for chunk in article_service.generate_article_stream(artist_id):
                yield chunk
            
            # Envoyer un signal de fin
            yield f"data: {{\"type\": \"done\"}}\n\n"
            
            logger.info(f"✅ Streaming article terminé pour artiste {artist_id}")
            
        except Exception as e:
            logger.error(f"❌ Erreur streaming article: {str(e)}", exc_info=True)
            import json
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Désactiver le buffering nginx
        }
    )

