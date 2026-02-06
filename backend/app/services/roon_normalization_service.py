"""Service de normalisation des noms d'artiste et d'album avec RÈGLES LOCALES.

Ce service applique des règles de normalisation directement sur la base de données
sans accès API Roon pour garantir un traitement rapide (< 10 secondes pour 200 items).
"""
import logging
import time
import copy
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from app.models import Artist, Album
from app.database import SessionLocal
from datetime import datetime

logger = logging.getLogger(__name__)

# Global state pour tracker la progression
_normalization_progress = {
    "status": "idle",  # idle, simulating, normalizing, completed, error
    "phase": "",  # "" , "artists", "albums"
    "current_item": 0,
    "total_items": 0,
    "current_item_name": "",
    "artists_updated": 0,
    "albums_updated": 0,
    "matches_found": [],
    "no_matches": [],
    "errors": [],
    "start_time": None,
    "elapsed_seconds": 0,
    "estimated_remaining": 0
}

# Global state pour les résultats de simulation
_simulation_results = {
    "status": "idle",  # idle, simulating, completed, error
    "changes": {
        "artists": [],
        "albums": []
    },
    "stats": {
        "artists_total": 0,
        "artists_would_update": 0,
        "albums_total": 0,
        "albums_would_update": 0,
        "no_matches": 0
    },
    "error": None
}

def get_normalization_progress() -> Dict:
    """Récupérer l'état actuel de la progression."""
    progress = _normalization_progress.copy()
    
    # Calculer le temps écoulé
    if progress["start_time"]:
        elapsed = time.time() - progress["start_time"]
        progress["elapsed_seconds"] = int(elapsed)
        
        # Estimer le temps restant
        if progress["current_item"] > 0 and progress["total_items"] > 0:
            avg_time_per_item = elapsed / progress["current_item"]
            remaining_items = progress["total_items"] - progress["current_item"]
            progress["estimated_remaining"] = int(avg_time_per_item * remaining_items)
    
    # Calculer le pourcentage
    if progress["total_items"] > 0:
        progress["percent"] = int((progress["current_item"] / progress["total_items"]) * 100)
    else:
        progress["percent"] = 0
    
    return progress

def reset_normalization_progress():
    """Réinitialiser l'état de progression."""
    global _normalization_progress
    _normalization_progress = {
        "status": "idle",
        "phase": "",
        "current_item": 0,
        "total_items": 0,
        "current_item_name": "",
        "artists_updated": 0,
        "albums_updated": 0,
        "matches_found": [],
        "no_matches": [],
        "errors": [],
        "start_time": None,
        "elapsed_seconds": 0,
        "estimated_remaining": 0
    }

def update_normalization_progress(**kwargs):
    """Mettre à jour l'état de progression."""
    global _normalization_progress
    _normalization_progress.update(kwargs)


def get_simulation_results() -> Dict:
    """Récupérer les résultats de la simulation (deep copy pour éviter les mutations)."""
    return copy.deepcopy(_simulation_results)


def reset_simulation_results():
    """Réinitialiser les résultats de simulation."""
    global _simulation_results
    _simulation_results = {
        "status": "idle",
        "changes": {
            "artists": [],
            "albums": []
        },
        "stats": {
            "artists_total": 0,
            "artists_would_update": 0,
            "albums_total": 0,
            "albums_would_update": 0,
            "no_matches": 0
        },
        "error": None
    }


def update_simulation_results(**kwargs):
    """Mettre à jour les résultats de simulation."""
    global _simulation_results
    _simulation_results.update(kwargs)


