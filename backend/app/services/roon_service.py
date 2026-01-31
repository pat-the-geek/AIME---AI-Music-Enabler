"""Service d'intégration avec Roon via pyroon."""
import logging
from typing import Optional, Dict
from roonapi import RoonApi

logger = logging.getLogger(__name__)


class RoonService:
    """Service pour communiquer avec Roon."""
    
    def __init__(self, server: str, token: Optional[str] = None, app_info: Optional[Dict] = None):
        """Initialiser le service Roon.
        
        Args:
            server: Adresse IP du serveur Roon (ex: "192.168.1.100")
            token: Token d'authentification sauvegardé (optionnel)
            app_info: Informations sur l'application (optionnel)
        """
        self.server = server
        self._token = token
        
        # Informations par défaut de l'application
        self.app_info = app_info or {
            "extension_id": "aime_music_tracker",
            "display_name": "AIME - AI Music Enabler",
            "display_version": "4.0.0",
            "publisher": "AIME",
            "email": "contact@aime.music"
        }
        
        self.roon_api = None
        self.zones = {}
        self._connect()
    
    def _connect(self):
        """Se connecter au serveur Roon."""
        try:
            self.roon_api = RoonApi(self.app_info, self._token, self.server)
            
            # Enregistrer le callback pour les changements d'état
            self.roon_api.register_state_callback(self._state_callback)
            
            logger.info(f"✅ Connecté au serveur Roon: {self.server}")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Roon: {e}")
            self.roon_api = None
    
    def _state_callback(self, event: str, changed_ids: list):
        """Callback appelé quand l'état change dans Roon.
        
        Args:
            event: Type d'événement ('zones_changed', 'zones_added', etc.)
            changed_ids: Liste des IDs des zones modifiées
        """
        logger.debug(f"Roon state callback - event: {event}, changed_ids: {changed_ids}")
        
        # Mettre à jour le cache des zones
        if self.roon_api and hasattr(self.roon_api, 'zones'):
            self.zones = self.roon_api.zones
    
    def get_now_playing(self) -> Optional[Dict]:
        """Récupérer le morceau actuellement en lecture sur Roon.
        
        Returns:
            Dict avec les informations du track ou None si rien ne joue
            Format: {
                'title': str,
                'artist': str,
                'album': str,
                'zone_id': str,
                'zone_name': str
            }
        """
        if not self.roon_api or not hasattr(self.roon_api, 'zones'):
            logger.warning("API Roon non disponible")
            return None
        
        try:
            # Parcourir toutes les zones pour trouver une lecture en cours
            zones = getattr(self.roon_api, 'zones', {})
            
            for zone_id, zone_info in zones.items():
                # Vérifier si la zone est en lecture
                state = zone_info.get('state', '')
                if state != 'playing':
                    continue
                
                # Extraire les informations du track en cours
                now_playing = zone_info.get('now_playing', {})
                if not now_playing:
                    continue
                
                three_line = now_playing.get('three_line', {})
                
                return {
                    'title': three_line.get('line1', 'Unknown Title'),
                    'artist': three_line.get('line2', 'Unknown Artist'),
                    'album': three_line.get('line3', 'Unknown Album'),
                    'zone_id': zone_id,
                    'zone_name': zone_info.get('display_name', 'Unknown Zone')
                }
            
            # Aucune zone en lecture
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération now playing Roon: {e}")
            return None
    
    def get_token(self) -> Optional[str]:
        """Récupérer le token d'authentification actuel.
        
        Returns:
            Token ou None
        """
        if self.roon_api:
            return getattr(self.roon_api, 'token', None)
        return None
    
    def save_token(self, filepath: str):
        """Sauvegarder le token dans un fichier.
        
        Args:
            filepath: Chemin du fichier où sauvegarder le token
        """
        token = self.get_token()
        if token:
            try:
                with open(filepath, 'w') as f:
                    f.write(token)
                logger.info(f"✅ Token Roon sauvegardé: {filepath}")
            except Exception as e:
                logger.error(f"❌ Erreur sauvegarde token Roon: {e}")
    
    def get_zones(self) -> Dict:
        """Récupérer toutes les zones disponibles.
        
        Returns:
            Dict des zones {zone_id: zone_info}
        """
        if self.roon_api and hasattr(self.roon_api, 'zones'):
            return getattr(self.roon_api, 'zones', {})
        return {}
    
    def is_connected(self) -> bool:
        """Vérifier si le service est connecté à Roon.
        
        Returns:
            True si connecté, False sinon
        """
        return self.roon_api is not None
