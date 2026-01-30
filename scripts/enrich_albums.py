#!/usr/bin/env python3
"""Script pour enrichir tous les albums existants avec Spotify et IA via l'API."""

import requests
import sys
import time

API_BASE = "http://localhost:8000/api/v1"


def get_total_albums():
    """Récupérer le nombre total d'albums."""
    try:
        response = requests.get(f"{API_BASE}/collection/albums", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('total', 0)
        return 0
    except Exception as e:
        print(f"⚠️ Impossible de récupérer le total: {e}")
        return 0


def enrich_batch(batch_size=10):
    """Enrichir un lot d'albums."""
    try:
        response = requests.post(
            f"{API_BASE}/services/ai/enrich-all?limit={batch_size}", 
            timeout=600
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception as e:
        print(f"   ⚠️ Erreur batch: {e}")
        return None


def enrich_all_albums(batch_size=10, pause_between_batches=2):
    """
    Enrichir TOUS les albums par lots automatiquement.
    
    Args:
        batch_size: Nombre d'albums par lot (défaut: 10)
        pause_between_batches: Pause en secondes entre les lots (défaut: 2)
    """
    print("=" * 60)
    print("🚀 ENRICHISSEMENT COMPLET DE LA COLLECTION")
    print("=" * 60)
    
    # Obtenir le nombre total d'albums
    total_albums = get_total_albums()
    if total_albums > 0:
        print(f"\n📀 Collection: {total_albums} albums")
    
    print(f"📦 Traitement par lots de {batch_size} albums")
    print(f"⏸️  Pause de {pause_between_batches}s entre les lots")
    print(f"⏳ Cela peut prendre {int((total_albums / batch_size) * (batch_size * 3 + pause_between_batches) / 60)} à {int((total_albums / batch_size) * (batch_size * 4 + pause_between_batches) / 60)} minutes\n")
    
    # Statistiques globales
    total_spotify = 0
    total_ai = 0
    total_errors = 0
    batch_number = 0
    max_batches = (total_albums // batch_size) + 2  # +2 pour la sécurité
    
    print("Démarrage de l'enrichissement...\n")
    
    while batch_number < max_batches:
        batch_number += 1
        print(f"📦 Lot #{batch_number}/{max_batches}")
        
        # Enrichir le lot
        result = enrich_batch(batch_size)
        
        if result is None:
            print("   ❌ Échec du lot - arrêt")
            break
        
        # Mettre à jour les statistiques
        albums_processed = result.get('albums_processed', 0)
        spotify_added = result.get('spotify_added', 0)
        ai_added = result.get('ai_added', 0)
        errors = result.get('errors', 0)
        
        total_spotify += spotify_added
        total_ai += ai_added
        total_errors += errors
        
        print(f"   ✅ {albums_processed} albums traités")
        print(f"   🎵 {spotify_added} Spotify | 🤖 {ai_added} IA | ❌ {errors} erreurs")
        
        # Si aucun album n'a été traité, on a terminé
        if albums_processed == 0:
            print("\n🎉 Tous les albums sont enrichis!")
            break
        
        # Pause entre les lots pour éviter le rate limiting
        if albums_processed == batch_size:  # Il y a peut-être encore des albums
            print(f"   💤 Pause de {pause_between_batches}s...")
            time.sleep(pause_between_batches)
            print()
        else:
            # Dernier lot partiel
            print("\n✨ Enrichissement terminé (dernier lot)")
            break
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS FINAUX")
    print("=" * 60)
    print(f"🎵 Spotify URLs ajoutées: {total_spotify}")
    print(f"🤖 Descriptions IA ajoutées: {total_ai}")
    print(f"❌ Erreurs totales: {total_errors}")
    print(f"📦 Lots traités: {batch_number}")
    print("=" * 60)
    
    return total_errors == 0


if __name__ == "__main__":
    # Arguments: batch_size [pause_seconds]
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    pause_seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    
    success = enrich_all_albums(batch_size, pause_seconds)
    sys.exit(0 if success else 1)
