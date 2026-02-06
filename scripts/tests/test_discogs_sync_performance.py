#!/usr/bin/env python3
"""
Test de performance: Vérifier que le sync Discogs est RAPIDE avec l'optimisation.

Exécute une vraie sync et mesure le temps vs avant (qui étaient 2-4 minutes pour 0 nouveaux albums).
"""

import requests
import time
import json
import sys
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8000"
DISCOGS_SYNC_ENDPOINT = f"{BACKEND_URL}/api/v1/services/discogs/sync"
PROGRESS_ENDPOINT = f"{BACKEND_URL}/api/v1/services/discogs/sync-progress"

print("=" * 80)
print("🚀 TEST PERFORMANCE: DISCOGS SYNC AVEC OPTIMISATION")
print("=" * 80)
print()

# Vérifier que le backend tourne
print("🔍 Vérification du backend...")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if response.status_code == 200:
        print("✅ Backend actif sur http://localhost:8000")
    else:
        print(f"⚠️  Backend retourne {response.status_code}")
except Exception as e:
    print(f"❌ Backend indisponible: {e}")
    print("   Lance le backend avec: python backend/main.py")
    sys.exit(1)

print()
print("📊 Démarrage du sync Discogs...")
print("-" * 80)

# Lancer la sync
try:
    response = requests.post(DISCOGS_SYNC_ENDPOINT, timeout=5)
    if response.status_code == 202:
        print(f"✅ Sync lancée (202 Accepted)")
    else:
        print(f"⚠️  Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Erreur lors du lancement: {e}")
    sys.exit(1)

# Monitorer la progression
print()
print("⏱️  Monitoring de la progression...")
print()

start_time = time.time()
last_status = None
check_count = 0
max_checks = 600  # 10 minutes max (60s × 10)

while check_count < max_checks:
    try:
        response = requests.get(PROGRESS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            progress = response.json()
            
            # Afficher la progression
            status = progress.get('status', 'unknown')
            current = progress.get('current', 0)
            total = progress.get('total', 0)
            synced = progress.get('synced', 0)
            skipped = progress.get('skipped', 0)
            errors = progress.get('errors', 0)
            album_name = progress.get('current_album', '')
            
            # Afficher seulement si changement
            if status != last_status or current % 10 == 0:
                elapsed = time.time() - start_time
                if total > 0:
                    pct = (current / total * 100) if total > 0 else 0
                    print(f"[{elapsed:6.1f}s] {status:10s} | {current:3d}/{total:3d} ({pct:5.1f}%) " +
                          f"| ✨{synced:3d} ⏭️ {skipped:3d} ❌{errors:1d} | {album_name[:50]}")
                else:
                    print(f"[{elapsed:6.1f}s] {status:10s} | Initialisation...")
                
                last_status = status
            
            # Vérifier si terminé
            if status in ['completed', 'error', 'failed']:
                elapsed = time.time() - start_time
                print()
                print("-" * 80)
                print(f"✅ SYNC TERMINÉE")
                print(f"   ⏱️  Temps total: {elapsed:.1f}s")
                print(f"   ✨ Albums ajoutés: {synced}")
                print(f"   ⏭️  Albums existants (skipped): {skipped}")
                print(f"   ❌ Erreurs: {errors}")
                
                # Évaluer la performance
                print()
                if elapsed < 60:
                    print(f"   🎉 EXCELLENT: Sync en {elapsed:.1f}s (attendu <60s avec optimisation)")
                elif elapsed < 120:
                    print(f"   ✅ BON: Sync en {elapsed:.1f}s (attendu <120s)")
                elif elapsed < 240:
                    print(f"   ⚠️  MOYEN: Sync en {elapsed:.1f}s (avant optimisation: 2-4 min)")
                else:
                    print(f"   ❌ LENT: Sync en {elapsed:.1f}s (problème détecté)")
                
                print("=" * 80)
                break
        else:
            print(f"⚠️  Status: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Backend déconnecté")
        break
    except Exception as e:
        print(f"⚠️  Erreur: {e}")
    
    # Attendre avant prochain check
    time.sleep(1)
    check_count += 1

if check_count >= max_checks:
    elapsed = time.time() - start_time
    print()
    print(f"❌ TIMEOUT: Sync a dépassé 10 minutes ({elapsed:.1f}s)")
    print("=" * 80)
