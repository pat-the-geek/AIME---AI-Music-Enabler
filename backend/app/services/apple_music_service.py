"""Service pour générer les URLs Apple Music."""
from typing import Optional
from urllib.parse import quote
import logging
import re

logger = logging.getLogger(__name__)


class AppleMusicService:
    """Service pour générer des URLs Apple Music pour les albums.
    
    ⚠️  CONSTRAINT IMPORTANT:
    - Les URLs Apple Music DOIVENT utiliser le format search ou un format compatible avec window.open()
    - Les formats directs ID (https://music.apple.com/album/id{ID}) NE FONCTIONNENT PAS avec window.open()
    - Les protocoles music:// NE FONCTIONNENT PAS avec window.open()
    - SEULEMENT les search URLs (https://music.apple.com/search?term=...) sont fiables cross-browser
    """
    
    # Patterns d'URLs incompatibles avec window.open()
    INCOMPATIBLE_PATTERNS = [
        r'^music://',  # iTunes protocol
        r'^https://music\.apple\.com/album/id',  # Direct ID format
    ]
    
    @staticmethod
    def is_compatible_url(url: str) -> bool:
        """
        Vérifie si une URL est compatible avec window.open().
        
        Args:
            url: URL à vérifier
            
        Returns:
            True si l'URL fonctionne avec window.open(), False sinon
        """
        if not url:
            return False
        
        # Vérifier les patterns incompatibles
        for pattern in AppleMusicService.INCOMPATIBLE_PATTERNS:
            if re.match(pattern, url):
                logger.warning(f"Incompatible Apple Music URL pattern detected: {url[:80]}")
                return False
        
        # Vérifier que c'est une URL valide
        if not url.startswith('https://music.apple.com/'):
            return False
            
        return True
    
    @staticmethod
    def generate_search_url(artist_name: str, album_title: str) -> str:
        """
        Génère une URL de recherche Apple Music pour un album.
        
        Cette méthode est la SEULE approche fiable pour la génération d'URLs
        dans un contexte browser (window.open()).
        
        Args:
            artist_name: Nom de l'artiste
            album_title: Titre de l'album
            
        Returns:
            URL de recherche Apple Music (format compatible avec window.open())
            
        Example:
            >>> url = AppleMusicService.generate_search_url("Pink Floyd", "The Wall")
            >>> print(url)
            'https://music.apple.com/search?term=The+Wall+Pink+Floyd'
        """
        if not artist_name or not album_title:
            return None
            
        search_query = f"{album_title} {artist_name}".strip()
        encoded_query = quote(search_query)
        url = f"https://music.apple.com/search?term={encoded_query}"
        
        logger.debug(f"Generated Apple Music search URL: {url}")
        return url
    
    @staticmethod
    def sanitize_url(url: str, artist_name: str, album_title: str) -> str:
        """
        Nettoie une URL Apple Music incompatible en la convertissant en search URL.
        
        Args:
            url: URL potentiellement incompatible
            artist_name: Nom de l'artiste (fallback)
            album_title: Titre de l'album (fallback)
            
        Returns:
            URL compatible avec window.open()
        """
        if url and AppleMusicService.is_compatible_url(url):
            return url
        
        logger.info(f"Sanitizing incompatible Apple Music URL: {url[:80] if url else 'None'}")
        return AppleMusicService.generate_search_url(artist_name, album_title)
    
    @staticmethod
    def generate_url_for_album(artist_name: str, album_title: str) -> Optional[str]:
        """
        Génère une URL Apple Music compatible avec window.open().
        
        ⚠️  IMPORTANT: Cette méthode retourne TOUJOURS une search URL
        pour garantir la compatibilité cross-browser avec window.open().
        
        Les tentatives précédentes d'URLs directes (avec IDs Apple Music directs
        ou protocoles music://) ont échoué car window.open() ne les supporte pas.
        
        Dans le futur, cette méthode pourrait être améliorée pour:
        - Appeler l'API Apple Music pour obtenir l'ID réel (pour lien direct en app)
        - Utiliser l'API Euria pour générer des URLs directes (si config disponible)
        - Cacher les résultats pour améliorer les performances
        
        Mais pour les URLs browser (window.open()), les search URLs restent la seule
        option fiable et universelle.
        
        Args:
            artist_name: Nom de l'artiste
            album_title: Titre de l'album
            
        Returns:
            URL Apple Music compatible (search URL) ou None si impossible à générer
        """
        try:
            return AppleMusicService.generate_search_url(artist_name, album_title)
        except Exception as e:
            logger.error(f"Error generating Apple Music URL for {album_title} by {artist_name}: {e}")
            return None
