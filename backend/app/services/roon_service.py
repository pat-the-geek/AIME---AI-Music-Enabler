"""Service d'intégration avec Roon via pyroon."""
import logging
import threading
import time
from typing import Optional, Dict, Callable
from roonapi import RoonApi

logger = logging.getLogger(__name__)


class RoonService:
    """Service pour communiquer avec Roon."""
    
    def __init__(self, server: str, token: Optional[str] = None, app_info: Optional[Dict] = None, 
                 on_token_received: Optional[Callable[[str], None]] = None):
        """Initialiser le service Roon.
        
        Args:
            server: Adresse IP du serveur Roon (ex: "192.168.1.100")
            token: Token d'authentification sauvegardé (optionnel)
            app_info: Informations sur l'application (optionnel)
            on_token_received: Callback appelé quand un nouveau token est reçu
        """
        self.server = server
        self._token = token
        self.on_token_received = on_token_received
        
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
        
        # Connecter avec timeout pour éviter blocage
        self._connect_with_timeout()
    
    def _connect_with_timeout(self, timeout: int = 15):
        """Se connecter avec timeout pour éviter blocage indéfini."""
        thread = threading.Thread(target=self._connect, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            logger.warning(f"⚠️ Timeout connexion Roon après {timeout}s - serveur peut être inaccessible")
            self.roon_api = None
    
    def _connect(self):
        """Se connecter au serveur Roon."""
        try:
            # RoonApi nécessite (app_info, token, host, port)
            # Port par défaut Roon : 9330
            self.roon_api = RoonApi(self.app_info, self._token, self.server, 9330)
            
            # Enregistrer le callback pour les changements d'état
            self.roon_api.register_state_callback(self._state_callback)
            
            # Donner un peu de temps à RoonApi pour se connecter et obtenir le token
            time.sleep(1)
            
            # Essayer d'extraire le token après approbation
            if self.roon_api and hasattr(self.roon_api, 'token') and self.roon_api.token:
                new_token = self.roon_api.token
                # Si c'est un nouveau token (pas le même qu'avant), le sauvegarder
                if new_token != self._token:
                    logger.info(f"✅ Nouveau token Roon reçu après approbation")
                    self._token = new_token
                    # Appeler le callback pour sauvegarder le token
                    if self.on_token_received:
                        self.on_token_received(new_token)
            
            # Attendre que les zones soient chargées
            max_wait = 3  # Attendre max 3 secondes
            for i in range(max_wait):
                if hasattr(self.roon_api, 'zones') and self.roon_api.zones:
                    self.zones = self.roon_api.zones
                    logger.info(f"✅ {len(self.zones)} zone(s) Roon disponible(s)")
                    break
                time.sleep(1)
            else:
                logger.warning("⚠️ Aucune zone Roon trouvée après connexion")
            
            logger.info(f"✅ Connecté au serveur Roon: {self.server}:9330")
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
                
                # Extraire la durée (en secondes)
                duration_seconds = now_playing.get('length')
                
                return {
                    'title': three_line.get('line1', 'Unknown Title'),
                    'artist': three_line.get('line2', 'Unknown Artist'),
                    'album': three_line.get('line3', 'Unknown Album'),
                    'zone_id': zone_id,
                    'zone_name': zone_info.get('display_name', 'Unknown Zone'),
                    'duration_seconds': duration_seconds
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
    
    def play_track(self, zone_or_output_id: str, track_title: str, artist: str, album: str = None) -> bool:
        """Démarrer la lecture d'un morceau sur une zone.
        
        Note: Roon ne permet pas de jouer un track individuel via play_media().
        Cette méthode joue l'album contenant le track.
        
        Args:
            zone_or_output_id: ID de la zone ou output
            track_title: Titre du morceau (informatif seulement)
            artist: Artiste(s) - utilise le premier si plusieurs
            album: Album (optionnel mais recommandé)
        
        Returns:
            True si succès, False sinon
        """
        if not self.roon_api:
            logger.error("API Roon non disponible")
            return False
        
        try:
            # Si plusieurs artistes séparés par des virgules, prendre le premier
            primary_artist = artist.split(',')[0].strip() if artist else "Unknown"
            
            logger.debug(f"🎵 Lecture album pour: {track_title} - {primary_artist} ({album or 'N/A'})")
            
            # Générer des variantes d'artiste
            artist_variants = [primary_artist]
            if primary_artist.lower().startswith("the "):
                artist_variants.append(primary_artist[4:])
            if not primary_artist.lower().startswith("the "):
                artist_variants.append(f"The {primary_artist}")
            
            # Générer des variantes d'album (soundtracks)
            album_variants = []
            if album:
                album_variants = [album]
                album_variants.extend([
                    f"{album} [Music from the Motion Picture]",
                    f"{album} (Music from the Motion Picture)",
                    f"{album} [Original Motion Picture Soundtrack]",
                    f"{album} (Original Motion Picture Soundtrack)",
                    f"{album} [Soundtrack]",
                    f"{album} (Soundtrack)",
                ])
            else:
                album_variants = [None]
            
            # Essayer toutes les combinaisons d'artiste/album
            for test_artist in artist_variants:
                for test_album in album_variants:
                    if test_album:
                        # Jouer l'album complet
                        path = ["Library", "Artists", test_artist, test_album]
                    else:
                        # Jouer l'artiste
                        path = ["Library", "Artists", test_artist]
                    
                    try:
                        result = self.roon_api.play_media(
                            zone_or_output_id=zone_or_output_id,
                            path=path,
                            action=None,
                            report_error=False
                        )
                        
                        if result:
                            logger.info(f"✅ Album lancé (pour track: {track_title})")
                            return True
                    except Exception:
                        pass
            
            logger.warning(f"❌ Album non trouvé pour: {track_title} ({primary_artist} - {album})")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur play_track: {e}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur lecture: {e}")
            logger.error(f"   Track: {track_title}, Artiste: {artist}, Album: {album}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return False
    
    def queue_tracks(self, zone_or_output_id: str, track_title: str, artist: str, album: str = None) -> bool:
        """Ajouter un morceau à la queue Roon.
        
        Args:
            zone_or_output_id: ID de la zone ou output
            track_title: Titre du morceau
            artist: Artiste(s) - Roon cherche par le premier artiste
            album: Album (optionnel)
        
        Returns:
            True si succès, False sinon
        """
        if not self.roon_api:
            logger.error("API Roon non disponible")
            return False
        
        try:
            # Prendre le premier artiste
            primary_artist = artist.split(',')[0].strip() if artist else "Unknown"
            
            # Construire le chemin de navigation
            path = ["Library", "Artists", primary_artist]
            if album:
                path.append(album)
            
            logger.debug(f"📋 Ajout à queue: {track_title} - {primary_artist}")
            
            # Utiliser action="Queue" pour ajouter à la file d'attente
            result = self.roon_api.play_media(
                zone_or_output_id=zone_or_output_id,
                path=path,
                action="Queue",  # Ajouter à la queue au lieu de Play Now
                report_error=True
            )
            
            if result:
                logger.info(f"✅ Ajouté à la queue: {track_title}")
                return True
            else:
                logger.warning(f"❌ Impossible d'ajouter à la queue: {track_title}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erreur queue: {e}")
            return False
    
    def playback_control(self, zone_or_output_id: str, control: str = "play") -> bool:
        """Contrôler la lecture sur une zone.
        
        Args:
            zone_or_output_id: ID de la zone ou output
            control: Commande (play, pause, stop, next, previous)
        
        Returns:
            True si succès, False sinon
        """
        if not self.roon_api:
            logger.error("API Roon non disponible")
            return False
        
        try:
            self.roon_api.playback_control(zone_or_output_id, control)
            logger.info(f"✅ Contrôle lecture: {control} sur zone {zone_or_output_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur contrôle lecture: {e}")
            return False
    
    def play_album(self, zone_or_output_id: str, artist: str, album: str) -> bool:
        """Démarrer la lecture d'un album complet sur une zone.
        
        Utilise une recherche Roon pour trouver l'album, ce qui est plus robuste
        que de naviguer par le chemin exact.
        
        Args:
            zone_or_output_id: ID de la zone ou output
            artist: Artiste (s'il y a plusieurs, Roon cherche par le premier)
            album: Titre de l'album
        
        Returns:
            True si succès, False sinon
        """
        if not self.roon_api:
            logger.error("API Roon non disponible")
            return False
        
        try:
            logger.info(f"🎵 Tentative de lecture de l'album: {album}")
            logger.info(f"   Artiste: {artist}")
            logger.info(f"   Zone: {zone_or_output_id}")
            
            # Étape 1 : Chercher l'album via la recherche
            album_info = self.search_album(artist, album)
            
            if not album_info:
                logger.warning(f"❌ Album '{album}' non trouvé dans Roon")
                logger.warning(f"   Artiste: {artist}")
                logger.warning(f"   💡 Suggestions:")
                logger.warning(f"      - Vérifiez que l'album est dans votre librairie Roon")
                logger.warning(f"      - Parcourez manuellement Library > Artists dans Roon pour vérifier les noms exacts")
                logger.warning(f"      - Vérifiez l'orthographe de l'artiste et de l'album")
                return False
            
            # Étape 2 : Jouer l'album trouvé
            album_path = album_info['path']
            logger.debug(f"   Chemin utilisé: {album_path}")
            
            result = self.roon_api.play_media(
                zone_or_output_id=zone_or_output_id,
                path=album_path,
                action=None,
                report_error=True
            )
            
            if result:
                logger.info(f"✅ Album lancé: {album_info['display_name']} - {album_info['artist']}")
                return True
            else:
                logger.warning(f"❌ play_media retourna False pour l'album trouvé")
                logger.warning(f"   Album: {album_info['display_name']}")
                logger.warning(f"   Chemin: {album_path}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erreur lecture album: {e}")
            logger.error(f"   Album: {album}, Artiste: {artist}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return False
    
    def search_album(self, artist: str, album: str) -> Optional[Dict]:
        """Chercher un album en essayant différentes variantes du nom.
        
        Stratégie: Puisque Roon ne fournit pas d'API de navigation browse,
        on va directement tenter de jouer l'album avec différentes variantes
        de l'artiste ET de l'album.
        
        Args:
            artist: Nom de l'artiste
            album: Titre de l'album (peut être partiel)
        
        Returns:
            Dictionnaire avec les infos de l'album trouvé:
            {
                'path': [...],
                'display_name': 'Album Title',
                'artist': 'Artist Name'
            }
            ou None si non trouvé
        """
        if not self.roon_api:
            logger.error("API Roon non disponible")
            return None
        
        try:
            # Prendre le premier artiste s'il y en a plusieurs
            primary_artist = artist.split(',')[0].strip() if artist else "Unknown"
            
            logger.info(f"🔍 Recherche album Roon: '{album}' par '{primary_artist}'")
            logger.info(f"   (accepte noms partiels et variantes)")
            
            # Générer des variantes d'artiste (ex: "The Young Gods" -> "Young Gods")
            artist_variants = [primary_artist]
            
            # Essayer sans "The" au début
            if primary_artist.lower().startswith("the "):
                artist_variants.append(primary_artist[4:])
            
            # Essayer avec "The" si pas déjà présent
            if not primary_artist.lower().startswith("the "):
                artist_variants.append(f"The {primary_artist}")
            
            # Essayer avec des variantes communes d'espaces/traits
            artist_variants.append(primary_artist.replace("-", " "))
            artist_variants.append(primary_artist.replace(" ", "-"))
            
            # Générer des variantes d'album (soundtracks avec suffixes)
            album_variants = [album]
            album_variants.extend([
                f"{album} [Music from the Motion Picture]",
                f"{album} (Music from the Motion Picture)",
                f"{album} [Original Motion Picture Soundtrack]",
                f"{album} (Original Motion Picture Soundtrack)",
                f"{album} [Soundtrack]",
                f"{album} (Soundtrack)",
            ])
            
            # Essayer toutes les combinaisons
            for test_artist in artist_variants:
                logger.debug(f"   Tentative artiste: {test_artist}")
                
                for test_album in album_variants:
                    path = ["Library", "Artists", test_artist, test_album]
                    
                    if test_artist == primary_artist and test_album == album:
                        logger.info(f"   Tentative 1: Chemin exact [{test_artist} / {test_album}]")
                    else:
                        logger.debug(f"      → Variante: [{test_artist} / {test_album}]")
                    
                    result = self.roon_api.play_media(
                        zone_or_output_id=None,
                        path=path,
                        action=None,
                        report_error=False
                    )
                    
                    if result:
                        logger.info(f"   ✅ Album trouvé: '{test_album}' par '{test_artist}'")
                        return {
                            'path': path,
                            'display_name': test_album,
                            'artist': test_artist
                        }
            
            logger.warning(f"   ❌ Album '{album}' par '{primary_artist}' non trouvé")
            logger.warning(f"   💡 Variantes d'artiste testées: {artist_variants}")
            logger.warning(f"   💡 Variantes d'album testées: {album_variants}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche album: {e}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return None
    
    def pause_all(self) -> bool:
        """Mettre en pause toutes les zones.
        
        Returns:
            True si succès, False sinon
        """
        if not self.roon_api:
            logger.error("API Roon non disponible")
            return False
        
        try:
            self.roon_api.pause_all()
            logger.info("✅ Toutes les zones mises en pause")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur pause globale: {e}")
            return False
    
    def get_zone_by_name(self, zone_name: str) -> Optional[str]:
        """Récupérer l'ID d'une zone par son nom.
        
        Args:
            zone_name: Nom de la zone
        
        Returns:
            ID de la zone ou None si non trouvée
        """
        if not self.roon_api:
            return None
        
        try:
            zone_info = self.roon_api.zone_by_name(zone_name)
            if zone_info:
                return zone_info.get('zone_id')
        except Exception as e:
            logger.error(f"❌ Erreur recherche zone: {e}")
        
        return None
    
    def search_track(self, artist: str, album: str, track_title: str, zone_id: str = None) -> Optional[Dict]:
        """Chercher et retourner le chemin d'un track dans Roon.
        
        Teste différentes variantes de noms d'artiste/album.
        
        Args:
            artist: Nom de l'artiste
            album: Titre de l'album
            track_title: Titre du morceau
            zone_id: ID de la zone (optionnel, pour test de lecture)
        
        Returns:
            Dictionnaire avec les infos du track trouvé, ou None
        """
        if not self.roon_api:
            logger.error("API Roon non disponible")
            return None
        
        try:
            primary_artist = artist.split(',')[0].strip() if artist else "Unknown"
            
            logger.debug(f"🔍 Recherche track: '{track_title}' ({album} - {primary_artist})")
            
            # Générer des variantes d'artiste
            artist_variants = [primary_artist]
            if primary_artist.lower().startswith("the "):
                artist_variants.append(primary_artist[4:])
            if not primary_artist.lower().startswith("the "):
                artist_variants.append(f"The {primary_artist}")
            artist_variants.append(primary_artist.replace("-", " "))
            artist_variants.append(primary_artist.replace(" ", "-"))
            
            # Générer des variantes d'album
            album_variants = []
            if album:
                album_variants = [album]
                album_variants.extend([
                    f"{album} [Music from the Motion Picture]",
                    f"{album} (Music from the Motion Picture)",
                    f"{album} [Original Motion Picture Soundtrack]",
                    f"{album} (Original Motion Picture Soundtrack)",
                    f"{album} [Soundtrack]",
                    f"{album} (Soundtrack)",
                ])
            else:
                album_variants = [None]
            
            # Essayer toutes les combinaisons
            for test_artist in artist_variants:
                for test_album in album_variants:
                    if test_album:
                        path = ["Library", "Artists", test_artist, test_album, track_title]
                    else:
                        path = ["Library", "Artists", test_artist, track_title]
                    
                    try:
                        # Test avec zone_id si fourni
                        test_zone = zone_id if zone_id else None
                        result = self.roon_api.play_media(
                            zone_or_output_id=test_zone,
                            path=path,
                            action=None,
                            report_error=False
                        )
                        
                        if result:
                            logger.debug(f"   ✅ Track trouvé: {track_title}")
                            return {
                                'path': path,
                                'display_name': track_title,
                                'artist': test_artist,
                                'album': test_album,
                                'duration_seconds': None
                            }
                    except:
                        pass
            
            logger.debug(f"   ❌ Track '{track_title}' non trouvé")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche track: {e}")
            return None
    
    def get_track_duration(self, zone_id: str) -> Optional[int]:
        """Récupérer la durée du track en cours de lecture (en secondes).
        
        Args:
            zone_id: ID de la zone
        
        Returns:
            Durée en secondes, ou None si non disponible
        """
        try:
            now_playing = self.get_now_playing()
            if now_playing and 'duration' in now_playing:
                # Roon retourne la durée en secondes
                return now_playing.get('duration')
        except Exception as e:
            logger.debug(f"Impossible de récupérer la durée du track: {e}")
        
        return None
