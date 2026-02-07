"""Service d'intégration avec Roon via le bridge Node.js (node-roon-api officiel).

Ce service communique avec le microservice roon-bridge qui utilise exclusivement
l'API officielle RoonLabs (https://github.com/RoonLabs/node-roon-api).
"""
import logging
import time
from typing import Optional, Dict, Callable

import httpx

logger = logging.getLogger(__name__)

# Timeout par défaut pour les requêtes HTTP vers le bridge
DEFAULT_TIMEOUT = 5.0
PLAY_TIMEOUT = 10.0  # Plus long pour les opérations de navigation/browse


class RoonService:
    """Service pour communiquer avec Roon via le bridge Node.js."""

    def __init__(
        self,
        server: str,
        token: Optional[str] = None,
        app_info: Optional[Dict] = None,
        on_token_received: Optional[Callable[[str], None]] = None,
        bridge_url: Optional[str] = None,
    ):
        """Initialiser le service Roon.

        Args:
            server: Adresse IP du serveur Roon (passée au bridge via env).
            token: Token d'authentification (géré par le bridge, conservé pour compatibilité).
            app_info: Informations sur l'application (conservé pour compatibilité).
            on_token_received: Callback (conservé pour compatibilité, non utilisé).
            bridge_url: URL du bridge Node.js (ex: "http://localhost:9330").
        """
        self.server = server
        self._token = token
        self.on_token_received = on_token_received
        self.app_info = app_info or {}

        # URL du bridge Node.js
        self.bridge_url = bridge_url or "http://localhost:3330"

        # Vérifier la connexion au bridge
        self._connected = False
        self._check_bridge()

    # ========================================================================
    # Connexion / statut
    # ========================================================================

    def _check_bridge(self):
        """Vérifier que le bridge Node.js est accessible et connecté à Roon."""
        try:
            resp = httpx.get(f"{self.bridge_url}/status", timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                self._connected = data.get("connected", False)
                if self._connected:
                    logger.info(
                        "Bridge Roon connecté à %s (core: %s)",
                        self.server,
                        data.get("core_name", "?"),
                    )
                else:
                    logger.warning("Bridge Roon accessible mais pas encore connecté au Core")
            else:
                logger.warning("Bridge Roon a répondu %d", resp.status_code)
                self._connected = False
        except Exception as e:
            logger.warning("Bridge Roon inaccessible (%s): %s", self.bridge_url, e)
            self._connected = False

    def is_connected(self) -> bool:
        """Vérifier si le bridge est connecté à Roon Core."""
        try:
            resp = httpx.get(f"{self.bridge_url}/status", timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                self._connected = resp.json().get("connected", False)
                return self._connected
        except Exception:
            pass
        self._connected = False
        return False

    # ========================================================================
    # Zones
    # ========================================================================

    def get_zones(self) -> Dict:
        """Récupérer toutes les zones disponibles.

        Returns:
            Dict des zones {zone_id: zone_info}
        """
        try:
            resp = httpx.get(f"{self.bridge_url}/zones", timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                zones_list = data.get("zones", [])
                return {z["zone_id"]: z for z in zones_list}
        except Exception as e:
            logger.error("Erreur récupération zones: %s", e)
        return {}

    def get_zone_by_name(self, zone_name: str) -> Optional[str]:
        """Récupérer l'ID d'une zone par son nom.

        Args:
            zone_name: Nom de la zone

        Returns:
            ID de la zone ou None si non trouvée
        """
        try:
            resp = httpx.get(
                f"{self.bridge_url}/zones/{zone_name}",
                timeout=DEFAULT_TIMEOUT,
            )
            if resp.status_code == 200:
                return resp.json().get("zone_id")
        except Exception as e:
            logger.error("Erreur recherche zone '%s': %s", zone_name, e)
        return None

    # ========================================================================
    # Now Playing
    # ========================================================================

    def get_now_playing(self) -> Optional[Dict]:
        """Récupérer le morceau actuellement en lecture sur Roon.

        Returns:
            Dict avec les informations du track ou None si rien ne joue.
            Format: {
                'title': str,
                'artist': str,
                'album': str,
                'zone_id': str,
                'zone_name': str,
                'duration_seconds': int | None,
                'image_url': str | None
            }
        """
        try:
            resp = httpx.get(f"{self.bridge_url}/now-playing", timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                if not data.get("playing", False):
                    return None

                result = {
                    "title": data.get("title", "Unknown Title"),
                    "artist": data.get("artist", "Unknown Artist"),
                    "album": data.get("album", "Unknown Album"),
                    "zone_id": data.get("zone_id", ""),
                    "zone_name": data.get("zone_name", "Unknown Zone"),
                    "duration_seconds": data.get("duration_seconds"),
                    "image_url": None,
                }

                # Construire l'URL d'image via le bridge si image_key est disponible
                image_key = data.get("image_key")
                if image_key:
                    result["image_url"] = (
                        f"{self.bridge_url}/image/{image_key}?scale=fit&width=300&height=300"
                    )

                return result
        except Exception as e:
            logger.error("Erreur récupération now playing: %s", e)
        return None

    # ========================================================================
    # Playback Control
    # ========================================================================

    def playback_control(
        self, zone_or_output_id: str, control: str = "play", max_retries: int = 2
    ) -> bool:
        """Contrôler la lecture sur une zone avec retry logic.

        Args:
            zone_or_output_id: ID de la zone ou output
            control: Commande (play, pause, stop, next, previous)
            max_retries: Nombre maximum de tentatives

        Returns:
            True si succès, False sinon
        """
        for attempt in range(max_retries):
            try:
                logger.debug(
                    "Contrôle '%s' sur zone %s (tentative %d/%d)",
                    control, zone_or_output_id, attempt + 1, max_retries,
                )
                resp = httpx.post(
                    f"{self.bridge_url}/control",
                    json={
                        "zone_or_output_id": zone_or_output_id,
                        "control": control,
                    },
                    timeout=DEFAULT_TIMEOUT,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    logger.info("Contrôle lecture: %s (état: %s)", control, data.get("state"))
                    return True
                else:
                    logger.warning(
                        "Contrôle '%s' échoué (HTTP %d): %s",
                        control, resp.status_code, resp.text,
                    )
            except Exception as e:
                logger.warning("Tentative %d/%d échouée: %s", attempt + 1, max_retries, e)

            if attempt < max_retries - 1:
                time.sleep(0.3)

        logger.error("Erreur contrôle lecture après %d tentatives", max_retries)
        return False

    # ========================================================================
    # Search Album in Roon Library
    # ========================================================================

    def search_album_in_roon(
        self, artist: str, album: str, timeout_seconds: float = 30.0
    ) -> Optional[Dict]:
        """Chercher un album dans la bibliothèque Roon et retourner les détails si trouvé.

        Essaie plusieurs variantes du nom d'album (avec Deluxe Edition, etc.)
        pour trouver l'album exact dans la bibliothèque Roon.

        Args:
            artist: Nom de l'artiste
            album: Titre de l'album
            timeout_seconds: Timeout global pour toutes les recherches

        Returns:
            Dict avec 'found': bool, 'exact_name': str si trouvé, None sinon
            Exemple: {'found': True, 'exact_name': 'Lucky Shiner (Deluxe Edition)'}
        """
        try:
            start_time = time.time()
            logger.info("Recherche album dans Roon: %s - %s", artist, album)

            # Essayer plusieurs variantes du nom d'album
            variants = [
                f"{album} (Deluxe Edition)",  # La variante exacte la plus courante
                f"{album} Deluxe Edition",     # Sans parenthèses
                f"{album} - Deluxe Edition",   # Avec tiret
                f"{album} (Deluxe)",
                album,  # Nom exact en dernier
            ]

            elapsed = time.time() - start_time
            
            # Essayer chaque variante
            for idx, variant in enumerate(variants):
                elapsed = time.time() - start_time
                
                # Arrêter à 85% du timeout global
                if elapsed > timeout_seconds * 0.85:
                    logger.warning("Approche du timeout global (%.1fs/%.1fs), arrêt", elapsed, timeout_seconds)
                    return {"found": False, "artist": artist, "album": album}
                
                # Timeout pour cette variante
                remaining_time = timeout_seconds - elapsed
                variants_left = len(variants) - idx
                variant_timeout = min(8.0, max(1.0, remaining_time / (variants_left + 0.5)))
                
                if variant_timeout <= 0.5:
                    logger.warning("Timeout épuisé avant variante %d: %s", idx + 1, variant)
                    return {"found": False, "artist": artist, "album": album}
                
                logger.info("Essai variante (%d/%d, %.1fs elapsed): %s - %s", 
                           idx + 1, len(variants), elapsed, artist, variant)
                
                try:
                    resp = httpx.post(
                        f"{self.bridge_url}/search-album",
                        json={
                            "artist": artist,
                            "album": variant,
                        },
                        timeout=variant_timeout,
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("found"):
                            exact_name = data.get("exact_name", variant)
                            elapsed_total = time.time() - start_time
                            logger.info(
                                "✓ Album trouvé dans Roon en %.2fs: %s",
                                elapsed_total,
                                exact_name,
                            )
                            return {
                                "found": True,
                                "exact_name": exact_name,
                                "artist": artist,
                            }
                except httpx.TimeoutException:
                    logger.debug("Timeout variante %d: %s", idx + 1, variant)
                    continue
                
            # Aucune variante trouvée
            elapsed_total = time.time() - start_time
            logger.info(
                "✗ Album non trouvé après %d variantes (%.2fs): %s - %s",
                len(variants),
                elapsed_total,
                artist,
                album,
            )
            return {"found": False, "artist": artist, "album": album}

        except Exception as e:
            logger.error("Erreur recherche album: %s", e)
            return None


    # ========================================================================
    # Play Album
    # ========================================================================

    def play_album(self, zone_or_output_id: str, artist: str, album: str) -> bool:
        """Démarrer la lecture d'un album complet sur une zone.

        Utilise le browse API du bridge pour naviguer dans Library > Artists > artist > album.

        Args:
            zone_or_output_id: ID de la zone ou output
            artist: Artiste
            album: Titre de l'album

        Returns:
            True si succès, False sinon
        """
        try:
            start_time = time.time()
            logger.info("Tentative de lecture de l'album: %s - %s", artist, album)

            resp = httpx.post(
                f"{self.bridge_url}/play-album",
                json={
                    "zone_or_output_id": zone_or_output_id,
                    "artist": artist,
                    "album": album,
                },
                timeout=PLAY_TIMEOUT,
            )

            total_time = time.time() - start_time

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    logger.info("Album lancé en %.2fs: %s - %s", total_time, artist, album)
                    return True

            logger.warning(
                "Impossible de lancer l'album après %.2fs: %s - %s (HTTP %d)",
                total_time, artist, album, resp.status_code,
            )
            return False

        except Exception as e:
            logger.error("Erreur lecture album: %s", e, exc_info=True)
            return False

    def play_album_with_timeout(
        self,
        zone_or_output_id: str,
        artist: str,
        album: str,
        timeout_seconds: float = 15.0,
    ) -> Optional[bool]:
        """Essayer de lancer un album avec timeout.

        Returns:
            True si succès, False si échec explicite, None si timeout.
        """
        try:
            start_time = time.time()
            logger.info("play_album_with_timeout: %s - %s (timeout=%.1fs)", artist, album, timeout_seconds)
            
            resp = httpx.post(
                f"{self.bridge_url}/play-album",
                json={
                    "zone_or_output_id": zone_or_output_id,
                    "artist": artist,
                    "album": album,
                },
                timeout=timeout_seconds + 0.5,  # Petite marge pour le réseau seulement
            )

            elapsed = time.time() - start_time
            
            if resp.status_code == 200:
                data = resp.json()
                success = data.get("success", False)
                logger.info("play_album_with_timeout result: %s in %.2fs for %s - %s", success, elapsed, artist, album)
                return success
            elif resp.status_code == 404:
                logger.warning("play_album_with_timeout: album not found in %.2fs: %s - %s", elapsed, artist, album)
                return False
            else:
                logger.warning("play_album_with_timeout: HTTP %d in %.2fs for %s - %s", resp.status_code, elapsed, artist, album)
                return None

        except httpx.TimeoutException:
            logger.warning(
                "play_album timeout après %.1fs pour: %s - %s",
                timeout_seconds, artist, album,
            )
            return None
        except Exception as e:
            logger.error("Erreur play_album_with_timeout: %s", e)
            return None

    def play_album_with_variants(
        self,
        zone_or_output_id: str,
        artist: str,
        album: str,
        timeout_seconds: float = 15.0,
    ) -> Optional[bool]:
        """Essayer de jouer un album en essayant plusieurs variantes du nom.
        
        Si l'album exact n'existe pas, essaie les variantes les plus courantes :
        - Album (Deluxe Edition)
        - Album (Deluxe)
        
        Chaque variante a un timeout très réduit pour éviter de bloquer trop longtemps.
        
        Returns:
            True si succès, False si échec explicite, None si timeout général.
        """
        # Seulement les variantes les plus probables pour réduire le temps total
        # IMPORTANT: Chercher d'abord la variante Deluxe Edition car c'est probablement celle qui existe
        variants = [
            f"{album} (Deluxe Edition)",  # La variante exacte
            f"{album} Deluxe Edition",     # Sans parenthèses
            f"{album} - Deluxe Edition",   # Avec tiret
            f"{album} (Deluxe)",
            album,  # Nom exact en dernier
        ]
        
        start_time = time.time()
        
        # Essayer chaque variante avec un timeout propor tionnel
        for idx, variant in enumerate(variants):
            elapsed = time.time() - start_time
            
            # Vérifier si on approche du timeout global (arrêter à 85% du timeout)
            if elapsed > timeout_seconds * 0.85:
                logger.warning("Approche du timeout global (%.1fs/%.1fs), arrêt des variantes", elapsed, timeout_seconds)
                return None
            
            # Timeout disponible divisé entre variantes restantes
            remaining_time = timeout_seconds - elapsed
            variants_left = len(variants) - idx
            variant_timeout = min(25.0, max(1.0, remaining_time / (variants_left + 0.5)))
            
            if variant_timeout <= 0.5:
                logger.warning("Timeout épuisé avant de pouvoir essayer variante %d: %s", idx + 1, variant)
                return None
            
            logger.info("Essai variante (%d/%d, %.1fs elapsed, %.1fs timeout): %s - %s", idx + 1, len(variants), elapsed, variant_timeout, artist, variant)
            
            result = self.play_album_with_timeout(
                zone_or_output_id=zone_or_output_id,
                artist=artist,
                album=variant,
                timeout_seconds=variant_timeout,
            )
            
            # Si succès, retourner immédiatement
            if result is True:
                logger.info("✓ Album trouvé avec variante: %s (%.2fs)", variant, time.time() - start_time)
                return True
            
            # Si timeout global, retourner None
            elif result is None:
                elapsed_now = time.time() - start_time
                logger.warning("Timeout lors de la tentative avec variante: %s (%.2fs elapsed)", variant, elapsed_now)
                return None
            
            # Si False (not found), essayer la variante suivante
            logger.debug("Album pas trouvé pour variante: %s", variant)
        
        # Aucune variante trouvée
        elapsed = time.time() - start_time
        logger.warning("Album non trouvé après %d variantes (%.2fs): %s - %s", len(variants), elapsed, artist, album)
        return False

    # ========================================================================
    # Play Track
    # ========================================================================

    def play_track(
        self,
        zone_or_output_id: str,
        track_title: str,
        artist: str,
        album: str = None,
    ) -> bool:
        """Démarrer la lecture d'un morceau sur une zone.

        Note: Roon ne permet pas de jouer un track individuel directement.
        Cette méthode joue l'album contenant le track.

        Args:
            zone_or_output_id: ID de la zone ou output
            track_title: Titre du morceau (informatif)
            artist: Artiste(s) - utilise le premier si plusieurs
            album: Album (optionnel mais recommandé)

        Returns:
            True si succès, False sinon
        """
        try:
            logger.debug("Lecture track: %s - %s (%s)", track_title, artist, album or "N/A")

            # Si on a un album, jouer l'album
            if album:
                primary_artist = artist.split(",")[0].strip() if artist else "Unknown"
                return self.play_album(zone_or_output_id, primary_artist, album)

            # Sinon essayer via le bridge play-track
            resp = httpx.post(
                f"{self.bridge_url}/play-track",
                json={
                    "zone_or_output_id": zone_or_output_id,
                    "artist": artist,
                    "track_title": track_title,
                    "album": album,
                },
                timeout=PLAY_TIMEOUT,
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    logger.info("Track lancé: %s - %s", track_title, artist)
                    return True

            logger.warning("Impossible de lancer le track: %s - %s", track_title, artist)
            return False

        except Exception as e:
            logger.error("Erreur play_track: %s", e)
            return False

    # ========================================================================
    # Queue
    # ========================================================================

    def queue_tracks(
        self,
        zone_or_output_id: str,
        track_title: str,
        artist: str,
        album: str = None,
    ) -> bool:
        """Ajouter un morceau à la queue Roon.

        Args:
            zone_or_output_id: ID de la zone ou output
            track_title: Titre du morceau
            artist: Artiste(s)
            album: Album (optionnel)

        Returns:
            True si succès, False sinon
        """
        try:
            resp = httpx.post(
                f"{self.bridge_url}/queue",
                json={
                    "zone_or_output_id": zone_or_output_id,
                    "artist": artist,
                    "album": album or "",
                },
                timeout=PLAY_TIMEOUT,
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    logger.info("Ajouté à la queue: %s - %s", track_title, artist)
                    return True

            logger.warning("Impossible d'ajouter à la queue: %s", track_title)
            return False

        except Exception as e:
            logger.error("Erreur queue: %s", e)
            return False

    # ========================================================================
    # Pause All
    # ========================================================================

    def pause_all(self) -> bool:
        """Mettre en pause toutes les zones.

        Returns:
            True si succès, False sinon
        """
        try:
            resp = httpx.post(f"{self.bridge_url}/pause-all", timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                logger.info("Toutes les zones mises en pause")
                return True
        except Exception as e:
            logger.error("Erreur pause globale: %s", e)
        return False

    # ========================================================================
    # Token (compatibilité - géré par le bridge)
    # ========================================================================

    def get_token(self) -> Optional[str]:
        """Récupérer le token d'authentification.

        Note: Le token est maintenant géré par le bridge Node.js.
        """
        return self._token

    def save_token(self, filepath: str):
        """Sauvegarder le token (compatibilité).

        Note: Le token est maintenant géré par le bridge Node.js.
        """
        logger.debug("save_token() appelé - le token est géré par le bridge Node.js")

    # ========================================================================
    # Search (compatibilité)
    # ========================================================================

    def search_track(
        self,
        artist: str,
        album: str,
        track_title: str,
        zone_id: str = None,
    ) -> Optional[Dict]:
        """Chercher un track dans Roon (via browse API du bridge).

        Args:
            artist: Nom de l'artiste
            album: Titre de l'album
            track_title: Titre du morceau
            zone_id: ID de la zone (optionnel)

        Returns:
            Dictionnaire avec les infos du track trouvé, ou None
        """
        try:
            primary_artist = artist.split(",")[0].strip() if artist else "Unknown"
            path = ["Library", "Artists", primary_artist]
            if album:
                path.append(album)
            path.append(track_title)

            resp = httpx.post(
                f"{self.bridge_url}/browse",
                json={
                    "zone_or_output_id": zone_id,
                    "path": path,
                },
                timeout=PLAY_TIMEOUT,
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return {
                        "path": path,
                        "display_name": track_title,
                        "artist": primary_artist,
                        "album": album,
                        "duration_seconds": None,
                    }

        except Exception as e:
            logger.error("Erreur recherche track: %s", e)
        return None

    def get_track_duration(self, zone_id: str) -> Optional[int]:
        """Récupérer la durée du track en cours de lecture.

        Args:
            zone_id: ID de la zone

        Returns:
            Durée en secondes, ou None
        """
        np = self.get_now_playing()
        if np:
            return np.get("duration_seconds")
        return None
