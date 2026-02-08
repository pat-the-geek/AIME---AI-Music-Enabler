"""Configuration pytest et fixtures pour la suite de tests.

Cet fichier configure:
- Session de base de données (SQLite en mémoire)
- Client de test FastAPI
- Fixtures pour chaque service
- Mocks pour les APIs externes
"""

import pytest
import os
import json
import asyncio
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Import de l'application et des dépendances
from app.main import app
from app.database import Base, get_db
from app.models import Album, Artist, Track, ListeningHistory, Playlist, Image, Metadata, ServiceState
from app.schemas import AlbumCreate, ArtistCreate, TrackCreate
from app.services.collection.album_service import AlbumService
from app.services.collection.artist_service import ArtistService
from app.services.spotify_service import SpotifyService
from app.services.external.ai_service import AIService
from app.services.discogs_service import DiscogsService
from app.core.config import get_settings


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def db_engine():
    """Créer un moteur SQLite en mémoire pour les tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Créer une session de base de données pour chaque test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    # Override la dépendance get_db
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Client de test FastAPI avec base de données en mémoire."""
    return TestClient(app)


# ============================================================================
# SERVICE FIXTURES
# ============================================================================

@pytest.fixture
def album_service(db_session: Session) -> AlbumService:
    """Instance d'AlbumService pour les tests."""
    return AlbumService()


@pytest.fixture
def artist_service(db_session: Session) -> ArtistService:
    """Instance d'ArtistService pour les tests."""
    return ArtistService()


# ============================================================================
# MOCK FIXTURES - APIs EXTERNES
# ============================================================================

@pytest.fixture
def mock_spotify_service() -> AsyncMock:
    """Mock pour SpotifyService."""
    mock = AsyncMock(spec=SpotifyService)
    mock.search_artist_image.return_value = "https://example.com/artist.jpg"
    mock.search_album_image.return_value = "https://example.com/album.jpg"
    mock.search_album_url.return_value = "https://open.spotify.com/album/123"
    return mock


@pytest.fixture
def mock_ai_service() -> AsyncMock:
    """Mock pour AIService (EurIA)."""
    mock = AsyncMock(spec=AIService)
    mock.ask_for_ia.return_value = "Test generated description"
    mock.generate_haiku.return_value = "Old music plays / Time fades away / Memories sing"
    mock.generate_album_description.return_value = "A beautiful album with great musicianship"
    return mock


@pytest.fixture
def mock_discogs_service() -> AsyncMock:
    """Mock pour DiscogsService."""
    mock = AsyncMock(spec=DiscogsService)
    mock.search_album.return_value = {
        "id": "12345",
        "title": "Test Album",
        "artists": [{"name": "Test Artist"}],
        "year": 2023,
        "genres": ["Rock"],
        "formats": [{"name": "Vinyl"}]
    }
    return mock


# ============================================================================
# DATA FIXTURES - Données de test
# ============================================================================

@pytest.fixture
def sample_artist_data() -> Dict[str, Any]:
    """Données d'artiste pour les tests."""
    return {
        "name": "Test Artist",
        "spotify_id": "spotify123",
    }


@pytest.fixture
def sample_album_data(sample_artist_data: Dict[str, Any]) -> Dict[str, Any]:
    """Données d'album pour les tests."""
    return {
        "title": "Test Album",
        "year": 2023,
        "support": "Vinyl",
        "discogs_id": "12345",
        "source": "discogs",
        "genre": "Rock",
        "image_url": "https://example.com/album.jpg",
    }


@pytest.fixture
def sample_track_data() -> Dict[str, Any]:
    """Données de track pour les tests."""
    return {
        "title": "Test Track",
        "track_number": 1,
        "duration_seconds": 180,
        "spotify_id": "spotify_track_123",
    }


# ============================================================================
# DATABASE POPULATION FIXTURES
# ============================================================================

@pytest.fixture
def artist_in_db(db_session: Session, sample_artist_data: Dict[str, Any]) -> Artist:
    """Créer un artiste dans la base de test."""
    artist = Artist(**sample_artist_data)
    db_session.add(artist)
    db_session.commit()
    db_session.refresh(artist)
    return artist


@pytest.fixture
def album_in_db(db_session: Session, artist_in_db: Artist, sample_album_data: Dict[str, Any]) -> Album:
    """Créer un album dans la base de test."""
    album = Album(**sample_album_data)
    album.artists.append(artist_in_db)
    db_session.add(album)
    db_session.commit()
    db_session.refresh(album)
    return album


@pytest.fixture
def track_in_db(db_session: Session, album_in_db: Album, sample_track_data: Dict[str, Any]) -> Track:
    """Créer une track dans la base de test."""
    track = Track(**sample_track_data, album_id=album_in_db.id)
    db_session.add(track)
    db_session.commit()
    db_session.refresh(track)
    return track


# ============================================================================
# ASYNC FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Event loop pour les tests async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# PATCH FIXTURES
# ============================================================================

@pytest.fixture
def patch_env_vars():
    """Patcher les variables d'environnement pour les tests."""
    env_vars = {
        'EURIA_API_URL': 'https://test.euria.api',
        'EURIA_BEARER_TOKEN': 'test_token',
        'SPOTIFY_CLIENT_ID': 'test_spotify_id',
        'SPOTIFY_CLIENT_SECRET': 'test_spotify_secret',
        'DATABASE_URL': 'sqlite:///./test.db',
    }
    
    with patch.dict(os.environ, env_vars):
        yield


# ============================================================================
# CONTEXT MANAGER FIXTURES
# ============================================================================

@pytest.fixture
def cleanup_files():
    """Nettoyer les fichiers de test crééss."""
    files_to_cleanup = []
    yield files_to_cleanup
    
    for file_path in files_to_cleanup:
        if Path(file_path).exists():
            Path(file_path).unlink()
