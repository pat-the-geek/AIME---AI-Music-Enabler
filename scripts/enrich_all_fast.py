#!/usr/bin/env python3
"""
Script d'enrichissement RAPIDE en mode batch pour premier import.
Utilise des lots plus grands avec gestion intelligente du rate limiting.
"""

import requests
import sys
import time
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"


def get_stats():
    """Récupérer les statistiques de la collection."""
    try:
        # Récupérer tous les albums (en plusieurs pages si nécessaire)
        all_albums = []
        page = 1
        page_size = 100
        
        while True:
            response = requests.get(
                f"{API_BASE}/collection/albums?page={page}&page_size={page_size}",
                timeout=10
            )
            
            if response.status_code != 200:
                break
            
            data = response.json()
            albums = data.get('items', [])
            if not albums:
                break
            
            all_albums.extend(albums)
            
            # Si on a tout récupéré, sortir
            if len(albums) < page_size:
                break
            
            page += 1
        
        return {
            'total': len(all_albums),
            'albums': all_albums
        }
    except:
        pass
    return {'total': 0, 'albums': []}


def count_enriched():
    """Compter combien d'albums ont déjà des infos IA."""
    stats = get_stats()
    enriched = sum(1 for album in stats['albums'] if album.get('ai_info'))
    return enriched, stats['total']


def enrich_batch(batch_size=15):
    """Enrichir un lot d'albums."""
    try:
        response = requests.post(
            f"{API_BASE}/services/ai/enrich-all?limit={batch_size}", 
            timeout=900  # 15 minutes max par lot
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)


def main():
    """Enrichissement complet en mode rapide."""
    
    print("\n" + "=" * 70)
    print("🚀 ENRICHISSEMENT COMPLET - MODE RAPIDE")
    print("=" * 70)
    
    # Vérifier l'état initial
    enriched, total = count_enriched()
    remaining = total - enriched
    
    print(f"\n📊 État actuel:")
    print(f"   • Total albums: {total}")
    print(f"   • Déjà enrichis: {enriched}")
    print(f"   • Restants: {remaining}")
    
    if remaining == 0:
        print("\n✨ Tous les albums sont déjà enrichis!")
        return True
    
    # Configuration
    batch_size = 15  # Lots de 15 albums
    initial_pause = 1.5  # Pause initiale entre lots
    max_pause = 10  # Pause max en cas d'erreurs répétées
    
    print(f"\n⚙️  Configuration:")
    print(f"   • Taille des lots: {batch_size} albums")
    print(f"   • Pause initiale: {initial_pause}s")
    print(f"   • Temps estimé: ~{int(remaining * 3.5 / 60)} minutes")
    
    input("\n▶️  Appuyez sur ENTRÉE pour démarrer...")
    
    # Statistiques
    start_time = time.time()
    total_spotify = 0
    total_ai = 0
    total_errors = 0
    batch_number = 0
    consecutive_errors = 0
    current_pause = initial_pause
    
    print("\n" + "-" * 70)
    
    while remaining > 0:
        batch_number += 1
        batch_start = time.time()
        
        # Affichage de la progression
        progress = int((enriched / total) * 100) if total > 0 else 0
        bar_length = 40
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\n📦 Lot {batch_number} | [{bar}] {progress}%")
        print(f"   Restants: {remaining}/{total}")
        
        # Enrichir le lot
        result, error = enrich_batch(batch_size)
        batch_duration = time.time() - batch_start
        
        if result is None:
            consecutive_errors += 1
            current_pause = min(current_pause * 1.5, max_pause)
            print(f"   ❌ Erreur: {error}")
            print(f"   ⏸️  Pause augmentée à {current_pause:.1f}s")
            
            if consecutive_errors >= 3:
                print("\n⚠️  Trop d'erreurs consécutives - arrêt")
                break
            
            time.sleep(current_pause)
            continue
        
        # Réinitialiser le compteur d'erreurs
        if consecutive_errors > 0:
            consecutive_errors = 0
            current_pause = initial_pause
        
        # Mettre à jour les statistiques
        processed = result.get('albums_processed', 0)
        spotify_added = result.get('spotify_added', 0)
        ai_added = result.get('ai_added', 0)
        errors = result.get('errors', 0)
        
        total_spotify += spotify_added
        total_ai += ai_added
        total_errors += errors
        
        print(f"   ✅ {processed} traités en {batch_duration:.1f}s")
        print(f"   🎵 {spotify_added} Spotify | 🤖 {ai_added} IA | ❌ {errors} err")
        
        # Mettre à jour les compteurs
        enriched += ai_added
        remaining = total - enriched
        
        # Si aucun album traité, on a terminé
        if processed == 0:
            print("\n✨ Tous les albums sont enrichis!")
            break
        
        # Pause adaptative
        if processed == batch_size and remaining > 0:
            print(f"   💤 Pause {current_pause:.1f}s...")
            time.sleep(current_pause)
    
    # Résumé final
    duration = time.time() - start_time
    minutes = int(duration / 60)
    seconds = int(duration % 60)
    
    print("\n" + "=" * 70)
    print("📊 RÉSULTATS FINAUX")
    print("=" * 70)
    print(f"⏱️  Durée totale: {minutes}m {seconds}s")
    print(f"🎵 Spotify URLs: {total_spotify}")
    print(f"🤖 Descriptions IA: {total_ai}")
    print(f"❌ Erreurs: {total_errors}")
    print(f"📦 Lots traités: {batch_number}")
    
    # Vérification finale
    enriched_final, total_final = count_enriched()
    coverage = int((enriched_final / total_final) * 100) if total_final > 0 else 0
    print(f"📈 Couverture: {enriched_final}/{total_final} ({coverage}%)")
    print("=" * 70 + "\n")
    
    return total_errors == 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur - enrichissement arrêté")
        print("💡 Relancez le script pour continuer où vous vous êtes arrêté\n")
        sys.exit(1)
