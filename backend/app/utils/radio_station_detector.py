"""
Détection des stations de radio.

Module utilitaire pour identifier si un track en cours de lecture provient
d'une station de radio. Les stations de radio doivent être ignorées du tracking.
"""
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class RadioStationDetector:
    """Détecteur de stations de radio basé sur une liste configurable."""
    
    def __init__(self, radio_stations: Optional[List[str]] = None):
        """
        Initialise le détecteur avec une liste de stations de radio.
        
        Args:
            radio_stations: Liste des noms de stations de radio à détecter.
                           Par défaut, utilise une liste vide.
        """
        self.radio_stations = radio_stations or []
        # Normaliser les noms pour les comparaisons (minuscules)
        self.normalized_stations = [station.lower() for station in self.radio_stations]
        
    def is_radio_station(self, track_data: Dict) -> bool:
        """
        Vérifie si le track en cours provient d'une station de radio.
        
        La détection se fait en vérifiant:
        1. Le champ 'source' (si disponible)
        2. Le champ 'artist' (pour Roon ou Last.fm)
        3. Le champ 'album' (alternative si l'album contient le nom de station)
        
        Args:
            track_data: Dictionnaire contenant les données du track avec les clés:
                       - source (optionnel): Source du track (Roon, Last.fm, etc.)
                       - artist (str): Nom de l'artiste
                       - album (str): Nom de l'album
                       - zone_name (optionnel): Nom de la zone Roon
        
        Returns:
            bool: True si c'est une station de radio, False sinon.
        """
        if not self.normalized_stations:
            # Si aucune station n'est configurée, retourner False
            return False
        
        # Champs à vérifier (dans l'ordre de priorité)
        fields_to_check = [
            ('source', track_data.get('source', '')),
            ('artist', track_data.get('artist', '')),
            ('album', track_data.get('album', '')),
            ('zone_name', track_data.get('zone_name', '')),
        ]
        
        for field_name, field_value in fields_to_check:
            if field_value and self._matches_station(field_value):
                logger.info(f"📻 Station de radio détectée dans le champ '{field_name}': {field_value}")
                return True
        
        return False
    
    def _matches_station(self, text: str) -> bool:
        """
        Vérifie si le texte correspond à l'une des stations configurées.
        
        La comparaison est case-insensitive et cherche une correspondance
        exacte ou partielle (la station est contenue dans le texte).
        
        Args:
            text: Texte à vérifier.
        
        Returns:
            bool: True si le texte contient le nom d'une station.
        """
        text_normalized = text.lower()
        
        for station in self.normalized_stations:
            # Correspondance exacte
            if text_normalized == station:
                return True
            # Correspondance partielle (format "Artiste - Titre")
            if f" - {station}" in text_normalized or f"{station} - " in text_normalized:
                return True
            # Correspondance si la station est un préfixe
            if text_normalized.startswith(station):
                return True
        
        return False
    
    def get_configured_stations(self) -> List[str]:
        """
        Retourne la liste des stations actuellement configurées.
        
        Returns:
            List[str]: Liste des noms de stations de radio.
        """
        return self.radio_stations.copy()
    
    def add_station(self, station_name: str) -> None:
        """
        Ajoute une nouvelle station à la liste.
        
        Args:
            station_name: Nom de la station à ajouter.
        """
        if station_name not in self.radio_stations:
            self.radio_stations.append(station_name)
            self.normalized_stations.append(station_name.lower())
            logger.debug(f"✅ Station ajoutée: {station_name}")
    
    def remove_station(self, station_name: str) -> None:
        """
        Retire une station de la liste.
        
        Args:
            station_name: Nom de la station à retirer.
        """
        if station_name in self.radio_stations:
            idx = self.radio_stations.index(station_name)
            self.radio_stations.pop(idx)
            self.normalized_stations.pop(idx)
            logger.debug(f"❌ Station retirée: {station_name}")
