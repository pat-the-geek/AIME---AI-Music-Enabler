#!/usr/bin/env python3
"""Script pour enrichir uniquement les URLs Spotify des albums."""

import requests
import sys
import time

API_BASE = "http://localhost:8000/api/v1"


def get_albums_stats():
    """Récupérer les statistiques des albums."""
    try:
        # On fait un appel pour obtenir le nombre total
        response = requests.get(f"{API_BASE}/collection/albums?page=1&page_size=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('total', 0)
        return None
    except Exception as e:
        print(f"⚠️ Erreur: {e}")
        return None


def enrich_spotify_batch(batch_size=20):
    """Enrichir un lot d'URLs Spotify."""
    try:
        response = requests.post(
            f"{API_BASE}/services/spotify/enrich-all?limit={batch_size}", 
            timeout=300
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erreur {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ⚠️ Erreur batch: {e}")
        return None


def enrich_all_spotify(batch_size=20, pause_between_batches=1, max_batches=None):
    """
    Enrichir toutes les URLs Spotify manquantes.
    
    Args:
        batch_size: Nombre d'albums par lot (défaut: 20)
        pause_between_batches: Pause en secondes entre les lots (défaut: 1)
        max_batches: Nombre maximum de lots (None = illimité)
    """
    print("=" * 60)
    print("🎵 ENRICHISSEMENT SPOTIFY")
    print("=" * 60)
    
    # Récupérer stats
    total_albums = get_albums_stats()
    if total_albums:
        print(f"\n📊 Total albums dans la base: {total_albums}")
    
    print(f"\n📦 Traitement par lots de {batch_size} albums")
    print(f"⏸️  Pause de {pause_between_batches}s entre les lots")
    if max_batches:
        print(f"🔢 Maximum {max_batches} lots")
    else:
        print(f"♾️  Sans limite de lots (tous les albums)")
    print()
    
    # Statistiques globales
    total_spotify = 0
    total_errors = 0
    batch_number = 0
    
    print("Démarrage de l'enrichissement Spotify...\n")
    
    while True:
        # Vérifier si on a atteint le maximum de lots
        if max_batches and batch_number >= max_batches:
            print(f"\n⏹️  Maximum de {max_batches} lots atteint")
            break
        
        batch_number += 1
        print(f"📦 Lot #{batch_number}")
        
        # Enrichir le lot
        result = enrich_spotify_batch(batch_size)
        
        if result is None:
            print("   ❌ Échec du lot - arrêt")
            break
        
        # Mettre à jour les statistiques
        albums_processed = result.get('albums_processed', 0)
        spotify_added = result.get('spotify_added', 0)
        errors = result.get('errors', 0)
        
        total_spotify += spotify_added
        total_errors += errors
        
        print(f"   ✅ {albums_processed} albums traités")
        print(f"   🎵 {spotify_added} Spotify ajoutés | ❌ {errors} erreurs")
        
        # Si aucun album n'a été traité, on a terminé
        if albums_processed == 0:
            print("\n🎉 Tous les albums ont leurs URLs Spotify!")
            break
        
        # Pause entre les lots
        if albums_processed == batch_size:
            print(f"   💤 Pause de {pause_between_batches}s...")
            time.sleep(pause_between_batches)
            print()
        else:
            # Dernier lot partiel
            print("\n✨ Enrichissement Spotify terminé (dernier lot)")
            break
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS FINAUX")
    print("=" * 60)
    print(f"🎵 Spotify URLs ajoutées: {total_spotify}")
    print(f"❌ Erreurs totales: {total_errors}")
    print(f"📦 Lots traités: {batch_number}")
    print("=" * 60)
    
    return total_errors == 0


if __name__ == "__main__":
    # Arguments: [batch_size] [pause_seconds] [max_batches]
    # Exemples:
    #   python enrich_spotify.py              -> lots de 20, pause 1s, max 5 lots
    #   python enrich_spotify.py 50           -> lots de 50, pause 1s, max 5 lots
    #   python enrich_spotify.py 50 2         -> lots de 50, pause 2s, max 5 lots
    #   python enrich_spotify.py 50 2 0       -> lots de 50, pause 2s, TOUS les albums
    
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    pause_seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    max_batches = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    # Si max_batches = 0, on met None (illimité)
    if max_batches == 0:
        max_batches = None
    
    success = enrich_all_spotify(batch_size, pause_seconds, max_batches)
    sys.exit(0 if success else 1)
