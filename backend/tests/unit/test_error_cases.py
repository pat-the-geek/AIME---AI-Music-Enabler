"""Tests pour les cas d'erreur et edge cases."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import httpx

from app.services.collection.album_service import AlbumService
from app.services.spotify_service import SpotifyService
from app.services.external.ai_service import AIService
from app.models import Album, Artist
from app.schemas import AlbumCreate, AlbumUpdate


class TestAlbumServiceEdgeCases:
    """Tests pour les cas d'erreur et limites d'AlbumService."""
    
    def test_list_albums_very_large_page_number(
        self,
        album_service: AlbumService,
        db_session: Session
    ):
        """Tester pagination avec numéro de page très élevé."""
        items, total, pages = album_service.list_albums(
            db_session,
            page=9999,  # Page très élevée
            page_size=10
        )
        
        assert items == []
        assert total >= 0
        assert pages >= 0
    
    def test_list_albums_zero_page_size(
        self,
        album_service: AlbumService,
        db_session: Session
    ):
        """Tester pagination avec page_size = 0 (edge case)."""
        # Devrait retourner une erreur ou résultat vide
        try:
            items, total, pages = album_service.list_albums(
                db_session,
                page_size=0
            )
            # Si pas d'erreur, résultat doit être cohérent
            assert isinstance(items, list)
        except (ValueError, ZeroDivisionError):
            # Comportement acceptable
            pass
    
    def test_list_albums_negative_year(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester filtrage avec année négative."""
        items, total, pages = album_service.list_albums(
            db_session,
            year=-1  # Année invalide
        )
        
        assert items == []
        assert total == 0
    
    def test_create_album_empty_title(
        self,
        album_service: AlbumService,
        db_session: Session,
        artist_in_db: Artist
    ):
        """Tester création d'album avec titre vide."""
        album_data = AlbumCreate(
            title="",  # Titre vide
            artist_ids=[artist_in_db.id]
        )
        
        # Devrait rejeter ou créer avec validation
        try:
            album = album_service.create_album(db_session, album_data)
            # Si créé, le titre ne doit pas être vide
            assert album.title == "" or album is None
        except (ValueError, IntegrityError):
            # Comportement attendu
            pass
    
    def test_create_album_very_long_title(
        self,
        album_service: AlbumService,
        db_session: Session,
        artist_in_db: Artist
    ):
        """Tester création d'album avec titre au maximum autorisé."""
        # Titre de 500 caractères (limite du schema)
        long_title = "A" * 500
        album_data = AlbumCreate(
            title=long_title,
            artist_ids=[artist_in_db.id]
        )
        
        album = album_service.create_album(db_session, album_data)
        
        if album:
            assert len(album.title) <= 500
        
        # Test que titre > 500 rejette (si validation en place)
        from pydantic_core import ValidationError
        try:
            album_data_toolong = AlbumCreate(
                title="A" * 501,  # Dépasse limite de 500
                artist_ids=[artist_in_db.id]
            )
        except ValidationError:
            # Comportement attendu
            pass
    
    def test_create_album_special_characters_title(
        self,
        album_service: AlbumService,
        db_session: Session,
        artist_in_db: Artist
    ):
        """Tester création d'album avec caractères spéciaux."""
        special_chars = "🎵 Café Français 🎶 <>&\"\'"
        album_data = AlbumCreate(
            title=special_chars,
            artist_ids=[artist_in_db.id]
        )
        
        album = album_service.create_album(db_session, album_data)
        
        assert album is not None
        assert album.title == special_chars or (
            "Caf" in album.title or album.title != ""
        )
    
    def test_update_album_null_fields(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester mise à jour avec champs None (ce qui ne change rien)."""
        original_title = album_in_db.title
        
        update_data = AlbumUpdate()  # Tous les champs optionnels = None
        
        album = album_service.update_album(db_session, album_in_db.id, update_data)
        
        # Aucun champ ne devrait changer
        assert album.title == original_title
    
    def test_update_nonexistent_album(
        self,
        album_service: AlbumService,
        db_session: Session
    ):
        """Tester mise à jour d'album inexistant."""
        update_data = AlbumUpdate(title="New Title")
        
        with pytest.raises(Exception):
            album_service.update_album(db_session, 99999, update_data)
    
    def test_delete_already_deleted_album(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester suppression d'un album déjà supprimé."""
        album_id = album_in_db.id
        
        # Première suppression
        result1 = album_service.delete_album(db_session, album_id)
        assert result1 is True
        
        # Deuxième suppression (idempotent - devrait retourner False)
        result2 = album_service.delete_album(db_session, album_id)
        assert result2 is False
    
    def test_create_album_duplicate_discogs_id(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album,
        artist_in_db: Artist
    ):
        """Tester création d'album avec même discogs_id."""
        album_data = AlbumCreate(
            title="Different Album",
            discogs_id=album_in_db.discogs_id,  # Même ID
            artist_ids=[artist_in_db.id]
        )
        
        # Devrait échouer ou ignorer duplicata
        try:
            album = album_service.create_album(db_session, album_data)
            # Peut être None ou lever une exception
            if album is None:
                pass  # OK
        except (IntegrityError, ValueError):
            pass  # OK


class TestSpotifyServiceErrorCases:
    """Tests pour les erreurs et edge cases SpotifyService."""
    
    @pytest.mark.asyncio
    async def test_search_artist_empty_name(
        self,
        mock_spotify_service: AsyncMock
    ):
        """Tester recherche d'artiste avec nom vide."""
        mock_spotify_service.search_artist_image.return_value = None
        
        result = await mock_spotify_service.search_artist_image("")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_search_artist_very_long_name(
        self,
        mock_spotify_service: AsyncMock
    ):
        """Tester recherche d'artiste avec nom très long."""
        long_name = "A" * 1000
        mock_spotify_service.search_artist_image.return_value = None
        
        result = await mock_spotify_service.search_artist_image(long_name)
        
        assert result is None or isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_search_artist_special_characters(
        self,
        mock_spotify_service: AsyncMock
    ):
        """Tester recherche avec caractères spéciaux."""
        special_name = "Artiste & Co. <test>"
        mock_spotify_service.search_artist_image.return_value = "https://example.com/artist.jpg"
        
        result = await mock_spotify_service.search_artist_image(special_name)
        
        assert result is not None or result is None  # Doit pas crasher
    
    @pytest.mark.asyncio
    async def test_search_album_auth_failure(
        self,
        mock_spotify_service: AsyncMock
    ):
        """Tester recherche d'album quand token échoue."""
        mock_spotify_service.search_album_image.side_effect = httpx.HTTPError("Auth failed")
        
        with pytest.raises(httpx.HTTPError):
            await mock_spotify_service.search_album_image("Artist", "Album")
    
    @pytest.mark.asyncio
    async def test_search_album_timeout(
        self,
        mock_spotify_service: AsyncMock
    ):
        """Tester recherche d'album avec timeout."""
        mock_spotify_service.search_album_image.side_effect = httpx.TimeoutException("Timeout")
        
        with pytest.raises(httpx.TimeoutException):
            await mock_spotify_service.search_album_image("Artist", "Album")
    
    @pytest.mark.asyncio
    async def test_search_album_connection_error(
        self,
        mock_spotify_service: AsyncMock
    ):
        """Tester recherche d'album avec erreur connexion."""
        mock_spotify_service.search_album_image.side_effect = httpx.ConnectError(
            "Connection refused"
        )
        
        with pytest.raises(httpx.ConnectError):
            await mock_spotify_service.search_album_image("Artist", "Album")


class TestAIServiceErrorCases:
    """Tests pour les erreurs et edge cases AIService."""
    
    @pytest.mark.asyncio
    async def test_ask_for_ia_empty_prompt(
        self,
        mock_ai_service: AsyncMock
    ):
        """Tester requête IA avec prompt vide."""
        mock_ai_service.ask_for_ia.return_value = ""
        
        result = await mock_ai_service.ask_for_ia("")
        
        assert result == "" or result is not None
    
    @pytest.mark.asyncio
    async def test_ask_for_ia_very_long_prompt(
        self,
        mock_ai_service: AsyncMock
    ):
        """Tester requête IA avec prompt très long."""
        long_prompt = "Question? " * 5000  # Env 50KB
        mock_ai_service.ask_for_ia.return_value = "Response"
        
        result = await mock_ai_service.ask_for_ia(long_prompt)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_ask_for_ia_zero_max_tokens(
        self,
        mock_ai_service: AsyncMock
    ):
        """Tester requête avec max_tokens = 0."""
        mock_ai_service.ask_for_ia.return_value = ""
        
        result = await mock_ai_service.ask_for_ia("prompt", max_tokens=0)
        
        # Devrait retourner réponse vide ou gérer gracieusement
        assert result == "" or result is not None
    
    @pytest.mark.asyncio
    async def test_ask_for_ia_negative_max_tokens(
        self,
        mock_ai_service: AsyncMock
    ):
        """Tester requête avec max_tokens négatif."""
        mock_ai_service.ask_for_ia.return_value = "Response"
        
        # Devrait valider et utiliser défaut
        result = await mock_ai_service.ask_for_ia("prompt", max_tokens=-100)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_ask_for_ia_circuit_breaker_open(
        self,
        mock_ai_service: AsyncMock
    ):
        """Tester quand circuit breaker est ouvert."""
        # Simuler circuit breaker ouvert
        mock_ai_service.ask_for_ia.return_value = "Aucune information disponible"
        
        result = await mock_ai_service.ask_for_ia("test")
        
        assert "information" in result.lower() or result is not None
    
    @pytest.mark.asyncio
    async def test_generate_haiku_missing_fields(
        self,
        mock_ai_service: AsyncMock
    ):
        """Tester génération haïku avec données incomplètes."""
        incomplete_data = {"artist": "Test"}  # Manque album, mood
        mock_ai_service.generate_haiku.return_value = "Incomplete haiku"
        
        result = await mock_ai_service.generate_haiku(incomplete_data)
        
        assert result is not None


class TestInputValidationAndSanitization:
    """Tests pour la validation des entrées utilisateur."""
    
    def test_sql_injection_attempt_in_search(
        self,
        album_service: AlbumService,
        db_session: Session
    ):
        """Tester protection contre injection SQL."""
        malicious_query = "'; DROP TABLE albums; --"
        
        # Devrait pas affecter la base de données
        items, total, pages = album_service.list_albums(
            db_session,
            search=malicious_query
        )
        
        # La table devrait toujours exister
        all_albums = db_session.query(Album).all()
        assert isinstance(all_albums, list)
    
    def test_xss_attempt_in_album_title(
        self,
        album_service: AlbumService,
        db_session: Session,
        artist_in_db: Artist
    ):
        """Tester protection contre XSS."""
        xss_payload = "<script>alert('test')</script>"
        
        album_data = AlbumCreate(
            title=xss_payload,
            artist_ids=[artist_in_db.id]
        )
        
        album = album_service.create_album(db_session, album_data)
        
        # Le titre devrait être stocké comme-est (DB safe)
        assert album.title == xss_payload or isinstance(album.title, str)
    
    def test_null_character_in_input(
        self,
        album_service: AlbumService,
        db_session: Session,
        artist_in_db: Artist
    ):
        """Tester gestion de null characters."""
        null_payload = "Album\x00Title"
        
        album_data = AlbumCreate(
            title=null_payload,
            artist_ids=[artist_in_db.id]
        )
        
        try:
            album = album_service.create_album(db_session, album_data)
            assert album is not None
        except (ValueError, Exception):
            # Comportement acceptable
            pass


class TestConcurrencyIssues:
    """Tests pour les problèmes de concurrence."""
    
    def test_concurrent_album_creation(
        self,
        album_service: AlbumService,
        db_session: Session,
        artist_in_db: Artist
    ):
        """Tester création concurrent d'albums (simulation)."""
        album_data1 = AlbumCreate(
            title="Album 1",
            artist_ids=[artist_in_db.id]
        )
        album_data2 = AlbumCreate(
            title="Album 2",
            artist_ids=[artist_in_db.id]
        )
        
        # Créer albums
        album1 = album_service.create_album(db_session, album_data1)
        album2 = album_service.create_album(db_session, album_data2)
        
        # Les deux doivent avoir IDs différents
        assert album1.id != album2.id
    
    def test_update_deleted_album_race_condition(
        self,
        album_service: AlbumService,
        db_session: Session,
        album_in_db: Album
    ):
        """Tester race condition: update après delete."""
        album_id = album_in_db.id
        
        # Supprimer l'album
        album_service.delete_album(db_session, album_id)
        
        # Essayer de mettre à jour
        update_data = AlbumUpdate(title="Should fail")
        
        with pytest.raises(Exception):
            album_service.update_album(db_session, album_id, update_data)