class RoonNormalizationService:
    """Service pour normaliser les noms avec règles locales (pas d'API Roon)."""
    
    # Dictionnaire de diacritiques - créé UNE SEULE FOIS au démarrage
    DIACRITICS = {
        'à': 'a', 'á': 'a', 'â': 'a', 'ä': 'a', 'ã': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'ö': 'o', 'õ': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
    }

    def __init__(self, bridge_url: str = "http://localhost:3330"):
        """Initialiser le service de normalisation.
        
        Note: bridge_url est ignoré - on applique des règles locales uniquement
        """
        # Règles courantes de variantes pour normaliser
        self.artist_variants = {
            ' feat. ': ' & ',
            ' feat ': ' & ',
            ' ft. ': ' & ',
            ' ft ': ' & ',
            ' featuring ': ' & ',
            'and': '&',
        }
        
        self.album_variants = {
            '(\w+\s+remix)': '',  # Supprimer les remixes parenthésés
            '(\w+\s+version)': '',  # Supprimer les versions
        }

    def is_connected(self) -> bool:
        """Toujours retourner True - pas de dépendance API."""
        logger.info("✓ Mode normalisation locale (pas de dépendance API)")
        return True

    def _normalize_name(self, name: str) -> str:
        """Normaliser un nom pour la comparaison.
        
        - Convertir en minuscules
        - Supprimer les espaces supplémentaires
        - Supprimer les accents
        """
        if not name:
            return ""
        
        # Minuscules
        name = name.lower().strip()
        
        # Supprimer les espaces multiples
        while "  " in name:
            name = name.replace("  ", " ")
        
        # Supprimer les diacritiques (utiliser classe variable, pas créer dict à chaque fois!)
        for old, new in self.DIACRITICS.items():
            name = name.replace(old, new)
        
        return name

    def _apply_corrections(self, name: str) -> str:
        """Appliquer une normalisation complète sur un nom.
        
        - Capitaliser correctement (Title Case)
        - Corriger les espaces autour de &
        - Normaliser les diacritiques (preserve mais correct)
        - Supprimer les espaces extras
        """
        if not name:
            return name
        
        # D'abord, normaliser les espaces
        name = name.replace(' & ', ' & ').replace('&', ' & ')
        while '  ' in name:
            name = name.replace('  ', ' ')
        name = name.strip()
        
        # Appliquer Title Case intelligent
        words = name.split()
        corrected = []
        
        for i, word in enumerate(words):
            # Garder certains mots en minuscules (sauf au début)
            if i > 0 and word.lower() in ('the', 'a', 'an', 'and', 'or', 'of', 'de', 'du', 'la', 'le', 'les', 'et'):
                corrected.append(word.lower())
            elif word in ('&',):
                corrected.append(word)
            else:
                # Title case: première lettre majuscule, reste minuscules
                # Cela préserve les accents mais applique la bonne casse
                if word:
                    corrected.append(word[0].upper() + word[1:].lower())
                else:
                    corrected.append(word)
        
        result = ' '.join(corrected)
        return result.strip()


    def _find_correction_candidate(self, name: str, normalized_map: Dict[str, str], threshold: float = 0.8) -> Optional[str]:
        """Trouver un nom similaire existant dans la liste.
        
        Optimisé: Utilise un dictionnaire {normalized: original} pour O(1) lookup
        au lieu de O(n) loop sur tous les noms.
        """
        if not name or not normalized_map:
            return None
            
        normalized_name = self._normalize_name(name)
        
        # Lookup O(1) dans le dictionnaire
        if normalized_name in normalized_map:
            original = normalized_map[normalized_name]
            if original != name:
                return original
        
        # No match found
        return None

    def normalize_with_roon(self, db: Session) -> Dict[str, any]:
        """Normaliser tous les noms de la BD avec règles locales.
        
        Applique des règles de normalisation intelligentes et compare avec
        les noms existants - sans access API pour une exécution ultra-rapide!
        """
        try:
            logger.info("\n" + "=" * 60)
            logger.info("NORMALISATION LOCALE ⚡ (Sans API Roon)")
            logger.info("=" * 60)
            
            reset_normalization_progress()
            
            stats = {
                "artists_total": 0,
                "artists_updated": 0,
                "albums_total": 0,
                "albums_updated": 0,
                "no_matches": [],
                "matches_found": [],
            }
            
            # Charger TOUS les artistes une fois
            local_artists = db.query(Artist).all()
            stats["artists_total"] = len(local_artists)
            
            logger.info(f"\n📍 Phase 1: Normalisation des ARTISTES ({len(local_artists)} items)")
            logger.info("-" * 60)
            
            # Construire dictionnaire {normalized: original} pour O(1) lookup
            artist_normalized_map = {
                self._normalize_name(a.name): a.name 
                for a in local_artists
            }
            
            update_normalization_progress(
                status="normalizing",
                phase="artists",
                total_items=len(local_artists)
            )

            for idx, local_artist in enumerate(local_artists):
                update_normalization_progress(
                    current_item=idx + 1,
                    current_item_name=local_artist.name
                )
                
                # Appliquer directement la normalisation canonique
                canonical_form = self._apply_corrections(local_artist.name)

                if canonical_form != local_artist.name:
                    old_name = local_artist.name
                    
                    # CRITIQUE: Vérifier si mettre à jour créerait un doublon
                    # (même nom exactement pour un artiste différent)
                    existing_with_new_name = db.query(Artist).filter(
                        Artist.name == canonical_form,
                        Artist.id != local_artist.id
                    ).first()
                    
                    if existing_with_new_name:
                        # Doublon détecté - n'appliquer que si l'existant est vraiment identique  
                        # sinon c'est une vraie fusion qui sera loggée
                        logger.info(f"  ⊘ [{idx+1}/{len(local_artists)}] '{old_name}' → '{canonical_form}' [DOUBLE: existe id={existing_with_new_name.id}]")
                        continue
                    
                    local_artist.name = canonical_form
                    db.add(local_artist)
                    
                    stats["artists_updated"] += 1
                    logger.info(f"  ✓ [{idx+1}/{len(local_artists)}] '{old_name}' → '{canonical_form}'")
                    update_normalization_progress(artists_updated=stats["artists_updated"])
                    
                    logger.info(f"  ✓ [{idx+1}/{len(local_artists)}] '{old_name}' → '{local_artist.name}'")

            # ========== ALBUMS ==========
            logger.info(f"\n📍 Phase 2: Normalisation des ALBUMS")
            logger.info("-" * 60)
            
            local_albums = db.query(Album).all()
            stats["albums_total"] = len(local_albums)
            
            # Construire dictionnaire {normalized: original} pour O(1) lookup
            album_normalized_map = {
                self._normalize_name(a.title): a.title 
                for a in local_albums
            }
            
            update_normalization_progress(
                phase="albums",
                total_items=len(local_albums),
                current_item=0
            )

            for idx, local_album in enumerate(local_albums):
                update_normalization_progress(
                    current_item=idx + 1,
                    current_item_name=local_album.title
                )
                
                # Appliquer directement la normalisation canonique
                canonical_title = self._apply_corrections(local_album.title)

                if canonical_title != local_album.title:
                    old_title = local_album.title
                    
                    # CRITIQUE: Vérifier si mettre à jour créerait un doublon
                    existing_with_new_title = db.query(Album).filter(
                        Album.title == canonical_title,
                        Album.id != local_album.id
                    ).first()
                    
                    if existing_with_new_title:
                        # Doublon détecté
                        logger.info(f"  ⊘ [{idx+1}/{len(local_albums)}] '{old_title}' → '{canonical_title}' [DOUBLE: existe id={existing_with_new_title.id}]")
                        continue
                    
                    local_album.title = canonical_title
                    db.add(local_album)
                    
                    stats["albums_updated"] += 1
                    
                    match_info = {
                        "type": "album",
                        "local": old_title,
                        "normalized": local_album.title,
                        "artist": local_album.artists[0].name if local_album.artists else "Unknown"
                    }
                    stats["matches_found"].append(match_info)
                    logger.info(f"  ✓ [{idx+1}/{len(local_albums)}] '{old_title}' → '{canonical_title}'")
                    update_normalization_progress(albums_updated=stats["albums_updated"])

            # Valider les changements
            logger.info(f"📝 Avant commit: artists_updated={stats['artists_updated']}, albums_updated={stats['albums_updated']}")
            db.commit()
            logger.info(f"✓ Commit réussi - changements sauvegardés en DB")
            
            update_normalization_progress(status="completed")
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ NORMALISATION TERMINÉE")
            logger.info("=" * 60)
            logger.info(f"Artistes normalisés: {stats['artists_updated']}/{stats['artists_total']}")
            logger.info(f"Albums normalisés: {stats['albums_updated']}/{stats['albums_total']}")
            
            return stats

        except Exception as e:
            logger.error(f"Erreur normalisation: {e}", exc_info=True)
            update_normalization_progress(status="idle")
            raise

    def simulate_normalization(self, db: Session, limit: int = None) -> Dict[str, any]:
        """Simuler la normalisation sans apporter de changements.
        
        Utilise les règles locales pour ultra-rapidité!
        
        Args:
            db: Session SQLAlchemy
            limit: Limiter à N artistes et N albums pour un test rapide (None = tous)
            
        Returns:
            Dictionnaire avec les changements qui seraient effectués
        """
        changes = {
            "artists": [],
            "albums": [],
            "stats": {
                "artists_total": 0,
                "artists_would_update": 0,
                "albums_total": 0,
                "albums_would_update": 0,
                "no_matches": 0
            }
        }

        try:
            logger.info("🔍 Simulation de normalisation LOCALE ⚡...")
            
            reset_normalization_progress()
            
            # ARTISTES
            local_artists = db.query(Artist).all()
            if limit:
                local_artists = local_artists[:limit]
                logger.info(f"🔬 Mode TEST: Limitation à {limit} artistes")
            
            changes["stats"]["artists_total"] = len(local_artists)
            # Construire dictionnaire {normalized: original} pour O(1) lookup
            artist_normalized_map = {
                self._normalize_name(a.name): a.name 
                for a in local_artists
            }
            
            update_normalization_progress(
                status="simulating",
                phase="artists",
                total_items=len(local_artists)
            )

            for idx, local_artist in enumerate(local_artists):
                update_normalization_progress(
                    current_item=idx + 1,
                    current_item_name=local_artist.name
                )
                
                # Appliquer directement la normalisation canonique
                canonical_form = self._apply_corrections(local_artist.name)

                if canonical_form != local_artist.name:
                    # Vérifier si mettre à jour créerait un doublon
                    existing_with_new_name = db.query(Artist).filter(
                        Artist.name == canonical_form,
                        Artist.id != local_artist.id
                    ).first()
                    
                    if not existing_with_new_name:
                        # Pas de doublon, ajouter aux changements prévus
                        changes["artists"].append({
                            "local_name": local_artist.name,
                            "roon_name": canonical_form
                        })
                        changes["stats"]["artists_would_update"] += 1
                        update_normalization_progress(artists_updated=changes["stats"]["artists_would_update"])
                    else:
                        changes["stats"]["no_matches"] += 1
                else:
                    changes["stats"]["no_matches"] += 1

            # ALBUMS
            local_albums = db.query(Album).all()
            if limit:
                local_albums = local_albums[:limit]
                logger.info(f"🔬 Mode TEST: Limitation à {limit} albums")
            
            changes["stats"]["albums_total"] = len(local_albums)
            # Construire dictionnaire {normalized: original} pour O(1) lookup
            album_normalized_map = {
                self._normalize_name(a.title): a.title 
                for a in local_albums
            }
            
            update_normalization_progress(
                phase="albums",
                total_items=len(local_albums),
                current_item=0
            )

            for idx, local_album in enumerate(local_albums):
                update_normalization_progress(
                    current_item=idx + 1,
                    current_item_name=local_album.title
                )
                
                # Appliquer directement la normalisation canonique
                canonical_title = self._apply_corrections(local_album.title)

                if canonical_title != local_album.title:
                    # Vérifier si mettre à jour créerait un doublon
                    existing_with_new_title = db.query(Album).filter(
                        Album.title == canonical_title,
                        Album.id != local_album.id
                    ).first()
                    
                    if not existing_with_new_title:
                        # Pas de doublon, ajouter aux changements prévus
                        changes["albums"].append({
                            "local_name": local_album.title,
                            "roon_name": canonical_title,
                            "artist": local_album.artists[0].name if local_album.artists else "Unknown"
                        })
                        changes["stats"]["albums_would_update"] += 1
                        update_normalization_progress(albums_updated=changes["stats"]["albums_would_update"])
                    else:
                        changes["stats"]["no_matches"] += 1
                else:
                    changes["stats"]["no_matches"] += 1

            logger.info(f"✅ Simulation terminée ⚡")
            update_normalization_progress(status="idle")
            
            update_simulation_results(
                status="completed",
                changes=changes,
                stats=changes["stats"],
                error=None
            )
            
            return changes

        except Exception as e:
            logger.error(f"Erreur simulation normalisation: {e}", exc_info=True)
            update_normalization_progress(status="idle")
            update_simulation_results(
                status="error",
                error=str(e)
            )
            update_simulation_results(
                status="error",
                error=str(e)
            )
            raise

