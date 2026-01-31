"""API endpoints pour la collection d'albums."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import math
import io
import json
from datetime import datetime

from app.database import get_db
from app.models import Album, Artist, Image, Metadata, album_artist
from app.services.markdown_export_service import MarkdownExportService
from app.services.ai_service import AIService
from app.core.config import get_settings
from app.schemas import (
    AlbumCreate,
    AlbumUpdate,
    AlbumResponse,
    AlbumDetail,
    AlbumListResponse,
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
    # Filtrer uniquement sur les albums de collection Discogs
    query = db.query(Album).filter(Album.source == 'discogs')
    
    # Recherche
    if search:
        query = query.join(Album.artists).filter(
            (Album.title.ilike(f"%{search}%")) | (Artist.name.ilike(f"%{search}%"))
        )
    
    # Filtres
    if support:
        query = query.filter(Album.support == support)
    
    if year:
        query = query.filter(Album.year == year)
    
    if is_soundtrack is not None:
        query = query.outerjoin(Album.album_metadata).filter(
            Metadata.film_title.isnot(None) if is_soundtrack else Metadata.film_title.is_(None)
        )
    
    # Total
    total = query.count()
    
    # Pagination
    offset = (page - 1) * page_size
    albums = query.offset(offset).limit(page_size).all()
    
    # Formater la réponse
    items = []
    for album in albums:
        try:
            # Récupérer les noms d'artistes
            artists = [a.name for a in album.artists] if album.artists else []
            
            # Récupérer les images
            images = [img.url for img in album.images] if album.images else []
            
            # Récupérer l'info IA
            ai_info = None
            if album.album_metadata:
                ai_info = album.album_metadata.ai_info
            
            items.append(AlbumResponse(
                id=album.id,
                title=album.title,
                year=album.year,
                support=album.support,
                discogs_id=album.discogs_id,
                spotify_url=album.spotify_url,
                discogs_url=album.discogs_url,
                artists=artists,
                images=images,
                ai_info=ai_info,
                created_at=album.created_at,
                updated_at=album.updated_at
            ))
        except Exception as e:
            # Log mais continue avec les autres albums
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur formatage album {album.id}: {e}")
            continue
    
    return AlbumListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/albums/{album_id}", response_model=AlbumDetail)
async def get_album(
    album_id: int,
    db: Session = Depends(get_db)
):
    """Détail d'un album."""
    album = db.query(Album).filter(Album.id == album_id).first()
    
    if not album:
        raise HTTPException(status_code=404, detail="Album non trouvé")
    
    # Formater la réponse
    artists = [a.name for a in album.artists]
    images = [img.url for img in album.images]
    
    ai_info = None
    resume = None
    labels = None
    film_title = None
    film_year = None
    film_director = None
    
    if album.album_metadata:
        ai_info = album.album_metadata.ai_info
        resume = album.album_metadata.resume
        labels = album.album_metadata.labels.split(',') if album.album_metadata.labels else None
        film_title = album.album_metadata.film_title
        film_year = album.album_metadata.film_year
        film_director = album.album_metadata.film_director
    
    return AlbumDetail(
        id=album.id,
        title=album.title,
        year=album.year,
        support=album.support,
        discogs_id=album.discogs_id,
        spotify_url=album.spotify_url,
        discogs_url=album.discogs_url,
        artists=artists,
        images=images,
        ai_info=ai_info,
        resume=resume,
        labels=labels,
        film_title=film_title,
        film_year=film_year,
        film_director=film_director,
        created_at=album.created_at,
        updated_at=album.updated_at
    )


@router.post("/albums", response_model=AlbumResponse, status_code=201)
async def create_album(
    album_data: AlbumCreate,
    db: Session = Depends(get_db)
):
    """Créer un nouvel album."""
    # Vérifier que les artistes existent
    artists = db.query(Artist).filter(Artist.id.in_(album_data.artist_ids)).all()
    
    if len(artists) != len(album_data.artist_ids):
        raise HTTPException(status_code=400, detail="Un ou plusieurs artistes non trouvés")
    
    # Créer l'album
    album = Album(
        title=album_data.title,
        year=album_data.year,
        support=album_data.support,
        discogs_id=album_data.discogs_id,
        spotify_url=album_data.spotify_url,
        discogs_url=album_data.discogs_url
    )
    album.artists = artists
    
    db.add(album)
    db.commit()
    db.refresh(album)
    
    return AlbumResponse(
        id=album.id,
        title=album.title,
        year=album.year,
        support=album.support,
        discogs_id=album.discogs_id,
        spotify_url=album.spotify_url,
        discogs_url=album.discogs_url,
        artists=[a.name for a in album.artists],
        images=[],
        ai_info=None,
        created_at=album.created_at,
        updated_at=album.updated_at
    )


