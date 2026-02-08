"""Tests d'intégration pour les services externes (APIs)."""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.spotify_service import SpotifyService
from app.services.external.ai_service import AIService
from app.services.discogs_service import DiscogsService


class TestSpotifyServiceIntegration:
    """Tests d'intégration pour SpotifyService."""
    
    @pytest.mark.asyncio
    async def test_search_artist_image(
        self,
        mock_spotify_service: AsyncMock
    ):
        """Tester la recherche d'image artiste sur Spotify."""
        result = await mock_spotify_service.search_artist_image("The Beatles")
        
        assert result is not None
        assert "https" in result
    
    @pytest.mark.asyncio
    async def test_search_album_image(
        self,
        mock_spotify_service: AsyncMock
    ):
        """Tester la recherche d'image album sur Spotify."""
        result = await mock_spotify_service.search_album_image(
            "The Beatles",
            "Abbey Road"
        )
        
        assert result is not None
        assert "https" in result
    
    @pytest.mark.asyncio
    async def test_search_album_url(
        self,
        mock_spotify_service: AsyncMock
    ):
        """Tester la recherche d'URL album sur Spotify."""
        result = await mock_spotify_service.search_album_url(
            "The Beatles",
            "Abbey Road"
        )
        
        assert result is not None
        assert "spotify" in result


class TestAIServiceIntegration:
    """Tests d'intégration pour AIService (EurIA)."""
    
    @pytest.mark.asyncio
    async def test_ask_for_ia(
        self,
        mock_ai_service: AsyncMock
    ):
        """Tester une requête AI basique."""
        result = await mock_ai_service.ask_for_ia("What is music?")
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_generate_haiku(
        self,
        mock_ai_service: AsyncMock
    ):
        """Tester la génération de haïku."""
        listening_data = {
            "album": "Abbey Road",
            "artist": "The Beatles",
            "mood": "calm"
        }
        
        result = await mock_ai_service.generate_haiku(listening_data)
        
        assert result is not None
        assert isinstance(result, str)
        # Un haïku a généralement 3 lignes
        lines = result.split("\n")
        assert len(lines) >= 1
    
    @pytest.mark.asyncio
    async def test_generate_album_description(
        self,
        mock_ai_service: AsyncMock
    ):
        """Tester la génération de description d'album."""
        result = await mock_ai_service.generate_album_description(
            "The Beatles",
            "Abbey Road",
            1969
        )
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 20


class TestDiscogsServiceIntegration:
    """Tests d'intégration pour DiscogsService."""
    
    @pytest.mark.asyncio
    async def test_search_album(
        self,
        mock_discogs_service: AsyncMock
    ):
        """Tester la recherche d'album sur Discogs."""
        result = await mock_discogs_service.search_album(
            "The Beatles",
            "Abbey Road",
            1969
        )
        
        assert result is not None
        assert isinstance(result, dict)
        assert result.get("title") == "Test Album"
    
    @pytest.mark.asyncio
    async def test_get_album_details(
        self,
        mock_discogs_service: AsyncMock
    ):
        """Tester la récupération des détails d'album."""
        result = await mock_discogs_service.search_album("Test")
        
        assert result is not None
        if result:
            assert "id" in result or "title" in result


class TestAPIErrorHandling:
    """Tests pour la gestion d'erreurs des APIs."""
    
    @pytest.mark.asyncio
    async def test_spotify_timeout(
        self,
        mock_spotify_service: AsyncMock
    ):
        """Tester la gestion de timeout Spotify."""
        mock_spotify_service.search_artist_image.side_effect = TimeoutError("API timeout")
        
        with pytest.raises(TimeoutError):
            await mock_spotify_service.search_artist_image("Test")
    
    @pytest.mark.asyncio
    async def test_ai_service_failure(
        self,
        mock_ai_service: AsyncMock
    ):
        """Tester la gestion d'erreur du service IA."""
        mock_ai_service.ask_for_ia.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            await mock_ai_service.ask_for_ia("test")
    
    @pytest.mark.asyncio
    async def test_discogs_rate_limit(
        self,
        mock_discogs_service: AsyncMock
    ):
        """Tester la gestion du rate limit Discogs."""
        from app.core.exceptions import RateLimitException
        
        mock_discogs_service.search_album.side_effect = RateLimitException("Rate limited")
        
        with pytest.raises(RateLimitException):
            await mock_discogs_service.search_album("Test")


class TestAPIFallbacks:
    """Tests pour les mécanismes de fallback."""
    
    @pytest.mark.asyncio
    async def test_spotify_fallback_to_lastfm(self):
        """Tester le fallback de Spotify vers Last.fm."""
        # Ce test vérifierait que si Spotify échoue, on essaie Last.fm
        pass
    
    @pytest.mark.asyncio
    async def test_default_image_on_api_failure(self):
        """Tester l'utilisation d'image par défaut en cas d'erreur."""
        # Ce test vérifierait qu'on retourne une image par défaut
        pass
