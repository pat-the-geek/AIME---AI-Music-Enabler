"""Service AI unifié pour EurIA (Infomaniak AI) - fusion de ai_service.py et euria_service.py."""
import httpx
import json
import os
import logging
import asyncio
from typing import Optional, List, Dict
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
    """Client unifié pour l'API EurIA (Infomaniak AI).
    
    Fusionne les services eu_service.py et euria_service.py.
    Gère:
    - Communications bas niveau avec l'API EurIA
    - Configuration via secrets.json ou variables d'environnement
    - Streaming Server-Sent Events (SSE)
    - Génération de contenu (haïkus, articles, descriptions)
    - Recherche d'albums via IA
    - Circuit breaker et retry logic
    """
    
    def __init__(self, url: Optional[str] = None, bearer: Optional[str] = None, 
                 max_attempts: int = 3, default_error_message: str = "Aucune information disponible"):
        """Initialiser le service AI.
        
        Args:
            url: URL de l'API EurIA (utilise la config si None)
            bearer: Bearer token (utilise la config si None)
            max_attempts: Nombre de tentatives en cas d'erreur
            default_error_message: Message d'erreur par défaut
        """
        # Charger la configuration
        config = self._load_config()
        
        self.url = url or config['url']
        self.bearer = bearer or config['bearer']
        self.max_attempts = max_attempts
        self.default_error_message = default_error_message
        self.timeout = 45.0  # Timeout de 45 secondes pour les requêtes IA
    
    def _load_config(self) -> dict:
        """Charger la configuration EurIA depuis secrets.json ou variables d'environnement."""
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
        """Poser une question à l'IA avec retry logic.
        
        Args:
            prompt: Texte de la requête
            max_tokens: Nombre maximum de tokens dans la réponse
            
        Returns:
            Réponse de l'IA ou message d'erreur par défaut
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
    
    async def ask_for_ia_stream(self, prompt: str, max_tokens: int = 500):
        """Poser une question à l'IA en streaming (Server-Sent Events).
        
        Yields:
            str: Chunks de texte au fur et à mesure de la génération
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
        """Rechercher des albums sur le web via EurIA.
        
        Utilise l'IA pour rechercher les albums correspondant à la requête,
        retourne un résultat structuré en JSON.
        
        Args:
            query: Requête en langage naturel
            limit: Nombre d'albums à retourner
            
        Returns:
            Liste de dictionnaires avec: {artist, album, year}
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
        """Générer une description d'album via EurIA.
        
        Args:
            artist: Nom de l'artiste
            album: Titre de l'album
            year: Année de sortie (optionnel)
            
        Returns:
            Description générée par l'IA
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
        """Générer un nom de collection via EurIA.
        
        Génère un nom synthétique et évocateur basé sur la requête.
        
        Args:
            query: Requête en langage naturel
            
        Returns:
            Nom de collection généré
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
        """Générer une description d'album par IA (max 2000 caractères).
        
        Args:
            artist_name: Nom de l'artiste
            album_title: Titre de l'album
            
        Returns:
            Description de l'album ou None en cas d'erreur
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
        """Générer un haïku basé sur les données d'écoute.
        
        Args:
            listening_data: Dict avec 'top_artists', 'top_albums', 'total_tracks'
            
        Returns:
            Haïku généré
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
        """Générer une sélection de tracks basée sur un prompt.
        
        Args:
            prompt: Requête pour la sélection
            available_tracks: Liste de tracks avec {id, artist, title, album}
            
        Returns:
            Liste d'IDs de tracks sélectionnées
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