@router.put("/albums/{album_id}", response_model=AlbumResponse)
async def update_album(
    album_id: int,
    album_data: AlbumUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un album."""
    album = db.query(Album).filter(Album.id == album_id).first()
    
    if not album:
        raise HTTPException(status_code=404, detail="Album non trouvé")
    
    # Mettre à jour les champs
    if album_data.title is not None:
        album.title = album_data.title
    if album_data.year is not None:
        album.year = album_data.year
    if album_data.support is not None:
        album.support = album_data.support
    if album_data.discogs_id is not None:
        album.discogs_id = album_data.discogs_id
    if album_data.spotify_url is not None:
        album.spotify_url = album_data.spotify_url
    if album_data.discogs_url is not None:
        album.discogs_url = album_data.discogs_url
    
    if album_data.artist_ids is not None:
        artists = db.query(Artist).filter(Artist.id.in_(album_data.artist_ids)).all()
        if len(artists) != len(album_data.artist_ids):
            raise HTTPException(status_code=400, detail="Un ou plusieurs artistes non trouvés")
        album.artists = artists
    
    db.commit()
    db.refresh(album)
    
    return AlbumResponse(
        id=album.id,
        title=album.title,
        year=album.year,
        support=album.support,
        discogs_id=album.discogs_id,
        spotify_url=album.spotify_url,
        discogs_url=album.discogs_url,
        artists=[a.name for a in album.artists],
        images=[img.url for img in album.images],
        ai_info=album.album_metadata.ai_info if album.album_metadata else None,
        created_at=album.created_at,
        updated_at=album.updated_at
    )


@router.patch("/albums/{album_id}")
async def patch_album(
    album_id: int,
    patch_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Mettre à jour partiellement un album (ex: URL Spotify)."""
    album = db.query(Album).filter(Album.id == album_id).first()
    
    if not album:
        raise HTTPException(status_code=404, detail="Album non trouvé")
    
    # Mettre à jour uniquement les champs fournis
    if 'spotify_url' in patch_data:
        album.spotify_url = patch_data['spotify_url']
    
    db.commit()
    db.refresh(album)
    
    return {
        "id": album.id,
        "spotify_url": album.spotify_url,
        "message": "Album mis à jour"
    }


@router.delete("/albums/{album_id}", status_code=204)
async def delete_album(
    album_id: int,
    db: Session = Depends(get_db)
):
    """Supprimer un album."""
    album = db.query(Album).filter(Album.id == album_id).first()
    
    if not album:
        raise HTTPException(status_code=404, detail="Album non trouvé")
    
    db.delete(album)
    db.commit()
    
    return None


@router.get("/artists", response_model=List[dict])
async def list_artists(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Liste des artistes."""
    artists = db.query(Artist).limit(limit).all()
    
    result = []
    for artist in artists:
        # Récupérer l'image
        image_url = None
        if artist.images:
            image_url = artist.images[0].url
        
        result.append({
            "id": artist.id,
            "name": artist.name,
            "spotify_id": artist.spotify_id,
            "image_url": image_url
        })
    
    return result


@router.get("/stats")
async def get_collection_stats(
    db: Session = Depends(get_db)
):
    """Statistiques de la collection Discogs."""
    # Stats sur les albums Discogs uniquement
    total_albums = db.query(Album).filter(Album.source == 'discogs').count()
    total_artists = db.query(Artist).distinct(Artist.id).join(Album.artists).filter(
        Album.source == 'discogs'
    ).count()
    
    # Par support (Discogs uniquement)
    supports = db.query(Album.support, db.func.count(Album.id)).filter(
        Album.source == 'discogs'
    ).group_by(Album.support).all()
    
    # Soundtracks
    soundtracks = db.query(Metadata).filter(
        Metadata.film_title.isnot(None)
    ).join(Album).filter(Album.source == 'discogs').count()
    
    return {
        "collection": "discogs",
        "total_albums": total_albums,
        "total_artists": total_artists,
        "by_support": {s[0] or "Unknown": s[1] for s in supports},
        "soundtracks": soundtracks
    }


@router.get("/listenings", response_model=AlbumListResponse)
async def list_listening_albums(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(30, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title or artist"),
    source: Optional[str] = Query(None, description="Filter by source (lastfm, roon, spotify, manual)"),
    db: Session = Depends(get_db)
):
    """Liste des albums provenant des écoutes (non-Discogs)."""
    # Exclure explicitement les albums Discogs
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
    offset = (page - 1) * page_size
    albums = query.offset(offset).limit(page_size).all()
    
    # Formater la réponse
    items = []
    for album in albums:
        try:
            artists = [a.name for a in album.artists] if album.artists else []
            images = [img.url for img in album.images] if album.images else []
            ai_info = None
            if album.album_metadata:
                ai_info = album.album_metadata.ai_info
            
            items.append(AlbumResponse(
                id=album.id,
                title=album.title,
                year=album.year,
                support=album.support,
                discogs_id=album.discogs_id,
                spotify_url=album.spotify_url,
                discogs_url=album.discogs_url,
                artists=artists,
                images=images,
                ai_info=ai_info,
                created_at=album.created_at,
                updated_at=album.updated_at
            ))
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur formatage album {album.id}: {e}")
            continue
    
    return AlbumListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/source-stats")
async def get_source_statistics(
    db: Session = Depends(get_db)
):
    """Statistiques par source d'albums."""
    stats = db.query(Album.source, db.func.count(Album.id)).group_by(Album.source).all()
    
    result = {}
    for source, count in stats:
        result[source or 'unknown'] = count
    
    # Stats supplémentaires pour les supports
    discogs_supports = db.query(Album.support, db.func.count(Album.id)).filter(
        Album.source == 'discogs'
    ).group_by(Album.support).all()
    
    listening_sources = {
        'lastfm': db.query(Album).filter(Album.source == 'lastfm').count(),
        'roon': db.query(Album).filter(Album.source == 'roon').count(),
        'spotify': db.query(Album).filter(Album.source == 'spotify').count(),
        'manual': db.query(Album).filter(Album.source == 'manual').count(),
    }
    
    return {
        "by_source": result,
        "discogs_supports": {s[0] or "unknown": s[1] for s in discogs_supports},
        "listening_sources": listening_sources,
        "total_albums": db.query(Album).count()
    }


@router.get("/export/markdown", response_class=StreamingResponse)
async def export_collection_markdown(
    db: Session = Depends(get_db)
):
    """
    Exporter la collection complète en markdown.
    Triée par artiste et album avec toutes les informations et résumés IA.
    """
    # Générer le markdown
    markdown_content = MarkdownExportService.get_collection_markdown(db)
    
    # Convertir en bytes
    markdown_bytes = markdown_content.encode('utf-8')
    
    return StreamingResponse(
        io.BytesIO(markdown_bytes),
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=collection-discogs.md"}
    )


@router.get("/export/markdown/{artist_id}", response_class=StreamingResponse)
async def export_artist_markdown(
    artist_id: int,
    db: Session = Depends(get_db)
):
    """Exporter la discographie d'un artiste en markdown."""
    # Vérifier que l'artiste existe
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artiste non trouvé")
    
    # Générer le markdown
    markdown_content = MarkdownExportService.get_artist_markdown(db, artist_id)
    
    if not markdown_content:
        raise HTTPException(status_code=404, detail="Aucun album trouvé pour cet artiste")
    
    # Convertir en bytes
    markdown_bytes = markdown_content.encode('utf-8')
    
    return StreamingResponse(
        io.BytesIO(markdown_bytes),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=collection-{artist.name.replace(' ', '-').lower()}.md"}
    )


@router.get("/export/markdown/support/{support}", response_class=StreamingResponse)
async def export_support_markdown(
    support: str = Path(..., description="Support (Vinyle, CD, Digital)"),
    db: Session = Depends(get_db)
):
    """Exporter tous les albums d'un support spécifique en markdown."""
    valid_supports = ['Vinyle', 'CD', 'Digital', 'Cassette']
    if support not in valid_supports:
        raise HTTPException(
            status_code=400, 
            detail=f"Support invalide. Supports valides: {', '.join(valid_supports)}"
        )
    
    # Générer le markdown
    markdown_content = MarkdownExportService.get_support_markdown(db, support)
    
    # Convertir en bytes
    markdown_bytes = markdown_content.encode('utf-8')
    
    return StreamingResponse(
        io.BytesIO(markdown_bytes),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=collection-{support.lower()}.md"}
    )


@router.get("/export/json", response_class=StreamingResponse)
async def export_collection_json(
    db: Session = Depends(get_db)
):
    """Exporter la collection complète en JSON."""
    # Récupérer tous les albums de collection
    albums = db.query(Album).filter(Album.source == 'discogs').order_by(Album.title).all()
    
    # Construire les données JSON
    data = {
        "export_date": datetime.now().isoformat(),
        "total_albums": len(albums),
        "albums": []
    }
    
    for album in albums:
        # Traiter les images
        images = []
        if album.images:
            for img in album.images:
                images.append({
                    "url": img.url,
                    "type": img.image_type,
                    "source": img.source
                })
        
        # Traiter les métadonnées (c'est un objet unique, pas une liste)
        metadata = {}
        if album.album_metadata:
            meta = album.album_metadata
            metadata = {
                "ai_info": meta.ai_info,
                "resume": meta.resume,
                "labels": meta.labels,
                "film_title": meta.film_title,
                "film_year": meta.film_year,
                "film_director": meta.film_director
            }
        
        album_data = {
            "id": album.id,
            "title": album.title,
            "artists": [artist.name for artist in album.artists],
            "year": album.year,
            "support": album.support,
            "discogs_id": album.discogs_id,
            "spotify_url": album.spotify_url,
            "discogs_url": album.discogs_url,
            "images": images,
            "created_at": album.created_at.isoformat() if album.created_at else None,
            "metadata": metadata
        }
        
        data["albums"].append(album_data)
    
    # Convertir en JSON
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=collection-discogs.json"}
    )


@router.get("/export/json/support/{support}", response_class=StreamingResponse)
async def export_support_json(
    support: str = Path(..., description="Support (Vinyle, CD, Digital)"),
    db: Session = Depends(get_db)
):
    """Exporter tous les albums d'un support spécifique en JSON."""
    valid_supports = ['Vinyle', 'CD', 'Digital', 'Cassette']
    if support not in valid_supports:
        raise HTTPException(
            status_code=400, 
            detail=f"Support invalide. Supports valides: {', '.join(valid_supports)}"
        )
    
    # Récupérer les albums du support
    albums = db.query(Album).filter(
        Album.source == 'discogs',
        Album.support == support
    ).order_by(Album.title).all()
    
    # Construire les données JSON
    data = {
        "export_date": datetime.now().isoformat(),
        "support": support,
        "total_albums": len(albums),
        "albums": []
    }
    
    for album in albums:
        # Traiter les images
        images = []
        if album.images:
            for img in album.images:
                images.append({
                    "url": img.url,
                    "type": img.image_type,
                    "source": img.source
                })
        
        # Traiter les métadonnées (c'est un objet unique, pas une liste)
        metadata = {}
        if album.album_metadata:
            meta = album.album_metadata
            metadata = {
                "ai_info": meta.ai_info,
                "resume": meta.resume,
                "labels": meta.labels,
                "film_title": meta.film_title,
                "film_year": meta.film_year,
                "film_director": meta.film_director
            }
        
        album_data = {
            "id": album.id,
            "title": album.title,
            "artists": [artist.name for artist in album.artists],
            "year": album.year,
            "support": album.support,
            "discogs_id": album.discogs_id,
            "spotify_url": album.spotify_url,
            "discogs_url": album.discogs_url,
            "images": images,
            "created_at": album.created_at.isoformat() if album.created_at else None,
            "metadata": metadata
        }
        
        data["albums"].append(album_data)
    
    # Convertir en JSON
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=collection-{support.lower()}.json"}
    )


