"""Tests unitaires pour AlbumService."""

import pytest
from typing import List
from sqlalchemy.orm import Session
from app.models import Album, Artist, Image, Metadata
from app.services.collection.album_service import AlbumService
from app.schemas import AlbumCreate, AlbumUpdate, AlbumResponse


class TestAlbumServiceList:
    """Tests pour AlbumService.list_albums()"""
    
    def test_list_albums_empty(self, album_service: AlbumService, db_session: Session):
        """Tester list_albums avec base de données vide."""
        items, total, pages = album_service.list_albums(db_session)
        
        assert items == []
        assert total == 0
        assert pages == 0
    
    def test_list_albums_pagination(
        self, 
        album_service: AlbumService, 
        db_session: Session,
        album_in_db: Album
    ):
        """Tester la pagination de list_albums."""
        items, total, pages = album_service.list_albums(
            db_session, 
            page=1, 
            page_size=10
        )
        
        assert len(items) >= 1
        assert total >= 1
        assert pages >= 1
    
    def test_list_albums_search(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester la recherche dans list_albums."""
        items, total, pages = album_service.list_albums(
            db_session,
            search="Test"
        )
        
        assert total >= 1
        assert any(album.title == "Test Album" for album in items)
    
    def test_list_albums_filter_by_year(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester le filtre par année."""
        items, total, pages = album_service.list_albums(
            db_session,
            year=2023
        )
        
        assert total >= 1
        assert all(album.year == 2023 for album in items)
    
    def test_list_albums_filter_by_support(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester le filtre par support."""
        items, total, pages = album_service.list_albums(
            db_session,
            support="Vinyl"
        )
        
        if items:
            assert all(album.support == "Vinyl" for album in items)
    
    def test_list_albums_filter_by_source(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester le filtre par source."""
        items, total, pages = album_service.list_albums(
            db_session,
            source="discogs"
        )
        
        assert len(items) >= 1


class TestAlbumServiceGetDetail:
    """Tests pour AlbumService.get_album()"""
    
    def test_get_album_success(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester la récupération d'un album existant."""
        album = album_service.get_album(db_session, album_in_db.id)
        
        assert album is not None
        assert album.id == album_in_db.id
        assert album.title == "Test Album"
    
    def test_get_album_not_found(
        self,
        album_service: AlbumService,
        db_session: Session
    ):
        """Tester la récupération d'un album inexistant."""
        album = album_service.get_album(db_session, 99999)
        
        assert album is None
    
    def test_get_album_with_metadata(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester che l'album inclut ses métadonnées."""
        # Ajouter des métadonnées
        metadata = Metadata(
            album_id=album_in_db.id,
            ai_info="Test metadata"
        )
        db_session.add(metadata)
        db_session.commit()
        
        album = album_service.get_album(db_session, album_in_db.id)
        
        assert album is not None
        assert album.ai_info is not None


class TestAlbumServiceCreate:
    """Tests pour AlbumService.create_album()"""
    
    def test_create_album_with_artist(
        self,
        album_service: AlbumService,
        db_session: Session,
        artist_in_db: Artist
    ):
        """Tester la création d'un album avec artiste."""
        album_data = AlbumCreate(
            title="New Album",
            year=2024,
            support="CD",
            discogs_id="54321",
            artist_ids=[artist_in_db.id]
        )
        
        album = album_service.create_album(db_session, album_data)
        
        assert album is not None
        assert album.title == "New Album"
        assert album.year == 2024
        assert len(album.artists) == 1
    
    def test_create_album_with_multiple_artists(
        self,
        album_service: AlbumService,
        db_session: Session,
        artist_in_db: Artist
    ):
        """Tester la création d'un album avec plusieurs artistes."""
        # Créer un deuxième artiste
        artist2 = Artist(name="Second Artist", spotify_id="spotify456")
        db_session.add(artist2)
        db_session.commit()
        
        album_data = AlbumCreate(
            title="Collaboration Album",
            year=2024,
            artist_ids=[artist_in_db.id, artist2.id]
        )
        
        album = album_service.create_album(db_session, album_data)
        
        assert album is not None
        assert len(album.artists) == 2
    
    def test_create_album_without_metadata_fails(
        self,
        album_service: AlbumService,
        db_session: Session,
        artist_in_db: Artist
    ):
        """Tester que la création échoue avec artiste invalide."""
        album_data = AlbumCreate(
            title="Invalid Album",
            year=2024,
            artist_ids=[99999]  # ID artiste inexistant
        )
        
        with pytest.raises(ValueError):
            album_service.create_album(db_session, album_data)


class TestAlbumServiceUpdate:
    """Tests pour AlbumService.update_album()"""
    
    def test_update_album_success(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester la mise à jour d'un album."""
        update_data = AlbumUpdate(
            title="Updated Title",
            year=2024,
            genre="Jazz"
        )
        
        album = album_service.update_album(db_session, album_in_db.id, update_data)
        
        assert album is not None
        assert album.title == "Updated Title"
        assert album.year == 2024
        assert album.genre == "Jazz"
    
    def test_update_album_partial(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester la mise à jour partielle d'un album."""
        original_support = album_in_db.support
        
        update_data = AlbumUpdate(
            title="New Title"
        )
        
        album = album_service.update_album(db_session, album_in_db.id, update_data)
        
        assert album.title == "New Title"
        assert album.support == original_support  # Pas modifié


class TestAlbumServiceDelete:
    """Tests pour AlbumService.delete_album()"""
    
    def test_delete_album_success(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester la suppression d'un album."""
        album_id = album_in_db.id
        
        result = album_service.delete_album(db_session, album_id)
        
        assert result is True
        
        # Vérifier que l'album est supprimé
        album = album_service.get_album(db_session, album_id)
        assert album is None
    
    def test_delete_album_not_found(
        self,
        album_service: AlbumService,
        db_session: Session
    ):
        """Tester la suppression d'un album inexistant."""
        result = album_service.delete_album(db_session, 99999)
        
        assert result is False


class TestAlbumServiceBulkOperations:
    """Tests pour les opérations en masse sur les albums."""
    
    def test_bulk_update_albums(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester la mise à jour en masse."""
        album_ids = [album_in_db.id]
        update_data = {"genre": "Rock"}
        
        updated_count = album_service.bulk_update(db_session, album_ids, update_data)
        
        assert updated_count >= 1
    
    def test_bulk_delete_albums(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester la suppression en masse."""
        album_ids = [album_in_db.id]
        
        deleted_count = album_service.bulk_delete(db_session, album_ids)
        
        assert deleted_count >= 1
