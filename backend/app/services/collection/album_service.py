"""Service pour la gestion des albums de la collection."""
import logging
import math
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload

from app.models import Album, Artist, Image, Metadata
from app.schemas import AlbumCreate, AlbumUpdate, AlbumResponse, AlbumDetail

logger = logging.getLogger(__name__)


class AlbumService:
    """Service pour les opérations CRUD sur les albums."""
    
    @staticmethod
    def list_albums(
        db: Session,
        page: int = 1,
        page_size: int = 30,
        search: Optional[str] = None,
        support: Optional[str] = None,
        year: Optional[int] = None,
        is_soundtrack: Optional[bool] = None,
        source: Optional[str] = None
    ) -> tuple[List[AlbumResponse], int, int]:
        """
        Lister les albums avec pagination et filtres.
        
        Args:
            db: Session de base de données
            page: Numéro de page
            page_size: Nombre d'éléments par page
            search: Recherche par titre ou artiste
            support: Filtre par support (Vinyle, CD, Digital)
            year: Filtre par année
            is_soundtrack: Filtre par soundtrack
            source: Filtre par source (discogs, lastfm, roon, spotify)
            
        Returns:
            Tuple (items, total, pages)
        """
        # Requête de base
        query = db.query(Album)
        
        # Filtre source par défaut si pas spécifié
        if source is None:
            query = query.filter(Album.source == 'discogs')
        elif source:
            query = query.filter(Album.source == source)
        
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
        pages = math.ceil(total / page_size) if total > 0 else 0
        
        # Pagination
        offset = (page - 1) * page_size
        albums = query.offset(offset).limit(page_size).all()
        
        # Formater la réponse
        items = AlbumService._format_album_list(albums)
        
        return items, total, pages
    
    @staticmethod
    def get_album(db: Session, album_id: int) -> AlbumDetail:
        """
        Récupérer un album avec tous les détails.
        
        Args:
            db: Session de base de données
            album_id: ID de l'album
            
        Returns:
            AlbumDetail complètement hydraté
            
        Raises:
            Exception: Si l'album n'existe pas
        """
        album = db.query(Album).options(
            joinedload(Album.images),
            joinedload(Album.artists)
        ).filter(Album.id == album_id).first()
        
        if not album:
            raise Exception(f"Album {album_id} non trouvé")
        
        # Récupérer les images d'artiste
        artist_images = {}
        for artist in album.artists:
            artist_image = db.query(Image).filter(
                Image.artist_id == artist.id,
                Image.image_type == 'artist'
            ).first()
            
            if artist_image and artist_image.url:
                artist_images[artist.name] = artist_image.url
                logger.info(f"✅ Image trouvée pour {artist.name}: {artist_image.url[:60]}...")
            else:
                logger.warning(f"⚠️ Pas d'image artiste trouvée pour '{artist.name}' (ID: {artist.id})")
        
        # Récupérer les métadonnées
        ai_info = album.ai_description  # Colonne principale
        resume = None
        labels = None
        film_title = None
        film_year = None
        film_director = None
        
        if album.album_metadata:
            if not ai_info:
                ai_info = album.album_metadata.ai_info
            resume = album.album_metadata.resume
            labels = album.album_metadata.labels.split(',') if album.album_metadata.labels else None
            film_title = album.album_metadata.film_title
            film_year = album.album_metadata.film_year
            film_director = album.album_metadata.film_director
        
        logger.info(f"📤 Retour pour album {album_id}: {album.title}")
        
        return AlbumDetail(
            id=album.id,
            title=album.title,
            year=album.year,
            support=album.support,
            discogs_id=album.discogs_id,
            spotify_url=album.spotify_url,
            discogs_url=album.discogs_url,
            artists=[a.name for a in album.artists],
            images=[img.url for img in album.images],
            ai_info=ai_info,
            resume=resume,
            labels=labels,
            film_title=film_title,
            film_year=film_year,
            film_director=film_director,
            artist_images=artist_images,
            created_at=album.created_at,
            updated_at=album.updated_at
        )
    
    @staticmethod
    def create_album(db: Session, album_data: AlbumCreate) -> AlbumResponse:
        """
        Créer un nouvel album.
        
        Args:
            db: Session de base de données
            album_data: Données de l'album
            
        Returns:
            AlbumResponse avec l'album créé
            
        Raises:
            Exception: Si les artistes n'existent pas
        """
        # Vérifier que les artistes existent
        artists = db.query(Artist).filter(Artist.id.in_(album_data.artist_ids)).all()
        
        if len(artists) != len(album_data.artist_ids):
            raise Exception("Un ou plusieurs artistes non trouvés")
        
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
        
        logger.info(f"✅ Album créé: {album.title} (ID: {album.id})")
        
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
    
    @staticmethod
    def update_album(db: Session, album_id: int, album_data: AlbumUpdate) -> AlbumResponse:
        """
        Mettre à jour un album.
        
        Args:
            db: Session de base de données
            album_id: ID de l'album
            album_data: Nouvelles données
            
        Returns:
            AlbumResponse avec l'album mis à jour
            
        Raises:
            Exception: Si l'album n'existe pas
        """
        album = db.query(Album).filter(Album.id == album_id).first()
        
        if not album:
            raise Exception(f"Album {album_id} non trouvé")
        
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
                raise Exception("Un ou plusieurs artistes non trouvés")
            album.artists = artists
        
        db.commit()
        db.refresh(album)
        
        logger.info(f"✅ Album mis à jour: {album.title} (ID: {album.id})")
        
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
    
    @staticmethod
    def patch_album(db: Session, album_id: int, patch_data: dict) -> dict:
        """
        Mettre à jour partiellement un album.
        
        Args:
            db: Session de base de données
            album_id: ID de l'album
            patch_data: Dictionnaire des champs à mettre à jour
            
        Returns:
            Dictionnaire avec les données mises à jour
            
        Raises:
            Exception: Si l'album n'existe pas
        """
        album = db.query(Album).filter(Album.id == album_id).first()
        
        if not album:
            raise Exception(f"Album {album_id} non trouvé")
        
        # Mettre à jour uniquement les champs fournis
        if 'spotify_url' in patch_data:
            album.spotify_url = patch_data['spotify_url']
        
        db.commit()
        db.refresh(album)
        
        logger.info(f"✅ Album patché: {album.title} (ID: {album.id})")
        
        return {
            "id": album.id,
            "spotify_url": album.spotify_url,
            "message": "Album mis à jour"
        }
    
    @staticmethod
    def delete_album(db: Session, album_id: int) -> None:
        """
        Supprimer un album.
        
        Args:
            db: Session de base de données
            album_id: ID de l'album
            
        Raises:
            Exception: Si l'album n'existe pas
        """
        album = db.query(Album).filter(Album.id == album_id).first()
        
        if not album:
            raise Exception(f"Album {album_id} non trouvé")
        
        album_title = album.title
        db.delete(album)
        db.commit()
        
        logger.info(f"✅ Album supprimé: {album_title} (ID: {album_id})")
    
    @staticmethod
    def _format_album_list(albums: List[Album]) -> List[AlbumResponse]:
        """Formater une liste d'albums."""
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
                logger.error(f"Erreur formatage album {album.id}: {e}")
                continue
        
        return items