@router.post("/markdown/presentation")
async def generate_presentation_markdown(
    request: AlbumMarkdownRequest,
    db: Session = Depends(get_db)
):
    """
    Générer une présentation markdown pour les albums sélectionnés.
    Format: Haïku + Albums avec description multi-ligne générée par l'IA.
    """
    if not request.album_ids:
        raise HTTPException(status_code=400, detail="Aucun album sélectionné")
    
    # Récupérer les albums
    albums = db.query(Album).filter(
        Album.id.in_(request.album_ids),
        Album.source == 'discogs'
    ).all()
    
    if not albums:
        raise HTTPException(status_code=404, detail="Aucun album trouvé")
    
    # Charger la config pour l'IA
    settings = get_settings()
    euria_config = settings.app_config.get('euria', {})
    
    # Initialiser le service IA
    ai = AIService(
        url=euria_config.get('url'),
        bearer=euria_config.get('bearer'),
        max_attempts=euria_config.get('max_attempts', 3),
        default_error_message=euria_config.get('default_error_message', 'Aucune information disponible')
    )
    
    import logging
    logger = logging.getLogger(__name__)
    
    # Générer le markdown
    markdown = "# Album Haïku\n"
    
    # Date du jour
    now = datetime.now()
    date_str = now.strftime("#### The %d of %B, %Y").replace(" 0", " ")  # Enlever le 0 du jour si présent
    markdown += f"{date_str}\n"
    markdown += f"\t\t{len(albums)} albums from Discogs collection\n"
    
    # Ajouter un haïku si demandé
    haiku_text = ""
    if request.include_haiku:
        try:
            haiku_prompt = "Génère un haïku court sur la musique et les albums. Réponds uniquement avec le haïku en 3 lignes, sans numérotation."
            haiku_text = await ai.ask_for_ia(haiku_prompt, max_tokens=100)
            # Ajouter chaque ligne du haïku avec indentation
            for line in haiku_text.strip().split('\n'):
                markdown += f"\t\t{line}\n"
        except Exception as e:
            logger.warning(f"⚠️ Erreur génération haïku: {e}")
            # Haïku par défaut
            markdown += "\t\tMusique qui danse,\n"
            markdown += "\t\talbunis en harmonie,\n"
            markdown += "\t\tcœur qui s'envole.\n"
    
    markdown += "---\n"
    
    # Générer une section pour chaque album
    for album in albums:
        # Artiste en titre
        if album.artists:
            artist_name = album.artists[0].name
            markdown += f"# {artist_name}\n"
        
        # Titre, année et infos
        title_line = f"#### {album.title}"
        if album.year:
            title_line += f" ({album.year})"
        markdown += f"{title_line}\n"
        
        # Liens Spotify et Discogs
        markdown += "\t###### 🎧"
        if album.spotify_url:
            markdown += f" [Listen with Spotify]({album.spotify_url})"
        markdown += "  👥"
        if album.discogs_url:
            markdown += f" [Read on Discogs]({album.discogs_url})"
        markdown += "\n\t###### 💿 "
        markdown += f"{album.support if album.support else 'Digital'}\n"
        
        # Description générée par l'IA (multi-ligne, basée sur le prompt spécifique)
        description = ""
        try:
            album_lower = album.title.lower()
            artist_lower = (album.artists[0].name.lower() if album.artists else "artiste inconnu")
            description_prompt = f"""Présente moi l'album {album_lower} de {artist_lower}. 
N'ajoute pas de questions ou de commentaires. 
Limite ta réponse à 35 mots maximum.
Réponds uniquement en français."""
            description = await ai.ask_for_ia(description_prompt, max_tokens=100)
            
            # Vérifier si le service retourne le message d'erreur par défaut
            if description == euria_config.get('default_error_message', 'Aucune information disponible'):
                # Utiliser la description par défaut si l'IA n'est pas disponible
                description = f"Album {album.title} sorti en {album.year if album.year else '?'}. Œuvre musicale enrichissante, à découvrir absolument."
        except Exception as e:
            logger.warning(f"⚠️ Erreur génération description pour {album.title}: {e}")
            # Description par défaut
            description = f"Album {album.title} sorti en {album.year if album.year else '?'}. Œuvre musicale enrichissante, à découvrir absolument."
        
        # Ajouter la description avec indentation
        description = description.strip()
        for line in description.split('\n'):
            markdown += f"\t\t{line}\n"
        
        # Image HTML
        if album.images and album.images[0].url:
            image_url = album.images[0].url
            markdown += f"\n\n<img src='{image_url}' />\n"
        
        markdown += "---\n"
    
    # Footer
    markdown += "\t\tPython generated with love, for iA Presenter using Euria AI from Infomaniak\n"
    
    return {
        "markdown": markdown,
        "count": len(albums),
        "generated_at": datetime.now().isoformat()
    }
