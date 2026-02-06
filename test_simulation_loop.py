#!/usr/bin/env python3
"""
Test de simulation double pour vérifier qu'il n'y a pas de boucle infinie.
Simule ce que le frontend ferait:
1. Appel POST /services/roon/normalize/simulate?limit=10
2. Polling GET /services/roon/normalize/simulate-results jusqu'à status='completed'
3. Répétition pour le 2e test
"""
import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_simulation(test_num: int, limit: int = 10):
    """Faire un test de simulation et attendre la complétion."""
    print(f"\n{'='*60}")
    print(f"🚀 TEST {test_num}: Lancement simulation (limit={limit})...")
    print(f"{'='*60}")
    
    # Lancer la simulation
    try:
        response = requests.post(
            f"{BASE_URL}/services/roon/normalize/simulate",
            params={"limit": limit},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        print(f"✓ Simulation lancée: {data.get('message')}")
    except Exception as e:
        print(f"❌ Erreur au lancement: {e}")
        return False
    
    # Polling pour attendre la complétion
    print(f"⏳ En attente de résultats...")
    start_time = time.time()
    max_wait = 30  # Timeout de 30 secondes
    poll_interval = 0.5  # Vérifier chaque 500ms
    polls = 0
    last_status = None
    
    while time.time() - start_time < max_wait:
        try:
            polls += 1
            response = requests.get(
                f"{BASE_URL}/services/roon/normalize/simulate-results",
                timeout=5
            )
            response.raise_for_status()
            results = response.json()
            status = results.get("status")
            
            # Afficher le statut s'il a changé
            if status != last_status:
                elapsed = time.time() - start_time
                print(f"  [{elapsed:.1f}s] Status: {status}")
                last_status = status
            
            # Vérifier si c'est terminé
            if status == "completed":
                elapsed = time.time() - start_time
                stats = results.get("stats", {})
                changes = results.get("changes", {})
                print(f"✅ COMPLÉTÉ en {elapsed:.2f}s après {polls} polls")
                print(f"   Artists: {stats.get('artists_total', 0)} total, {stats.get('artists_would_update', 0)} à mettre à jour")
                print(f"   Albums: {stats.get('albums_total', 0)} total, {stats.get('albums_would_update', 0)} à mettre à jour")
                print(f"   Changements artistes: {len(changes.get('artists', []))}")
                print(f"   Changements albums: {len(changes.get('albums', []))}")
                return True
            
            elif status == "error":
                elapsed = time.time() - start_time
                print(f"❌ ERREUR en {elapsed:.2f}s: {results.get('error')}")
                return False
            
            # Attendre avant le prochain poll
            time.sleep(poll_interval)
            
        except Exception as e:
            print(f"  Erreur polling: {e}")
            time.sleep(poll_interval)
            continue
    
    # Timeout atteint
    elapsed = time.time() - start_time
    print(f"❌ TIMEOUT après {elapsed:.2f}s et {polls} polls (status={last_status})")
    print(f"⚠️  Le 2ème test bouclerait probablement - IL Y A UN PROBLÈME!")
    return False

def main():
    """Exécuter les tests."""
    print("\n" + "="*60)
    print("TEST DE SIMULATION DOUBLE - Vérification boucle infinie")
    print("="*60)
    
    # Test 1
    success1 = test_simulation(1, limit=10)
    
    if not success1:
        print("\n❌ Le premier test a échoué, arrêt.")
        sys.exit(1)
    
    # Pause entre les deux
    print("\n⏸️  Pause de 2 secondes avant le 2e test...")
    time.sleep(2)
    
    # Test 2
    success2 = test_simulation(2, limit=10)
    
    print("\n" + "="*60)
    if success1 and success2:
        print("✅ SUCCÈS: Les deux tests ont complété sans boucle!")
        print("="*60)
        sys.exit(0)
    else:
        print("❌ ÉCHEC: Au moins un test a échoué")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()
