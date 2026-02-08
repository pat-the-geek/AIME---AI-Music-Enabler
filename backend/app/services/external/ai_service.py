"""Service AI unifié pour EurIA (Infomaniak AI) - fusion de ai_service.py et euria_service.py."""
import httpx
import json
import os
import logging
import asyncio
from typing import Optional, List, Dict, AsyncIterator, Any
from pathlib import Path
from app.core.retry import CircuitBreaker, retry_with_backoff
from app.core.exceptions import AIServiceException, TimeoutException

logger = logging.getLogger(__name__)

# Circuit breaker pour le service IA
ai_circuit_breaker = CircuitBreaker(
    "EurIA",
    failure_threshold=10,
    success_threshold=3,
    timeout=60,
    recovery_timeout=120
)


class AIService:
    """
    Unified AI client for EurIA API (Infomaniak's LLM service).

    Provides a complete interface to EurIA for music-related AI tasks including
    content generation, album search, streaming, and playlist generation. Handles
    authentication, retry logic, circuit breaking, and fallback strategies.

    Features:
        - OAuth2 Bearer token authentication
        - Automatic retry with exponential backoff
        - Circuit breaker for resilience
        - SSE streaming support
        - Sync/async dual interface
        - Configuration via secrets.json or environment variables

    API Methods:
        - ask_for_ia(): Single query with retry
        - ask_for_ia_stream(): Streaming SSE responses
        - search_albums_web(): Web search for albums
        - generate_album_description(): Create album descriptions
        - generate_collection_name(): Name for playlists
        - generate_album_info(): Detailed album info
        - generate_haiku(): Creative haiku generation
        - generate_playlist_by_prompt(): Track selection by prompt

    Configuration:
        - Loads from config/secrets.json if available
        - Falls back to environment variables
        - Required keys: 'url', 'bearer'

    Example:
        >>> ai = AIService()
        >>> description = await ai.generate_album_description(
        ...     "Pink Floyd",
        ...     "The Dark Side of the Moon"
        ... )
    """
    
    def __init__(self, url: Optional[str] = None, bearer: Optional[str] = None, 
                 max_attempts: int = 3, default_error_message: str = "Aucune information disponible"):
        """
        Initialize the EurIA AI service client.

        Sets up authentication and configuration for communicating with EurIA API.
        If url/bearer are provided, they override loaded configuration. Otherwise,
        configuration is loaded from secrets.json or environment variables.

        Args:
            url: Optional API endpoint URL. If None, loaded from config/secrets.json
                or EURIA_API_URL environment variable.
                Default: https://api.infomaniak.com/2/ai/106561/openai/v1/chat/completions
            bearer: Optional OAuth2 bearer token. If None, loaded from config.
                Can also use EURIA_BEARER_TOKEN environment variable.
            max_attempts: Number of retry attempts for failed requests. Defaults to 3.
                Used by retry_with_backoff decorator.
            default_error_message: Message to return on all errors (graceful failure).
                Defaults to "Aucune information disponible" (French).
                Users see this message instead of error stacktraces.

        Attributes Set:
            - url: API endpoint for requests
            - bearer: OAuth2 token for authentication
            - max_attempts: Retry count
            - default_error_message: Error fallback message
            - timeout: Fixed at 45 seconds for requests, 120s for streaming

        Configuration Loading:
            - Priority 1: Direct arguments (url, bearer)
            - Priority 2: secrets.json config/euria section
            - Priority 3: Environment variables (EURIA_API_URL, EURIA_BEARER_TOKEN)
            - Priority 4: Hard-coded defaults

        Example:
            >>> # Using environment variables
            >>> ai = AIService()
            >>>  # Or with explicit credentials
            >>> ai = AIService(
            ...     url="https://api.infomaniak.com/...",
            ...     bearer="sk-...",
            ...     max_attempts=5
            ... )

        Logging:
            - Logs INFO when secrets.json loaded successfully
            - Logs WARNING if secrets.json not found, falls back to env vars
        """
        # Charger la configuration
        config = self._load_config()
        
        self.url = url or config['url']
        self.bearer = bearer or config['bearer']
        self.max_attempts = max_attempts
        self.default_error_message = default_error_message
        self.timeout = 45.0  # Timeout de 45 secondes pour les requêtes IA
    
    def _load_config(self) -> Dict[str, Any]:
        """Charger la configuration EurIA depuis secrets.json ou variables d'environnement.
        
        Returns:
            Dict avec clés: url, bearer, max_attempts, default_error_message
            
        Raises:
            KeyError: Si clés manquantes dans config
        """
        # Chemin par défaut
        secrets_path = Path(__file__).parent.parent.parent.parent / "config" / "secrets.json"
        
        # Essayer de charger depuis secrets.json
        if secrets_path.exists():
            try:
                with open(secrets_path, 'r', encoding='utf-8') as f:
                    secrets = json.load(f)
                    euria_config = secrets.get('euria', {})
                    
                    logger.info("✅ Configuration EurIA chargée depuis secrets.json")
                    
                    return {
                        'url': euria_config.get('url', 'https://api.infomaniak.com/2/ai/106561/openai/v1/chat/completions'),
                        'bearer': euria_config.get('bearer', ''),
                        'max_attempts': euria_config.get('max_attempts', 3),
                        'default_error_message': euria_config.get('default_error_message', 'Aucune information disponible')
                    }
            except Exception as e:
                logger.warning(f"⚠️ Erreur chargement secrets.json: {e}")
        
        # Fallback: variables d'environnement
        logger.warning("⚠️ secrets.json non trouvé ou inaccessible, utilisation variables d'environnement")
        return {
            'url': os.getenv('EURIA_API_URL', 'https://api.infomaniak.com/2/ai/106561/openai/v1/chat/completions'),
            'bearer': os.getenv('EURIA_BEARER_TOKEN', ''),
            'max_attempts': int(os.getenv('EURIA_MAX_ATTEMPTS', '3')),
            'default_error_message': os.getenv('EURIA_ERROR_MESSAGE', 'Aucune information disponible')
        }
    
    # ===== API Communication Methods =====
    
    @retry_with_backoff(max_attempts=3, initial_delay=2.0, max_delay=15.0)
    async def ask_for_ia(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Send a prompt to EurIA and get a response with automatic retry.

        Sends a single-turn question to the EurIA LLM and returns the response.
        Implements circuit breaker and exponential backoff retry logic for
        resilience against transient failures.

        Args:
            prompt: The question or instruction for the AI.
                Can be multi-line text (e.g., prompt engineering with context).
            max_tokens: Maximum tokens in response. Defaults to 500.
                Limits response length; higher values allow longer responses.
                Typical values: 100 (short), 500 (medium), 2000 (long)

        Returns:
            str: The AI response text, or default_error_message if:
                - Circuit breaker is OPEN (service unavailable)
                - API returns 4xx error (client error, non-retryable)
                - Parsing response JSON fails
                - No choices in response

        Raises:
            httpx.TimeoutException: If request exceeds 45 second timeout.
                Will be retried up to max_attempts times with backoff.
            httpx.ConnectError: If unable to connect to EurIA servers.
                Will be retried (transient network failures).
            httpx.HTTPError: For 5xx server errors.
                Will be retried (transient server failures).

        Example:
            >>> ai = AIService()
            >>> response = await ai.ask_for_ia(
            ...     "Décris l'album The Dark Side of the Moon en 100 mots",
            ...     max_tokens=150
            ... )
            >>> print(response)
            "The Dark Side of the Moon est un chef-d'œuvre..."

        Circuit Breaker Behavior:
            - CLOSED: Requests proceed normally
            - OPEN: All requests fail immediately (returns default_error_message)
            - HALF_OPEN: Testing recovery, limited requests allowed
            - Opens after 10 consecutive failures
            - Closes after 3 consecutive successes

        Retry Logic (via @retry_with_backoff):
            - Max 3 attempts including initial request
            - Initial backoff: 2 seconds
            - Exponential increase up to 15 seconds max
            - Retries for timeout/connection/5xx errors only
            - 4xx errors (authentication, bad request) not retried

        Performance:
            - Typical response time: 1-3 seconds
            - With retry (on failure): 2-30 seconds depending on failure point
            - Streaming not supported (use ask_for_ia_stream for SSE)

        Logging:
            - Logs WARNING if circuit breaker is OPEN
            - Logs ERROR with HTTP status for 4xx/5xx errors
            - Logs ERROR for timeout/connection errors (before retry)
            - Logs ERROR for JSON parsing failures
            - Silent success (no log)

        Model Information:
            - Model: mistral3
            - Temperature: 0.7 (creative but consistent)
            - Stop tokens: None (responses end naturally)
        """
        try:
            # Vérifier le circuit breaker
            if ai_circuit_breaker.state == "OPEN":
                logger.warning("⚠️ Circuit breaker EurIA ouvert - service indisponible temporairement")
                return self.default_error_message
            
            headers = {
                "Authorization": f"Bearer {self.bearer}",
                "Content-Type": "application/json"
            }
            
            # Modèle mistral3 pour l'API EurIA
            payload = {
                "model": "mistral3",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.url,
                    headers=headers,
                    json=payload
                )
                
                # Vérifier les erreurs HTTP
                if response.status_code >= 400:
                    error_text = response.text
                    logger.error(f"❌ EurIA API Error {response.status_code}: {error_text}")
                    ai_circuit_breaker.record_failure()
                    
                    # Erreurs réessayables (5xx)
                    if response.status_code >= 500:
                        raise httpx.HTTPError(f"Server error {response.status_code}")
                    
                    # Erreur non réessayable (4xx)
                    return self.default_error_message
                
                response.raise_for_status()
                data = response.json()
                
                # Succès
                ai_circuit_breaker.record_success()
                
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"].strip()
                
                return self.default_error_message
                
        except httpx.TimeoutException as e:
            logger.error(f"⏱️ Timeout EurIA: {e}")
            ai_circuit_breaker.record_failure()
            raise
        except httpx.ConnectError as e:
            logger.error(f"🔗 Erreur connexion EurIA: {e}")
            ai_circuit_breaker.record_failure()
            raise
        except httpx.HTTPError as e:
            logger.error(f"❌ Erreur HTTP EurIA: {e}")
            ai_circuit_breaker.record_failure()
            raise
        except Exception as e:
            logger.error(f"❌ Erreur appel API EurIA: {e}")
            ai_circuit_breaker.record_failure()
            return self.default_error_message
    
    async def ask_for_ia_stream(self, prompt: str, max_tokens: int = 500) -> AsyncIterator[str]:
        """
        Stream a response from EurIA using Server-Sent Events (SSE).

        Sends a prompt and yields response chunks as they arrive from the AI,
        enabling real-time streaming to clients. Uses HTTP streaming for
        efficient long-running requests.

        Args:
            prompt: The question or instruction for the AI.
            max_tokens: Maximum tokens in response. Defaults to 500.

        Yields:
            str: SSE-formatted data lines as chunks arrive.
                Format: "data: {json_with_type_and_content}\n\n"
                Example: 'data: {"type": "chunk", "content": " world"}\n\n'
                Special: 'data: [ERROR] {error_message}\n\n' on error

        Raises:
            httpx.TimeoutException: If request exceeds 120 second timeout.
                Exception is caught, yielded as error format.
            httpx.ConnectError: If unable to connect to EurIA.
                Exception is caught, yielded as error format.

        Example:
            >>> ai = AIService()
            >>> async for chunk in ai.ask_for_ia_stream(
            ...     "Écrire un poème sur la musique"
            ... ):
            ...     print(chunk, end='', flush=True)
            data: {"type": "chunk", "content": "La musique"}
            data: {"type": "chunk", "content": " danse"}
            ...

        Circuit Breaker:
            - If OPEN, yields default error message immediately
            - Success recorded on [DONE] message
            - Failure recorded on any error

        Performance:
            - Timeout: 120 seconds (2 minutes, longer than ask_for_ia)
            - Streaming begins immediately (low initial latency)
            - Yields chunks as they arrive, not buffered
            - Suitable for long-form content generation

        Use Cases:
            - Real-time text generation in web UI
            - Streaming long articles or descriptions
            - Progressive display of AI responses
            - Web sockets or EventSource clients

        Implementation Details:
            - HTTP chunked transfer encoding
            - Parses SSE "data: " lines
            - Ignores keepalive/heartbeat lines
            - Stops on "[DONE]" message from API
            - Yields error chunks on exception

        Logging:
            - Logs WARNING if circuit breaker is OPEN
            - Logs ERROR on any exception (yields error chunk)
            - No success logging (streaming is natural)
        """
        try:
            # Vérifier le circuit breaker
            if ai_circuit_breaker.state == "OPEN":
                logger.warning("⚠️ Circuit breaker EurIA ouvert - service indisponible temporairement")
                yield f"data: {self.default_error_message}\n\n"
                return
            
            headers = {
                "Authorization": f"Bearer {self.bearer}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "mistral3",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": True  # Activer le streaming
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    self.url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status_code >= 400:
                        logger.error(f"❌ EurIA API Error {response.status_code}")
                        ai_circuit_breaker.record_failure()
                        yield f"data: {self.default_error_message}\n\n"
                        return
                    
                    # Lire le stream ligne par ligne
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Enlever "data: "
                            
                            if data_str.strip() == "[DONE]":
                                ai_circuit_breaker.record_success()
                                break
                            
                            try:
                                data = json.loads(data_str)
                                
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    
                                    if content:
                                        # Envoyer le chunk au format SSE
                                        yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
                            except json.JSONDecodeError:
                                continue
                    
        except Exception as e:
            logger.error(f"❌ Erreur streaming EurIA: {e}")
            ai_circuit_breaker.record_failure()
            yield f"data: [ERROR] {str(e)}\n\n"
    
    # ===== Content Generation Methods =====
    
    async def search_albums_web(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search for albums matching a natural language query using AI.

        Uses EurIA to interpret a natural language query and return a structured
        list of matching albums. Useful for semantic search that understands
        music genres, moods, decades, etc., not just keyword matching.

        Args:
            query: Natural language search query.
                Examples:
                - "Album hip-hop des années 90"
                - "Musique relaxante pour étudier"
                - "Meilleurs albums rock progressif"
            limit: Maximum albums to return. Defaults to 50.
                API limit: prevents huge JSON responses.

        Returns:
            List[Dict]: Albums matching the query, each with:
                {
                    "artist": "Pink Floyd",
                    "album": "The Dark Side of the Moon",
                    "year": 1973
                }
                Empty list if query fails or no results.

        Example:
            >>> ai = AIService()
            >>> albums = await ai.search_albums_web(
            ...     "Albums psychédéliques des années 70",
            ...     limit=20
            ... )
            >>> for album in albums:
            ...     print(f"{album['artist']} - {album['album']} ({album['year']})")
            Pink Floyd - The Dark Side of the Moon (1973)

        Error Handling:
            - Returns empty list on any error (no exceptions)
            - Logs errors for debugging
            - JSON parsing errors caught separately

        Implementation Details:
            - Sends structured prompt requesting JSON response
            - Cleans response (removes ```json markers)
            - Validates JSON structure
            - Truncates to limit

        Performance:
            - Depends on query complexity
            - Typical time: 2-5 seconds
            - Timeout: 45 seconds

        Logging:
            - Logs INFO for searches
            - Logs INFO for successful results count
            - Logs ERROR for JSON parse failures
            - Logs ERROR for API failures
            - Logs DEBUG with full response for debugging
        """
        logger.info(f"🌐 Recherche EurIA: {query}")
        
        # Créer un prompt pour EurIA demandant un résultat JSON
        prompt = f"""Tu es un expert en musique. Basé sur cette requête: "{query}"

Recherche et liste les meilleures sélections d'albums qui correspondent à cette demande.

Retourne UNIQUEMENT un JSON valide (pas d'autre texte avant ou après) avec ce format:
{{
  "albums": [
    {{"artist": "Artiste", "album": "Titre Album", "year": 2024}},
    {{"artist": "Artiste 2", "album": "Album 2", "year": 2023}}
  ]
}}

Limite ta réponse à {limit} albums maximum.
Assure-toi que les albums existent réellement et correspondent bien à la demande."""

        logger.info(f"📝 PROMPT ENVOYÉ À EURIA:\n{prompt}")
        
        try:
            logger.info("📡 Appel en cours à EurIA API...")
            response = await self.ask_for_ia(prompt, max_tokens=2000)
            logger.info(f"📡 RÉPONSE BRUTE D'EURIA ({len(response)} chars):\n{response}")
            
            # Parser le JSON
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.split('```')[1]
                if cleaned_response.startswith('json'):
                    cleaned_response = cleaned_response[4:]
                cleaned_response = cleaned_response.strip()
            
            logger.info(f"🧹 RÉPONSE NETTOYÉE:\n{cleaned_response}")
            
            data = json.loads(cleaned_response)
            
            albums = data.get('albums', [])
            logger.info(f"✅ {len(albums)} albums trouvés via EurIA: {[a.get('album') for a in albums[:3]]}")
            
            return albums[:limit]
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur parsing JSON EurIA: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"❌ Erreur recherche EurIA: {e}", exc_info=True)
            return []
    
    async def generate_album_description(self, artist: str, album: str, year: Optional[int] = None) -> str:
        """
        Generate a brief, engaging description for an album.

        Creates a 2-3 sentence description highlighting the album's musical
        style, atmosphere, and what makes it unique. Designed for music
        discovery interfaces.

        Args:
            artist: Name of the artist (e.g., "Pink Floyd").
            album: Title of the album (e.g., "The Dark Side of the Moon").
            year: Optional release year. If provided, included in context.

        Returns:
            str: Engaging 2-3 sentence description, or fallback on error:
                "Album {album} par {artist}"

        Example:
            >>> ai = AIService()
            >>> desc = await ai.generate_album_description(
            ...     "Pink Floyd",
            ...     "The Dark Side of the Moon",
            ...     1973
            ... )
            >>> print(desc)
            "The Dark Side of the Moon is an iconic..."

        Prompt Structure:
            - Contextualizes the album (style, era)
            - Requests specific focus: musical style, atmosphere, uniqueness
            - Limits response to 2-3 sentences
            - Targets discovery audience (non-experts)

        Performance:
            - Typical time: 1-3 seconds
            - Response limited to ~300 tokens
            - Fallback on error (no exceptions)

        Error Handling:
            - Returns fallback message on API error
            - Logs ERROR with exception details
            - No exceptions raised to caller

        Logging:
            - Logs INFO when generation starts
            - Logs INFO when description generated (character count)
            - Logs ERROR on failure
        """
        logger.info(f"✍️ Génération description: {artist} - {album}")
        
        year_str = f" ({year})" if year else ""
        prompt = f"""Génère une brève description captivante et informative pour l'album:
"{album}" par {artist}{year_str}

La description doit:
- Être entre 2-3 phrases
- Décrire le style musical et l'ambiance
- Mettre en avant ce qui rend cet album unique
- Être engageante pour un découvreur de musique

Réponds UNIQUEMENT avec la description, sans introduction."""

        try:
            description = await self.ask_for_ia(prompt, max_tokens=300)
            logger.info(f"✅ Description générée ({len(description)} caractères)")
            return description.strip()
        except Exception as e:
            logger.error(f"❌ Erreur génération description: {e}")
            return f"Album {album} par {artist}"
    
    async def generate_collection_name(self, query: str) -> str:
        """
        Generate a short, evocative name for a music collection/playlist.

        Creates a 2-4 word French name that captures the essence of a
        collection query. Useful for naming automatically-generated playlists.

        Args:
            query: Natural language description of the collection.
                Examples:
                - "Musique pour travailler le soir"
                - "Albums rock progressif des années 80"
                - "Chansons à danser l'été"

        Returns:
            str: Short collection name (2-4 words), or fallback on error:
                "Collection Découverte" (French)

        Example:
            >>> ai = AIService()
            >>> name = await ai.generate_collection_name(
            ...     "Upbeat electronic music for workingout"
            ... )
            >>> print(name)
            "Beat Synth Power"

        Prompt Requirements:
            - Short (2-4 words) - enforced by prompt
            - Synthetic and evocative - captures essence
            - Catchy and memorable - suitable for display
            - French preferred for French-speaking users

        Performance:
            - Very fast: 0.5-1 second typical
            - ~100 tokens max
            - Fallback on error

        Error Handling:
            - Returns "Collection Découverte" if generation fails
            - Logs ERROR with exception
            - No exceptions raised

        Logging:
            - Logs INFO on generation start
            - Logs INFO with generated name
            - Logs ERROR on failure
        """
        logger.info(f"🎨 Génération nom collection pour: {query}")
        
        prompt = f"""Tu dois créer un nom court et évocateur pour une collection d'albums.

Requête: "{query}"

Le nom doit:
- Être court (2-4 mots maximum)
- Synthétiser l'essence de la requête
- Être captivant et mémorable
- Être en français si possible

Réponds UNIQUEMENT avec le nom, sans guillemets ni explication."""

        try:
            name = await self.ask_for_ia(prompt, max_tokens=100)
            name = name.strip().strip('"').strip("'")
            logger.info(f"✅ Nom généré: {name}")
            return name if name else "Collection Découverte"
        except Exception as e:
            logger.error(f"❌ Erreur génération nom: {e}")
            return "Collection Découverte"
    
    async def generate_album_info(self, artist_name: str, album_title: str) -> Optional[str]:
        """
        Generate comprehensive album information (1800-2000 characters).

        Creates detailed, multi-paragraph album description including historical
        context, musical style, thematic analysis, cultural impact, and notable
        tracks. Designed for enriched music database entries.

        Args:
            artist_name: Name of the artist.
            album_title: Title of the album.

        Returns:
            str: Detailed album description (1800-2000 characters), or None if:
                - API fails
                - Response is default error message
                - Parsing fails

        Example:
            >>> ai = AIService()
            >>> info = await ai.generate_album_info(
            ...     "Pink Floyd",
            ...     "The Dark Side of the Moon"
            ... )
            >>> if info:
            ...     print(f"Generated {len(info)} characters")
            ...     # Use info for database enrichment

        Response Structure (from prompt):
            - Historical and cultural context
            - Musical style and influences
            - Main themes and atmosphere
            - Cultural impact and reception
            - Notable tracks (if relevant)
            - Heritage and influence on music

        Length Control:
            - Target: 1800-2000 characters exactly
            - Truncates at last complete sentence if exceeding
            - No truncation in middle of words

        Performance:
            - Timeout: 45 seconds
            - Token limit: 750 tokens (response may be shorter)
            - Typical time: 3-5 seconds

        Error Handling:
            - Returns None on any error
            - Handles truncation gracefully
            - Logs ERROR with details
            - No exceptions raised

        Quality Notes:
            - Requires working EurIA connection
            - Results vary by artist/album popularity
            - Less-known albums may get shorter/generic responses
            - Default error message is excluded from results

        Logging:
            - Logs ERROR if generation fails
            - Logs nothing on success
        """
        prompt = f"""Tu es un expert musical. Décris l'album "{album_title}" de {artist_name}.

IMPORTANT : Ta réponse doit faire EXACTEMENT entre 1800 et 2000 caractères. Ne dépasse JAMAIS 2000 caractères. Termine proprement tes phrases, ne t'arrête pas au milieu d'une phrase.

Inclus dans ta description :
- Le contexte historique et culturel de l'album
- Le style musical et les influences
- Les thèmes principaux et l'atmosphère
- L'impact culturel et la réception
- Les morceaux marquants si pertinent
- L'héritage et l'influence sur la musique

Sois factuel, précis et captivant. Structure ton texte en paragraphes courts."""
        
        try:
            response = await self.ask_for_ia(prompt, max_tokens=750)
            
            # Seulement si vraiment nécessaire (sécurité)
            if len(response) > 2000:
                # Trouver la dernière phrase complète avant 2000 caractères
                truncated = response[:2000]
                last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
                if last_period > 1500:  # Si on trouve une phrase complète
                    response = response[:last_period + 1]
                else:
                    response = response[:1997] + "..."
            
            return response if response != self.default_error_message else None
            
        except Exception as e:
            logger.error(f"❌ Erreur génération info album: {e}")
            return None
    
    async def generate_haiku(self, listening_data: dict) -> str:
        """
        Generate a poetic haiku capturing the essence of listening patterns.

        Creates a traditional 5-7-5 syllable haiku inspired by favorite artists,
        albums, and listening volume. Useful for personalized music insights and
        creative sharing features.

        Args:
            listening_data: Dictionary with:
                - top_artists (List[str]): Top 5 artist names
                - top_albums (List[str]): Top 5 album titles
                - total_tracks (int): Total number of track plays

        Returns:
            str: Haiku in French (3 lines, 5-7-5 syllables), or fallback on error:
                "Musique écoute / Notes qui dansent dans le temps / L'âme en harmonie"

        Example:
            >>> ai = AIService()
            >>> listening_data = {
            ...     "top_artists": ["Pink Floyd", "David Gilmour", ...],
            ...     "top_albums": ["The Wall", "The Dark Side of the Moon", ...],
            ...     "total_tracks": 2500
            ... }
            >>> haiku = await ai.generate_haiku(listening_data)
            >>> print(haiku)
            Silence vibrant
            Notes dans le noir profond
            Âme résonnée

        Haiku Format:
            - Line 1 (5 syllables): Establishing mood
            - Line 2 (7 syllables): Main theme
            - Line 3 (5 syllables): Resolution/reflection
            - Language: French preferred
            - Traditional poetic form

        Performance:
            - Very fast: 0.5-2 seconds typical
            - Token limit: 100 tokens
            - Fallback on error (no exceptions)

        Error Handling:
            - Returns fallback haiku if generation fails
            - Logs ERROR on failure
            - No exceptions raised

        Use Cases:
            - Music profile pages
            - Listening summary insights
            - Creative sharing (social media)
            - Year-end music reviews

        Logging:
            - Logs ERROR on failure only
        """
        prompt = f"""Tu es un poète spécialisé en haïkus. Crée un haïku qui capture l'essence des écoutes musicales suivantes:

Artistes principaux: {', '.join(listening_data.get('top_artists', [])[:5])}
Albums principaux: {', '.join(listening_data.get('top_albums', [])[:5])}
Nombre total d'écoutes: {listening_data.get('total_tracks', 0)}

Le haïku doit respecter la structure 5-7-5 syllabes et capturer l'ambiance musicale."""
        
        try:
            response = await self.ask_for_ia(prompt, max_tokens=100)
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur génération haïku: {e}")
            return "Musique écoute / Notes qui dansent dans le temps / L'âme en harmonie"
    
    async def generate_playlist_by_prompt(self, prompt: str, available_tracks: list) -> list:
        """
        Generate track selection by AI based on natural language prompt.

        Uses EurIA to interpret a DJ-style prompt and select 20-30 tracks
        from available collection that match the vibe/criteria.

        Args:
            prompt: Natural language description of desired playlist.
                Examples:
                - "Musique pour une fête en bord de piscine"
                - "Road trip au coucher de soleil"
                - "Concentration intense - focus mode"
            available_tracks: List of track dicts with:
                - id (int): Unique track ID
                - artist (str): Artist name
                - title (str): Track title  
                - album (str): Album name
                Limited to first 100 for context window.

        Returns:
            List[int]: Track IDs in recommended order.
                - Length: 20-30 tracks (AI decides)
                - Fallback: First 25 tracks if AI fails (no exceptions)
                - Empty list: Only if available_tracks is empty

        Example:
            >>> ai = AIService()
            >>> available = [
            ...     {"id": 1, "artist": "...", "title": "...", "album": "..."},
            ...     ...
            ... ]
            >>> track_ids = await ai.generate_playlist_by_prompt(
            ...     "Upbeat electronic for workout",
            ...     available
            ... )
            >>> print(f"Generated {len(track_ids)} track playlist")
            Generated 27 track playlist

        Prompt Strategy:
            - Frames AI as expert DJ
            - Provides track context (CSV-like format)
            - Requests ID-only response (clean parsing)
            - Limits context to 100 tracks to fit token window

        Track Selection:
            - AI expected to return 20-30 IDs
            - IDs parsed as comma-separated integers
            - Invalid IDs skipped
            - IDs verified against available tracks

        Performance:
            - Timeout: 45 seconds
            - Token limit: 200 (response is just numbers)
            - Typical time: 1-3 seconds

        Error Handling:
            - Returns first 25 tracks as fallback
            - Invalid/missing IDs skipped gracefully
            - Logs ERROR on parsing/API failure
            - No exceptions raised

        DJ Prompt Examples:
            - Genre-based: "Seulement du jazz des années 60"
            - Mood-based: "Triste et introspectif - playlist méditative"
            - Time-based: "Road trip longue distance - haute énergie"
            - Activity-based: "Workout cardio - rythme rapide"

        Logging:
            - Logs ERROR on API/parsing failure
            - No success logging

        Limitations:
            - Relies on artist/title quality in available_tracks
            - AI may not find obscure tracks
            - No guarantee of exact prompt adherence
            - Falls back to generic selection if AI fails
        """
        tracks_context = "\n".join([
            f"{t['id']}: {t['artist']} - {t['title']} ({t['album']})"
            for t in available_tracks[:100]  # Limiter le contexte
        ])
        
        full_prompt = f"""Tu es un DJ expert. Sélectionne les meilleurs tracks pour créer une playlist correspondant à: "{prompt}"

Tracks disponibles:
{tracks_context}

Réponds uniquement avec les IDs des tracks séparés par des virgules (ex: 1,5,12,3). Sélectionne entre 20 et 30 tracks."""
        
        try:
            response = await self.ask_for_ia(full_prompt, max_tokens=200)
            
            # Parser les IDs
            track_ids = []
            for part in response.split(','):
                try:
                    track_id = int(part.strip())
                    if any(t['id'] == track_id for t in available_tracks):
                        track_ids.append(track_id)
                except ValueError:
                    continue
            
            return track_ids if track_ids else [t['id'] for t in available_tracks[:25]]
            
        except Exception as e:
            logger.error(f"❌ Erreur génération playlist IA: {e}")
            return [t['id'] for t in available_tracks[:25]]
    
    # ===== Synchronous Wrappers (for compatibility) =====
    
    def search_albums_web_sync(self, query: str, limit: int = 50) -> List[Dict]:
        """Version synchrone de search_albums_web."""
        try:
            # Vérifier s'il y a déjà une boucle en course (le cas dans FastAPI/Uvicorn)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Créer une nouvelle boucle dans un thread séparé pour éviter les conflits
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        future = pool.submit(lambda: asyncio.run(self.search_albums_web(query, limit)))
                        result = future.result(timeout=30)
                        logger.info(f"✅ Albums trouvés (thread pool): {len(result)}")
                        return result
            except RuntimeError:
                # Pas de boucle d'événements du tout
                pass
            
            # Sinon utiliser asyncio.run directement
            result = asyncio.run(self.search_albums_web(query, limit))
            logger.info(f"✅ Albums trouvés (direct): {len(result)}")
            return result
        except Exception as e:
            logger.error(f"❌ Erreur recherche synchrone: {e}", exc_info=True)
            return []
    
    def generate_album_description_sync(self, artist: str, album: str, year: Optional[int] = None) -> str:
        """Version synchrone de generate_album_description."""
        try:
            # Vérifier s'il y a déjà une boucle en course
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        future = pool.submit(lambda: asyncio.run(self.generate_album_description(artist, album, year)))
                        result = future.result(timeout=30)
                        logger.info(f"✅ Description générée (thread pool): {album}")
                        return result
            except RuntimeError:
                pass
            
            result = asyncio.run(self.generate_album_description(artist, album, year))
            logger.info(f"✅ Description générée (direct): {album}")
            return result
        except Exception as e:
            logger.error(f"❌ Erreur génération description synchrone: {e}", exc_info=True)
            return f"Album {album} par {artist}"
    
    def generate_collection_name_sync(self, query: str) -> str:
        """Version synchrone de generate_collection_name."""
        try:
            # Vérifier s'il y a déjà une boucle en course
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        future = pool.submit(lambda: asyncio.run(self.generate_collection_name(query)))
                        result = future.result(timeout=15)
                        logger.info(f"✅ Nom collection généré (thread pool): {result}")
                        return result
            except RuntimeError:
                pass
            
            result = asyncio.run(self.generate_collection_name(query))
            logger.info(f"✅ Nom collection généré (direct): {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Erreur génération nom synchrone: {e}", exc_info=True)
            return "Collection Découverte"


# Alias for backward compatibility
EuriaService = AIService
