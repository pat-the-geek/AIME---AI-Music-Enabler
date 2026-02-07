"""Service Spotify pour récupérer images d'artistes et albums."""
import httpx
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_lastfm_image(artist_name: str, album_title: str) -> Optional[str]:
    """Fallback: Chercher l'image via Last.fm si Spotify échoue."""
    try:
        api_key = os.getenv('API_KEY')  # Last.fm API key
        if not api_key:
            return None
        
        response = httpx.get(
            'http://ws.audioscrobbler.com/2.0/',
            params={
                'method': 'album.getinfo',
                'artist': artist_name,
                'album': album_title,
                'api_key': api_key,
                'format': 'json'
            },
            timeout=5.0
        )
        
        if response.status_code == 200:
            data = response.json()
            album = data.get('album', {})
            if album and 'image' in album and isinstance(album['image'], list):
                # Prendre la dernière image (la plus grande)
                for img in reversed(album['image']):
                    if img.get('#text') and 'http' in img['#text']:
                        logger.info(f"  ✅ Image trouvée via Last.fm: {album_title}")
                        return img['#text']
    except Exception as e:
        logger.debug(f"  ⚠️ Last.fm fallback échoué: {e}")
    
    return None


class SpotifyService:
    """Client pour l'API Spotify."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_url = "https://accounts.spotify.com/api/token"
        self.api_base_url = "https://api.spotify.com/v1"
    
    async def _get_access_token(self) -> str:
        """Obtenir un token d'accès Spotify."""
        if self.access_token:
            return self.access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret)
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            return self.access_token
    
    async def search_artist_image(self, artist_name: str) -> Optional[str]:
        """Rechercher l'image d'un artiste sur Spotify."""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/search",
                    params={"q": artist_name, "type": "artist", "limit": 1},
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                data = response.json()
                
                artists = data.get("artists", {}).get("items", [])
                if artists and artists[0].get("images"):
                    return artists[0]["images"][0]["url"]
                
                return None
                
        except Exception as e:
            logger.error(f"Erreur recherche artiste Spotify: {e}")
            return None
    
    async def search_album_image(self, artist_name: str, album_title: str) -> Optional[str]:
        """Rechercher l'image d'un album sur Spotify."""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                # Stratégie 1: Recherche avec artiste et album
                query = f"artist:{artist_name} album:{album_title}"
                response = await client.get(
                    f"{self.api_base_url}/search",
                    params={"q": query, "type": "album", "limit": 1},
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                data = response.json()
                
                albums = data.get("albums", {}).get("items", [])
                if albums and albums[0].get("images"):
                    logger.info(f"✅ Album trouvé avec artiste: {albums[0]['name']}")
                    return albums[0]["images"][0]["url"]
                
                # Stratégie 2: Recherche uniquement par titre d'album (fallback)
                logger.info(f"⚠️ Recherche avec artiste échouée, essai sans artiste...")
                query_fallback = f"album:{album_title}"
                response = await client.get(
                    f"{self.api_base_url}/search",
                    params={"q": query_fallback, "type": "album", "limit": 1},
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                data = response.json()
                
                albums = data.get("albums", {}).get("items", [])
                if albums and albums[0].get("images"):
                    logger.info(f"✅ Album trouvé sans artiste: {albums[0]['name']}")
                    return albums[0]["images"][0]["url"]
                
                return None
                
        except Exception as e:
            logger.error(f"Erreur recherche album Spotify: {e}")
            return None
    
    async def search_album_url(self, artist_name: str, album_title: str) -> Optional[str]:
        """Rechercher l'URL Spotify d'un album."""
        try:
            token = await self._get_access_token()
            
            query = f"artist:{artist_name} album:{album_title}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/search",
                    params={"q": query, "type": "album", "limit": 1},
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                data = response.json()
                
                albums = data.get("albums", {}).get("items", [])
                if albums:
                    return albums[0].get("external_urls", {}).get("spotify")
                
                return None
                
        except Exception as e:
            logger.error(f"Erreur recherche URL album Spotify: {e}")
            return None
    
    async def search_album_details(self, artist_name: str, album_title: str) -> Optional[dict]:
        """Rechercher les détails complets d'un album sur Spotify (URL + année).
        
        Stratégies multiples:
        1. artist:{name} album:{title} (strict)
        2. album:{title} (sans artiste)
        3. album:"{title}" (exact, avec guillemets)
        4. artist:{name} {title} (sans préfixe album:)
        5. {title} {artist_name} (simple, mots clés)
        6. Titre sans parenthèses (enlever remasters, éditions spéciales)
        """
        try:
            token = await self._get_access_token()
            
            import re
            
            # Normaliser les noms
            def normalize_name(name: str) -> str:
                """Enlever parenthèses et contenu superflu"""
                # Enlever (remaster), (extended), (remix), etc.
                cleaned = re.sub(r'\s*\([^)]*(?:remaster|extended|remix|edit|version|deluxe|special)[^)]*\)\s*', ' ', name, flags=re.IGNORECASE)
                # Enlever d'autres parenthèses
                cleaned = re.sub(r'\s*\([^)]*\)\s*', ' ', cleaned)
                # Nettoyer les espaces multiples
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                return cleaned
            
            album_clean = normalize_name(album_title)
            
            # Construire les stratégies de recherche avec la meilleure en premier
            strategies = [
                # Stratégie 1: Exact avec artiste
                (f'artist:"{artist_name}" album:"{album_title}"', "exacte avec artiste"),
                
                # Stratégie 2: Strict avec artiste
                (f'artist:{artist_name} album:{album_title}', "strict avec artiste"),
                
                # Stratégie 3: Album exact seul
                (f'album:"{album_title}"', "album exact"),
                
                # Stratégie 4: Avec titre nettoyé et artiste
                (f'artist:{artist_name} album:{album_clean}', "strict avec titre nettoyé"),
                
                # Stratégie 5: Album nettoyé seul
                (f'album:{album_clean}', "album nettoyé"),
                
                # Stratégie 6: Simple - artiste + album (sans préfixes)
                (f'{artist_name} {album_title}', "simple avec artiste"),
                
                # Stratégie 7: Simple avec titre nettoyé
                (f'{artist_name} {album_clean}', "simple avec titre nettoyé"),
                
                # Stratégie 8: Juste le titre
                (f'{album_title}', "titre seul"),
            ]
            
            async with httpx.AsyncClient() as client:
                for query, strategy_name in strategies:
                    try:
                        logger.info(f"  🔍 Tentative {strategy_name}: '{query}'")
                        response = await client.get(
                            f"{self.api_base_url}/search",
                            params={"q": query, "type": "album", "limit": 5},  # Augmenter la limite
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=10.0
                        )
                        response.raise_for_status()
                        data = response.json()
                        
                        albums = data.get("albums", {}).get("items", [])
                        if albums:
                            # Prendre le premier avec une image
                            for album in albums:
                                if album.get("images"):
                                    logger.info(f"  ✅ Trouvé avec {strategy_name}: {album.get('name')}")
                                    release_date = album.get("release_date", "")
                                    year = None
                                    if release_date:
                                        year = int(release_date.split("-")[0]) if release_date else None
                                    
                                    return {
                                        "spotify_url": album.get("external_urls", {}).get("spotify"),
                                        "year": year,
                                        "image_url": album["images"][0]["url"]
                                    }
                    except Exception as e:
                        logger.debug(f"    ⚠️ Stratégie {strategy_name} échouée: {e}")
                        continue
                
                logger.info(f"  ❌ Aucun album trouvé pour '{album_title}' de {artist_name}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur recherche détails album Spotify: {e}")
            return None
    
    async def get_artist_spotify_id(self, artist_name: str) -> Optional[str]:
        """Récupérer l'ID Spotify d'un artiste."""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/search",
                    params={"q": artist_name, "type": "artist", "limit": 1},
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                data = response.json()
                
                artists = data.get("artists", {}).get("items", [])
                if artists:
                    return artists[0]["id"]
                
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération ID artiste Spotify: {e}")
            return None
    
    def search_album_details_sync(self, artist_name: str, album_title: str) -> Optional[dict]:
        """Wrapper synchrone pour search_album_details (compatible Uvicorn)."""
        try:
            # Vérifier si une event loop est en cours d'exécution
            try:
                loop = asyncio.get_running_loop()
                # Si on est dans une event loop, utiliser ThreadPoolExecutor
                with ThreadPoolExecutor() as executor:
                    return executor.submit(
                        asyncio.run,
                        self.search_album_details(artist_name, album_title)
                    ).result()
            except RuntimeError:
                # Pas de event loop en cours, utiliser asyncio.run() directement
                return asyncio.run(
                    self.search_album_details(artist_name, album_title)
                )
        except Exception as e:
            logger.error(f"Erreur enrichissement Spotify (sync): {e}")
            return None
