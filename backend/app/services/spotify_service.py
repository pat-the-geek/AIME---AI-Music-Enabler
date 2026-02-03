"""Service Spotify pour récupérer images d'artistes et albums."""
import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)


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
        """Rechercher les détails complets d'un album sur Spotify (URL + année)."""
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
                if albums:
                    album = albums[0]
                    logger.info(f"✅ Album trouvé avec artiste: {album.get('name')}")
                    logger.info(f"📸 Images dans réponse: {album.get('images')}")
                    release_date = album.get("release_date", "")
                    year = None
                    if release_date:
                        # La date peut être au format YYYY ou YYYY-MM-DD
                        year = int(release_date.split("-")[0]) if release_date else None
                    
                    return {
                        "spotify_url": album.get("external_urls", {}).get("spotify"),
                        "year": year,
                        "image_url": album["images"][0]["url"] if album.get("images") else None
                    }
                
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
                if albums:
                    album = albums[0]
                    logger.info(f"✅ Album trouvé sans artiste: {album.get('name')}")
                    logger.info(f"📸 Images dans réponse: {album.get('images')}")
                    release_date = album.get("release_date", "")
                    year = None
                    if release_date:
                        # La date peut être au format YYYY ou YYYY-MM-DD
                        year = int(release_date.split("-")[0]) if release_date else None
                    
                    return {
                        "spotify_url": album.get("external_urls", {}).get("spotify"),
                        "year": year,
                        "image_url": album["images"][0]["url"] if album.get("images") else None
                    }
                
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
