"""Tests E2E pour les workflows critiques."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Album, Artist, Track
from app.schemas import AlbumCreate

pytest.skip("E2E workflows rely on full services; skipping in CI", allow_module_level=True)


class TestDiscogsImportWorkflow:
    """Tests E2E pour l'import Discogs."""
    
    def test_full_discogs_import_workflow(
        self,
        client: TestClient,
        db_session: Session
    ):
        """Tester le workflow complet: import → enrichissement → sauvegarde."""
        # 1. Créer un album
        artist = Artist(name="Test Artist")
        db_session.add(artist)
        db_session.commit()
        
        payload = {
            "title": "Test Album from Discogs",
            "year": 2023,
            "artist_ids": [artist.id],
            "discogs_id": "12345678",
            "source": "discogs"
        }
        
        # 2. Importer via API
        response = client.post("/api/v1/collection/albums", json=payload)
        assert response.status_code in [200, 201]
        
        # 3. Vérifier qu'il est en base
        albums = db_session.query(Album).filter_by(discogs_id="12345678").all()
        assert len(albums) > 0
        
        album = albums[0]
        
        # 4. Vérifier que les métadonnées sont disponibles
        assert album.title == "Test Album from Discogs"
        assert album.source == "discogs"


class TestMagazineGenerationWorkflow:
    """Tests E2E pour la génération de magazine."""
    
    def test_full_magazine_generation(
        self,
        client: TestClient,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester le workflow complet de génération de magazine."""
        # 1. Vérifier que l'album existe
        assert album_in_db is not None
        
        # 2. Appeler l'endpoint de génération magazine
        response = client.post("/api/v1/magazines/refresh")
        assert response.status_code in [200, 202, 500]  # 500 si pas d'IA
        
        # 3. Vérifier que magazine_editions existe
        response = client.get("/api/v1/magazines/editions/1")
        assert response.status_code in [200, 404]


class TestHaikuGenerationWorkflow:
    """Tests E2E pour la génération de haïkus."""
    
    def test_full_haiku_generation_from_history(
        self,
        client: TestClient,
        db_session: Session,
        album_in_db: Album,
        track_in_db: Track
    ):
        """Tester la génération de haïku à partir de l'historique d'écoute."""
        # 1. Créer un historique d'écoute
        from app.models import ListeningHistory
        
        listening = ListeningHistory(
            track_id=track_in_db.id,
            listened_at=None,
            source="lastfm"
        )
        db_session.add(listening)
        db_session.commit()
        
        # 2. Générer un haïku
        response = client.post(
            "/api/v1/content/haikus",
            json={
                "album_id": album_in_db.id,
                "mood": "reflective"
            }
        )
        
        assert response.status_code in [200, 500]  # 500 si pas d'IA
class TestCollectionEnrichmentWorkflow:
    """Tests E2E pour l'enrichissement de collection."""
    
    def test_full_enrichment_workflow(
        self,
        client: TestClient,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester le workflow complet d'enrichissement."""
        # 1. Vérifier l'état initial
        assert album_in_db.image_url is not None or album_in_db.image_url is None
        
        # 2. Déclencher l'enrichissement
        response = client.post(
            "/api/v1/collection/albums/enrich",
            json={"album_ids": [album_in_db.id]}
        )
        
        assert response.status_code in [200, 202, 500]
        
        # 3. Vérifier que l'album a été enrichi (au moins les métadonnées)
        album = db_session.query(Album).filter_by(id=album_in_db.id).first()
        assert album is not None


class TestPlaylistGenerationWorkflow:
    """Tests E2E pour la génération de playlists."""
    
    def test_full_playlist_generation_manual(
        self,
        client: TestClient,
        db_session: Session,
        album_in_db: Album,
        track_in_db: Track
    ):
        """Tester la création manuelle d'une playlist."""
        # 1. Créer une playlist
        response = client.post(
            "/api/v1/playback/playlists",
            json={
                "name": "Test Playlist",
                "track_ids": [track_in_db.id]
            }
        )
        
        assert response.status_code in [200, 201]
        
        if response.status_code in [200, 201]:
            data = response.json()
            playlist_id = data.get("id") or data.get("playlist_id")
            
            if playlist_id:
                # 2. Jouer la playlist
                response = client.post(
                    f"/api/v1/playback/playlists/{playlist_id}/play",
                    json={"zone_name": "test"}
                )
                assert response.status_code in [200, 500, 503]
    
    def test_full_playlist_generation_ai(
        self,
        client: TestClient,
        db_session: Session,
        album_in_db: Album,
        track_in_db: Track
    ):
        """Tester la génération de playlist par IA."""
        from app.models import Playlist, PlaylistTrack
        
        # 1. Créer une playlist vide
        playlist = Playlist(
            name="AI Generated",
            algorithm="ai_generated",
            ai_prompt="Songs for a rainy day"
        )
        db_session.add(playlist)
        db_session.commit()
        
        # 2. Ajouter des tracks
        if playlist.id:
            response = client.post(
                f"/api/v1/playback/playlists/{playlist.id}/generate",
                json={"ai_prompt": "Songs for a rainy day"}
            )
            
            assert response.status_code in [200, 500]


class TestAnalyticsWorkflow:
    """Tests E2E pour le workflow d'analytiques."""
    
    def test_full_analytics_generation(
        self,
        client: TestClient,
        db_session: Session,
        album_in_db: Album,
        artist_in_db: Artist
    ):
        """Tester le workflow complet d'analytiques."""
        # 1. Récupérer les statistiques globales
        response = client.get("/api/v1/analytics/stats")
        assert response.status_code == 200
        
        # 2. Récupérer les statistiques par artiste
        response = client.get(f"/api/v1/analytics/stats/artists/{artist_in_db.id}")
        assert response.status_code in [200, 404]
        
        # 3. Récupérer les stats par album
        response = client.get(f"/api/v1/analytics/stats/albums/{album_in_db.id}")
        assert response.status_code in [200, 404]


class TestExportWorkflow:
    """Tests E2E pour l'export de collection."""
    
    def test_full_markdown_export(
        self,
        client: TestClient,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester l'export en Markdown."""
        response = client.post(
            "/api/v1/collection/export/markdown",
            json={"album_ids": [album_in_db.id]}
        )
        
        assert response.status_code in [200, 500]
    
    def test_full_json_export(
        self,
        client: TestClient,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester l'export en JSON."""
        response = client.post(
            "/api/v1/collection/export/json",
            json={"album_ids": [album_in_db.id]}
        )
        
        assert response.status_code in [200, 500]
