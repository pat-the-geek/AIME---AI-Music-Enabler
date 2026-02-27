"""
Service Last.fm pour récupérer images d'artistes et albums, et URL d'album.
"""
import httpx
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class LastFMImageService:
    """
    Service pour récupérer images et URL d'albums/artistes via l'API Last.fm.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('LASTFM_API_KEY')
        self.base_url = 'http://ws.audioscrobbler.com/2.0/'

    async def get_album_image(self, artist_name: str, album_title: str) -> Optional[str]:
        """
        Récupère l'URL de l'image d'un album via Last.fm.
        """
        if not self.api_key:
            logger.warning("Clé API Last.fm manquante.")
            return None
        try:
            params = {
                'method': 'album.getinfo',
                'artist': artist_name,
                'album': album_title,
                'api_key': self.api_key,
                'format': 'json'
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, timeout=5.0)
                response.raise_for_status()
                data = response.json()
                album = data.get('album', {})
                if album and 'image' in album and isinstance(album['image'], list):
                    for img in reversed(album['image']):
                        if img.get('#text') and 'http' in img['#text']:
                            logger.info(f"  ✅ Image trouvée via Last.fm: {album_title}")
                            return img['#text']
        except Exception as e:
            logger.debug(f"  ⚠️ Last.fm image échouée: {e}")
        return None

    async def get_artist_image(self, artist_name: str) -> Optional[str]:
        """
        Récupère l'URL de l'image d'un artiste via Last.fm.
        """
        if not self.api_key:
            logger.warning("Clé API Last.fm manquante.")
            return None
        try:
            params = {
                'method': 'artist.getinfo',
                'artist': artist_name,
                'api_key': self.api_key,
                'format': 'json'
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, timeout=5.0)
                response.raise_for_status()
                data = response.json()
                artist = data.get('artist', {})
                if artist and 'image' in artist and isinstance(artist['image'], list):
                    for img in reversed(artist['image']):
                        if img.get('#text') and 'http' in img['#text']:
                            logger.info(f"  ✅ Image artiste trouvée via Last.fm: {artist_name}")
                            return img['#text']
        except Exception as e:
            logger.debug(f"  ⚠️ Last.fm image artiste échouée: {e}")
        return None

    async def get_album_url(self, artist_name: str, album_title: str) -> Optional[str]:
        """
        Récupère l'URL de la page album sur Last.fm.
        """
        if not self.api_key:
            logger.warning("Clé API Last.fm manquante.")
            return None
        try:
            params = {
                'method': 'album.getinfo',
                'artist': artist_name,
                'album': album_title,
                'api_key': self.api_key,
                'format': 'json'
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, timeout=5.0)
                response.raise_for_status()
                data = response.json()
                album = data.get('album', {})
                if album and 'url' in album:
                    logger.info(f"  ✅ URL album trouvée via Last.fm: {album['url']}")
                    return album['url']
        except Exception as e:
            logger.debug(f"  ⚠️ Last.fm URL album échouée: {e}")
        return None
