"""Service de gestion des collections d'albums."""
import logging
import json
import asyncio
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
    
    def _generate_collection_name(self, ai_query: str) -> str:
        """Générer un nom de collection via Euria IA.
        
        Utilise l'IA Euria pour créer un nom synthétique représentative de la requête.
        """
        try:
            from app.services.external.ai_service import AIService
            ai = AIService()
            name = ai.generate_collection_name_sync(ai_query)
            logger.info(f"🎨 Nom généré par Euria: {name}")
            return name
        except Exception as e:
            logger.warning(f"⚠️ Fallback génération nom: {e}")
            # Fallback simple si Euria indisponible
            words = ai_query.split()
            stop_words = {'fais', 'faites', 'faire', 'me', 'moi', 'de', 'du', 'et', 'ou', 'un', 'une', 'des', 'le', 'la', 'les', 'à', 'pour'}
            key_words = [w for w in words if w.lower() not in stop_words and len(w) > 2][:2]
            return ' '.join(w.capitalize() for w in key_words) if key_words else "Collection Découverte"
    
    def create_collection(
        self,
        name: Optional[str] = None,
        search_type: str = 'ai_query',
        search_criteria: Optional[Dict[str, Any]] = None,
        ai_query: Optional[str] = None,
        web_search: bool = True  # Recherche web prioritaire par défaut
    ) -> AlbumCollection:
        """Créer une nouvelle collection d'albums et la peupler automatiquement.
        
        Args:
            name: Nom de la collection (généré automatiquement si None)
            search_type: Type de recherche (par défaut 'ai_query')
            search_criteria: Critères de recherche
            ai_query: Requête IA en langage naturel
            web_search: Si True, recherche d'abord sur le web (défaut: True)
        """
        # Générer le nom automatiquement si non fourni
        if not name and ai_query:
            name = self._generate_collection_name(ai_query)
        
        if not name:
            name = "Nouvelle Collection"
        
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
            # 🌐 PRIORITÉ ABSOLUE: Recherche Euria IA sur le web
            if web_search:
                logger.info(f"🌐 Recherche Euria IA pour: {ai_query}")
                web_albums = self._search_albums_web(ai_query, limit=50)
                albums.extend(web_albums)
                
                if len(web_albums) > 0:
                    logger.info(f"🎉 {len(web_albums)} albums proposés par Euria - PAS DE COMPLÉMENT LOCAL")
                else:
                    logger.warning(f"⚠️ Euria n'a trouvé aucun album, complément avec librairie locale...")
                    local_albums = self.search_by_ai_query(ai_query, limit=50)
                    albums.extend(local_albums)
            else:
                # Fallback: Recherche en librairie locale seulement
                logger.info(f"📚 Recherche locale uniquement pour: {ai_query}")
                local_albums = self.search_by_ai_query(ai_query, limit=50)
                albums.extend(local_albums)
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
            
            # Afficher le détail des albums avant ajout
            logger.info(f"📋 ALBUMS À AJOUTER À LA COLLECTION ({len(albums)} total):")
            for album in albums:
                artists_names = ", ".join([a.name for a in album.artists]) if album.artists else "Unknown"
                logger.info(f"  • {album.title} - {artists_names} ({album.year}) [Genre: {album.genre}, Support: {album.support}]")
            
            collection = self.add_albums_to_collection(collection.id, album_ids)
            logger.info(f"✅ {len(album_ids)} albums ajoutés à la collection {name}")
        else:
            logger.warning("⚠️ Aucun album trouvé pour ajouter à la collection")
        
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
        
        Si aucun album ne matche, retourne des albums aléatoires avec ai_description.
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
        
        # FALLBACK: Si aucun album ne matche, retourner albums aléatoires avec ai_description
        if not albums:
            logger.warning(f"⚠️ Aucun album ne matche la requête '{query}'. Fallback: albums aléatoires avec AI descriptions")
            from sqlalchemy import func
            albums = self.db.query(Album).filter(
                Album.ai_description.isnot(None)
            ).order_by(func.random()).limit(limit).all()
            logger.info(f"📊 Fallback: {len(albums)} albums aléatoires retournés")
        
        return albums
    
    def _search_albums_web(self, query: str, limit: int = 20) -> List[Album]:
        """Rechercher des albums sur le web via Euria IA.
        
        Flux:
        1. 🧠 Demande à Euria des albums correspondant à la requête (JSON structuré)
        2. 📚 Crée les albums en base de données avec provenance "Discover IA"
        3. 🎨 Enrichit avec Spotify (URLs, images)
        4. ✍️ Génère des descriptions via Euria
        
        Returns:
            Liste des albums créés
        """
        logger.info(f"🌐 Recherche web via Euria pour: {query}")
        
        try:
            from app.services.external.ai_service import AIService
            import os
            
            ai = AIService()
            
            # Étape 1: Rechercher les albums via EurIA
            logger.info(f"🧠 Requête à EurIA...")
            albums_data = ai.search_albums_web_sync(query, limit=limit)
            
            logger.info(f"📊 RÉSULTAT BRUT DE EURIA: {albums_data}")
            logger.info(f"📊 Nombre d'albums retournés: {len(albums_data)}")
            
            # Dédupliquer les albums (Euria peut retourner des doublons)
            seen = set()
            deduplicated = []
            duplicates = []
            
            for album_info in albums_data:
                key = (album_info.get('artist', '').lower(), album_info.get('album', '').lower())
                if key not in seen:
                    seen.add(key)
                    deduplicated.append(album_info)
                else:
                    duplicates.append(f"{album_info.get('artist')} - {album_info.get('album')}")
            
            if duplicates:
                logger.warning(f"⚠️ {len(duplicates)} albums dupliqués détectés et supprimés: {duplicates}")
            
            albums_data = deduplicated
            logger.info(f"✅ Après déduplication: {len(albums_data)} albums uniques")
            
            if not albums_data:
                logger.warning("⚠️ Aucun album trouvé via Euria")
                return []
            
            logger.info(f"✅ {len(albums_data)} albums trouvés via Euria - Détail: {[(a.get('artist'), a.get('album')) for a in albums_data]}")
            
            # Préparer Spotify pour l'enrichissement
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            spotify_service = None
            
            if client_id and client_secret:
                from app.services.spotify_service import SpotifyService
                spotify_service = SpotifyService(client_id, client_secret)
                logger.info("🎵 Service Spotify prêt pour enrichissement")
            else:
                logger.warning("⚠️ Clés Spotify manquantes, enrichissement limité")
            
            # Étape 2-4: Créer et enrichir les albums
            albums_created = []
            
            for idx, album_info in enumerate(albums_data, 1):
                try:
                    artist_name = album_info.get('artist', 'Unknown')
                    album_title = album_info.get('album', '')
                    year = album_info.get('year')
                    
                    if not album_title:
                        logger.warning(f"⏭️  Album sans titre, skip: {album_info}")
                        continue
                    
                    # Rechercher ou créer l'artiste
                    artist = self.db.query(Artist).filter(
                        Artist.name.ilike(f"%{artist_name}%")
                    ).first()
                    
                    if not artist:
                        artist = Artist(name=artist_name)
                        self.db.add(artist)
                        self.db.flush()
                        logger.info(f"  👤 Artiste créé: {artist_name}")
                    
                    # Chercher si l'album existe déjà
                    existing_album = self.db.query(Album).filter(
                        Album.title.ilike(album_title)
                    ).filter(
                        Album.artists.any(Artist.name.ilike(artist_name))
                    ).first()
                    
                    if existing_album:
                        logger.info(f"  ℹ️ Album existant: {album_title}")
                        albums_created.append(existing_album)
                        continue
                    
                    # Étape 2: Créer l'album avec provenance "Discover IA"
                    logger.info(f"  [{idx}/{len(albums_data)}] 📀 Création: {album_title} - {artist_name}")
                    
                    album = Album(
                        title=album_title,
                        year=year,
                        genre="Discover IA",  # Provenance
                        support="Digital"  # Par défaut pour découverte web
                    )
                    album.artists.append(artist)
                    
                    # Étape 3: Enrichir avec Spotify (+fallback Last.fm)
                    if spotify_service:
                        try:
                            # Chercher les détails et l'image sur Spotify
                            spotify_details = spotify_service.search_album_details_sync(
                                artist_name, album_title
                            )
                            
                            if spotify_details:
                                album.spotify_url = spotify_details.get('spotify_url')
                                album.image_url = spotify_details.get('image_url')
                                if not year and spotify_details.get('year'):
                                    album.year = spotify_details['year']
                                logger.info(f"    ✨ Enrichi avec Spotify")
                            else:
                                logger.info(f"    ⚠️ Non trouvé sur Spotify, fallback Last.fm...")
                                # Fallback: Chercher via Last.fm
                                from app.services.spotify_service import get_lastfm_image
                                lastfm_image = get_lastfm_image(artist_name, album_title)
                                if lastfm_image:
                                    album.image_url = lastfm_image
                                    logger.info(f"    ✨ Image trouvée via Last.fm")
                                else:
                                    logger.info(f"    ⏭️ Pas d'image (Spotify + Last.fm), exclusion")
                                    continue  # Exclure si aucune image
                        except Exception as e:
                            logger.warning(f"    ⚠️ Enrichissement échoué, exclusion: {e}")
                            continue
                    else:
                        logger.warning(f"    ⚠️ Spotify désactivé, exclusion de l'album")
                        continue  # Exclure si Spotify n'est pas configuré
                    
                    # Vérification finale: l'album doit avoir une image
                    if not album.image_url:
                        logger.info(f"    ⏭️ Aucune image trouvée, exclusion finale")
                        continue
                    
                    # Étape 4: Générer description via Euria
                    try:
                        description = euria.generate_album_description_sync(artist_name, album_title, year)
                        album.ai_description = description
                        logger.info(f"    ✍️ Description générée")
                    except Exception as e:
                        logger.warning(f"    ⚠️ Description Euria échouée: {e}")
                        album.ai_description = f"Découverte Euria via: {query}"
                    
                    self.db.add(album)
                    self.db.flush()
                    albums_created.append(album)
                    logger.info(f"    ✅ Album conservé avec image")
                    logger.info(f"    ✅ Album créé avec enrichissements")
                    
                except Exception as e:
                    logger.error(f"  ❌ Erreur création album '{album_info.get('album', '?')}': {e}")
                    continue
            
            self.db.commit()
            
            logger.info(f"🎉 {len(albums_created)} albums créés et enrichis")
            
            # Afficher le détail des albums créés pour debugging
            for album in albums_created:
                artists_names = ", ".join([a.name for a in album.artists])
                logger.info(f"  ✅ ALBUM CRÉÉ: '{album.title}' de {artists_names} ({album.year}) - Genre: {album.genre}, Source pour recherche Euria")
            
            return albums_created
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche web: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_collection(self, collection_id: int) -> Optional[AlbumCollection]:
        """Récupérer une collection par son ID."""
        return self.db.query(AlbumCollection).filter(
            AlbumCollection.id == collection_id
        ).first()
    
    def get_collection_albums(self, collection_id: int) -> List[Album]:
        """Récupérer les albums d'une collection (seulement ceux avec image)."""
        collection_albums = self.db.query(CollectionAlbum).filter(
            CollectionAlbum.collection_id == collection_id
        ).order_by(CollectionAlbum.position).all()
        
        # Filtrer les albums sans image
        result = []
        for ca in collection_albums:
            if ca.album.image_url:  # Seulement les albums avec image
                result.append(ca.album)
        
        return result
    
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
