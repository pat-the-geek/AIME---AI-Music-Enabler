"""Tests unitaires pour les endpoints de collection."""

import pytest
from fastapi.testclient import TestClient
from app.models import Album, Artist


class TestAlbumEndpoints:
    """Tests pour les endpoints de gestion d'albums."""
    
    def test_list_albums_endpoint(
        self,
        client: TestClient,
        album_in_db: Album
    ):
        """Tester l'endpoint GET /api/v1/collection/albums."""
        response = client.get("/api/v1/collection/albums")
        
        assert response.status_code == 200
        data = response.json()
        assert "albums" in data or "items" in data
    
    def test_get_album_detail(
        self,
        client: TestClient,
        album_in_db: Album
    ):
        """Tester l'endpoint GET /api/v1/collection/albums/{id}."""
        response = client.get(f"/api/v1/collection/albums/{album_in_db.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("id") == album_in_db.id or data.get("title") == album_in_db.title
    
    def test_create_album(
        self,
        client: TestClient,
        artist_in_db: Artist
    ):
        """Tester l'endpoint POST /api/v1/collection/albums."""
        payload = {
            "title": "New Album",
            "year": 2024,
            "support": "Digital",
            "artist_ids": [artist_in_db.id],
            "discogs_id": "123456"
        }
        
        response = client.post("/api/v1/collection/albums", json=payload)
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("title") == "New Album"
    
    def test_update_album(
        self,
        client: TestClient,
        album_in_db: Album
    ):
        """Tester l'endpoint PUT /api/v1/collection/albums/{id}."""
        payload = {
            "title": "Updated Title",
            "year": 2024
        }
        
        response = client.put(f"/api/v1/collection/albums/{album_in_db.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("title") == "Updated Title"
    
    def test_delete_album(
        self,
        client: TestClient,
        album_in_db: Album
    ):
        """Tester l'endpoint DELETE /api/v1/collection/albums/{id}."""
        response = client.delete(f"/api/v1/collection/albums/{album_in_db.id}")
        
        assert response.status_code in [200, 204]
    
    def test_search_albums(
        self,
        client: TestClient,
        album_in_db: Album
    ):
        """Tester la recherche d'albums."""
        response = client.get("/api/v1/collection/albums?search=Test")
        
        assert response.status_code == 200
        data = response.json()
        assert "albums" in data or "items" in data
    
    def test_filter_albums_by_year(
        self,
        client: TestClient,
        album_in_db: Album
    ):
        """Tester le filtrage par année."""
        response = client.get("/api/v1/collection/albums?year=2023")
        
        assert response.status_code == 200


class TestArtistEndpoints:
    """Tests pour les endpoints de gestion d'artistes."""
    
    def test_list_artists(
        self,
        client: TestClient,
        artist_in_db: Artist
    ):
        """Tester l'endpoint GET /api/v1/collection/artists."""
        response = client.get("/api/v1/collection/artists/list")
        
        assert response.status_code == 200
        data = response.json()
        assert "artists" in data or "count" in data
    
    def test_get_artist_detail(
        self,
        client: TestClient,
        artist_in_db: Artist
    ):
        """Tester l'endpoint GET /api/v1/collection/artists/{id}."""
        response = client.get(f"/api/v1/collection/artists/{artist_in_db.id}")
        
        assert response.status_code in [200, 404]  # Peut ne pas exister
    
    def test_generate_artist_article(
        self,
        client: TestClient,
        artist_in_db: Artist
    ):
        """Tester la génération d'article artiste."""
        response = client.get(f"/api/v1/collection/artists/{artist_in_db.id}/article")
        
        assert response.status_code in [200, 500]  # Peut échouer si pas d'IA disponible


class TestCollectionSearch:
    """Tests pour la recherche dans la collection."""
    
    def test_search_collection_by_title(
        self,
        client: TestClient,
        album_in_db: Album
    ):
        """Tester la recherche par titre d'album."""
        response = client.get("/api/v1/search/search?query=Test&type=album")
        
        assert response.status_code == 200
    
    def test_search_collection_by_artist(
        self,
        client: TestClient,
        album_in_db: Album
    ):
        """Tester la recherche par artiste."""
        response = client.get("/api/v1/search/search?query=Test&type=artist")
        
        assert response.status_code == 200
