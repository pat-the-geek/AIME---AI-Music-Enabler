"""API endpoints pour la collection d'albums."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import io
import math
from datetime import datetime

from app.database import get_db
from app.schemas import (
    AlbumCreate,
    AlbumUpdate,
    AlbumResponse,
    AlbumDetail,
    AlbumListResponse,
)
from app.services.collection import (
    AlbumService,
    ArtistService,
    CollectionStatsService,
    ExportService,
)

router = APIRouter()


class AlbumMarkdownRequest(BaseModel):
    """Request body pour la génération de markdown avec albums sélectionnés."""
    album_ids: List[int]
    include_haiku: bool = True


@router.get("/albums", response_model=AlbumListResponse)
async def list_albums(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(30, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title or artist"),
    support: Optional[str] = Query(None, description="Filter by support (Vinyle, CD, Digital)"),
    year: Optional[int] = Query(None, description="Filter by year"),
    is_soundtrack: Optional[bool] = Query(None, description="Filter soundtracks"),
    db: Session = Depends(get_db)
):
    """Liste des albums Discogs avec pagination et filtres."""
    try:
        items, total, pages = AlbumService.list_albums(
            db,
            page=page,
            page_size=page_size,
            search=search,
            support=support,
            year=year,
            is_soundtrack=is_soundtrack,
            source='discogs'
        )
        
        return AlbumListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/albums/{album_id}", response_model=AlbumDetail)
async def get_album(
    album_id: int,
    db: Session = Depends(get_db)
):
    """Détail d'un album."""
    try:
        album = AlbumService.get_album(db, album_id)
        return album
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/albums", response_model=AlbumResponse, status_code=201)
async def create_album(
    album_data: AlbumCreate,
    db: Session = Depends(get_db)
):
    """Créer un nouvel album."""
    try:
        album = AlbumService.create_album(db, album_data)
        return album
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/albums/{album_id}", response_model=AlbumResponse)
async def update_album(
    album_id: int,
    album_data: AlbumUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un album."""
    try:
        album = AlbumService.update_album(db, album_id, album_data)
        return album
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/albums/{album_id}")
async def patch_album(
    album_id: int,
    patch_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Mettre à jour partiellement un album (ex: URL Spotify)."""
    try:
        result = AlbumService.patch_album(db, album_id, patch_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/albums/{album_id}", status_code=204)
async def delete_album(
    album_id: int,
    db: Session = Depends(get_db)
):
    """Supprimer un album."""
    try:
        AlbumService.delete_album(db, album_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/artists", response_model=List[dict])
async def list_artists(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Liste des artistes."""
    try:
        result = ArtistService.list_artists(db, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_collection_stats(
    db: Session = Depends(get_db)
):
    """Statistiques de la collection Discogs."""
    try:
        stats = CollectionStatsService.get_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/listenings", response_model=AlbumListResponse)
async def list_listening_albums(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(30, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title or artist"),
    source: Optional[str] = Query(None, description="Filter by source (lastfm, spotify, manual)"),
    db: Session = Depends(get_db)
):
    """Liste des albums provenant des écoutes (non-Discogs)."""
    try:
        # Pour listenings, on exclut les albums discogs
        from app.models import Album, Artist
        from sqlalchemy.orm import Session as SQLSession
        
        query = db.query(Album).filter(Album.source != 'discogs')
        
        # Recherche
        if search:
            query = query.join(Album.artists).filter(
                (Album.title.ilike(f"%{search}%")) | (Artist.name.ilike(f"%{search}%"))
            )
        
        # Filtre source
        if source:
            query = query.filter(Album.source == source)
        
        # Total
        total = query.count()
        
        # Pagination
        import math
        offset = (page - 1) * page_size
        albums = query.offset(offset).limit(page_size).all()
        
        items = AlbumService._format_album_list(albums)
        pages = math.ceil(total / page_size) if total > 0 else 0
        
        return AlbumListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/source-stats")
async def get_source_statistics(
    db: Session = Depends(get_db)
):
    """Statistiques par source d'albums."""
    try:
        stats = CollectionStatsService.get_source_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/markdown", response_class=StreamingResponse)
async def export_collection_markdown(
    db: Session = Depends(get_db)
):
    """
    Exporter la collection complète en markdown.
    Triée par artiste et album avec toutes les informations et résumés IA.
    """
    try:
        markdown_content = ExportService.export_markdown_full(db)
        markdown_bytes = markdown_content.encode('utf-8')
        
        return StreamingResponse(
            io.BytesIO(markdown_bytes),
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=collection-discogs.md"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/markdown/{artist_id}", response_class=StreamingResponse)
async def export_artist_markdown(
    artist_id: int,
    db: Session = Depends(get_db)
):
    """Exporter la discographie d'un artiste en markdown."""
    try:
        markdown_content = ExportService.export_markdown_artist(db, artist_id)
        markdown_bytes = markdown_content.encode('utf-8')
        
        # Récupérer le nom de l'artiste pour le nom de fichier
        from app.models import Artist
        artist = db.query(Artist).filter(Artist.id == artist_id).first()
        filename = f"collection-{artist.name.replace(' ', '-').lower()}.md" if artist else f"collection-artist-{artist_id}.md"
        
        return StreamingResponse(
            io.BytesIO(markdown_bytes),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/export/markdown/support/{support}", response_class=StreamingResponse)
async def export_support_markdown(
    support: str = Path(..., description="Support (Vinyle, CD, Digital)"),
    db: Session = Depends(get_db)
):
    """Exporter tous les albums d'un support spécifique en markdown."""
    try:
        markdown_content = ExportService.export_markdown_support(db, support)
        markdown_bytes = markdown_content.encode('utf-8')
        
        return StreamingResponse(
            io.BytesIO(markdown_bytes),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=collection-{support.lower()}.md"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export/json", response_class=StreamingResponse)
async def export_collection_json(
    db: Session = Depends(get_db)
):
    """Exporter la collection complète en JSON."""
    try:
        json_content = ExportService.export_json_full(db)
        json_bytes = json_content.encode('utf-8')
        
        return StreamingResponse(
            io.BytesIO(json_bytes),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=collection-discogs.json"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/json/support/{support}", response_class=StreamingResponse)
async def export_support_json(
    support: str = Path(..., description="Support (Vinyle, CD, Digital)"),
    db: Session = Depends(get_db)
):
    """Exporter tous les albums d'un support spécifique en JSON."""
    try:
        json_content = ExportService.export_json_support(db, support)
        json_bytes = json_content.encode('utf-8')
        
        return StreamingResponse(
            io.BytesIO(json_bytes),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=collection-{support.lower()}.json"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/markdown/presentation")
async def generate_presentation_markdown(
    request: AlbumMarkdownRequest,
    db: Session = Depends(get_db)
):
    """
    Générer une présentation markdown pour les albums sélectionnés.
    Format: Haïku + Albums avec description multi-ligne générée par l'IA.
    """
    try:
        markdown = await ExportService.generate_presentation_markdown(
            db,
            request.album_ids,
            request.include_haiku
        )
        
        return {
            "markdown": markdown,
            "count": len(request.album_ids),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
