"""Service de gestion des collections d'albums."""
import logging
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.models import Album, Artist, AlbumCollection, CollectionAlbum
from app.database import get_db

logger = logging.getLogger(__name__)


class AlbumCollectionService:
    """Service pour gérer les collections d'albums."""
    
    def __init__(self, db: Session):
        """Initialiser le service."""
        self.db = db
    
    def create_collection(
        self,
        name: str,
        search_type: Optional[str] = None,
        search_criteria: Optional[Dict[str, Any]] = None,
        ai_query: Optional[str] = None
    ) -> AlbumCollection:
        """Créer une nouvelle collection d'albums et la peupler automatiquement."""
        # Convertir search_criteria en JSON string si c'est un dict
        criteria_json = None
        if search_criteria:
            criteria_json = json.dumps(search_criteria) if isinstance(search_criteria, dict) else search_criteria
        
        collection = AlbumCollection(
            name=name,
            search_type=search_type,
            search_criteria=criteria_json,
            ai_query=ai_query,
            album_count=0
        )
        self.db.add(collection)
        self.db.commit()
        self.db.refresh(collection)
        logger.info(f"📚 Collection créée: {name}")
        
        # Rechercher et ajouter automatiquement les albums
        albums = []
        
        if search_type == 'ai_query' and ai_query:
            albums = self.search_by_ai_query(ai_query, limit=50)
        elif search_type == 'genre' and search_criteria and 'genre' in search_criteria:
            albums = self.search_by_genre(search_criteria['genre'], limit=50)
        elif search_type == 'artist' and search_criteria and 'artist' in search_criteria:
            albums = self.search_by_artist(search_criteria['artist'], limit=50)
        elif search_type == 'period' and search_criteria:
            start_year = search_criteria.get('start_year')
            end_year = search_criteria.get('end_year')
            albums = self.search_by_period(start_year, end_year, limit=50)
        
        # Ajouter les albums trouvés à la collection
        if albums:
            album_ids = [album.id for album in albums]
            collection = self.add_albums_to_collection(collection.id, album_ids)
            logger.info(f"✅ {len(album_ids)} albums ajoutés à la collection {name}")
        
        # Rafraîchir pour obtenir le album_count à jour
        self.db.refresh(collection)
        return collection
    
    def add_albums_to_collection(
        self,
        collection_id: int,
        album_ids: List[int]
    ) -> AlbumCollection:
        """Ajouter des albums à une collection."""
        collection = self.db.query(AlbumCollection).filter(
            AlbumCollection.id == collection_id
        ).first()
        
        if not collection:
            raise ValueError(f"Collection {collection_id} non trouvée")
        
        # Récupérer la position max actuelle
        max_position = self.db.query(func.max(CollectionAlbum.position)).filter(
            CollectionAlbum.collection_id == collection_id
        ).scalar() or 0
        
        # Ajouter les albums
        added_count = 0
        for idx, album_id in enumerate(album_ids):
            # Vérifier si l'album n'est pas déjà dans la collection
            exists = self.db.query(CollectionAlbum).filter(
                and_(
                    CollectionAlbum.collection_id == collection_id,
                    CollectionAlbum.album_id == album_id
                )
            ).first()
            
            if not exists:
                collection_album = CollectionAlbum(
                    collection_id=collection_id,
                    album_id=album_id,
                    position=max_position + idx + 1
                )
                self.db.add(collection_album)
                added_count += 1
        
        # Commit d'abord les albums
        self.db.commit()
        
        # Mettre à jour le compteur avec un count simple
        total_count = self.db.query(CollectionAlbum).filter(
            CollectionAlbum.collection_id == collection_id
        ).count()
        
        collection.album_count = total_count
        
        self.db.commit()
        self.db.refresh(collection)
        logger.info(f"📚 {added_count} albums ajoutés à la collection {collection.name} (total: {total_count})")
        return collection
    
    def search_by_genre(self, genre: str, limit: int = 50) -> List[Album]:
        """Rechercher des albums par genre."""
        logger.info(f"🔍 Recherche par genre: {genre}")
        
        # Recherche dans ai_description ou autres métadonnées
        albums = self.db.query(Album).filter(
            or_(
                Album.ai_description.ilike(f"%{genre}%"),
                Album.genre.ilike(f"%{genre}%")
            )
        ).limit(limit).all()
        
        logger.info(f"✅ {len(albums)} albums trouvés pour le genre {genre}")
        return albums
    
    def search_by_artist(self, artist_name: str, limit: int = 50) -> List[Album]:
        """Rechercher des albums par artiste."""
        logger.info(f"🔍 Recherche par artiste: {artist_name}")
        
        # Recherche d'artiste avec variantes
        artist_variants = [
            artist_name,
            artist_name.replace("The ", ""),
            f"The {artist_name}" if not artist_name.startswith("The ") else artist_name
        ]
        
        albums = self.db.query(Album).join(Album.artists).filter(
            or_(*[Artist.name.ilike(f"%{variant}%") for variant in artist_variants])
        ).limit(limit).all()
        
        logger.info(f"✅ {len(albums)} albums trouvés pour l'artiste {artist_name}")
        return albums
    
    def search_by_period(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        limit: int = 50
    ) -> List[Album]:
        """Rechercher des albums par période."""
        logger.info(f"🔍 Recherche par période: {start_year} - {end_year}")
        
        query = self.db.query(Album)
        
        if start_year:
            query = query.filter(Album.year >= start_year)
        if end_year:
            query = query.filter(Album.year <= end_year)
        
        albums = query.limit(limit).all()
        
        logger.info(f"✅ {len(albums)} albums trouvés pour la période {start_year}-{end_year}")
        return albums
    
    def search_by_ai_query(self, query: str, limit: int = 50) -> List[Album]:
        """Rechercher des albums par requête AI (recherche enrichie multi-champs).
        
        Utilise une recherche multi-critères dans:
        - ai_description: description longue générée par AI
        - ai_style: style/ambiance court
        - genre: genre musical
        - title: titre de l'album
        - artist name: nom de l'artiste
        """
        logger.info(f"🔍 Recherche AI enrichie: {query}")
        
        # Découper la requête en termes de recherche
        search_terms = query.lower().split()
        
        # Créer des conditions de recherche pour chaque terme dans différents champs
        conditions = []
        for term in search_terms:
            term_conditions = []
            
            # Recherche dans ai_description
            term_conditions.append(Album.ai_description.ilike(f"%{term}%"))
            
            # Recherche dans ai_style
            term_conditions.append(Album.ai_style.ilike(f"%{term}%"))
            
            # Recherche dans genre
            term_conditions.append(Album.genre.ilike(f"%{term}%"))
            
            # Recherche dans titre
            term_conditions.append(Album.title.ilike(f"%{term}%"))
            
            # Recherche dans artistes (via join)
            term_conditions.append(Artist.name.ilike(f"%{term}%"))
            
            # Au moins un champ doit matcher ce terme
            conditions.append(or_(*term_conditions))
        
        # Requête avec join pour accéder aux artistes
        albums = self.db.query(Album).outerjoin(Album.artists).filter(
            # Tous les termes doivent matcher (dans n'importe quel champ)
            and_(*conditions)
        ).distinct().limit(limit).all()
        
        logger.info(f"✅ {len(albums)} albums trouvés pour la requête AI: {query}")
        logger.info(f"   Termes recherchés: {', '.join(search_terms)}")
        
        return albums
    
    def get_collection(self, collection_id: int) -> Optional[AlbumCollection]:
        """Récupérer une collection par son ID."""
        return self.db.query(AlbumCollection).filter(
            AlbumCollection.id == collection_id
        ).first()
    
    def get_collection_albums(self, collection_id: int) -> List[Album]:
        """Récupérer les albums d'une collection."""
        collection_albums = self.db.query(CollectionAlbum).filter(
            CollectionAlbum.collection_id == collection_id
        ).order_by(CollectionAlbum.position).all()
        
        return [ca.album for ca in collection_albums]
    
    def list_collections(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[AlbumCollection]:
        """Lister toutes les collections."""
        return self.db.query(AlbumCollection).limit(limit).offset(offset).all()
    
    def delete_collection(self, collection_id: int) -> bool:
        """Supprimer une collection."""
        collection = self.get_collection(collection_id)
        if not collection:
            return False
        
        # Supprimer les associations
        self.db.query(CollectionAlbum).filter(
            CollectionAlbum.collection_id == collection_id
        ).delete()
        
        # Supprimer la collection
        self.db.delete(collection)
        self.db.commit()
        
        logger.info(f"🗑️ Collection {collection.name} supprimée")
        return True
