#!/usr/bin/env python3
"""Orchestrateur: exécute les 4 étapes avec suivi global."""
import subprocess
import sys
import time
from datetime import datetime

print("\n" + "=" * 80)
print("🚀 SYNCHRONISATION DISCOGS - MODE 4 ÉTAPES")
print("=" * 80)
print(f"⏱️ Démarrage: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 80 + "\n")

overall_start = time.time()
steps = [
    ("étape 1 (Récupération)", "step1_fetch_discogs.py"),
    ("étape 2 (Enrichissement)", "step2_enrich_data.py"),
    ("étape 3 (Import BD)", "step3_import_db.py"),
    ("étape 4 (Rafraîchissement)", "step4_refresh_albums.py"),
]

failed_steps = []

for step_name, script_file in steps:
    print(f"\n▶️ Exécution {step_name} ({script_file})...")
    print("─" * 80)
    
    step_start = time.time()
    try:
        result = subprocess.run([sys.executable, script_file], cwd=None, check=True)
        elapsed = time.time() - step_start
        print(f"✅ {step_name} complétée en {elapsed:.1f}s")
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - step_start
        print(f"❌ {step_name} échouée après {elapsed:.1f}s")
        failed_steps.append(step_name)

overall_elapsed = time.time() - overall_start

print("\n" + "=" * 80)
print("📋 RÉSUMÉ FINAL")
print("=" * 80)
print(f"⏱️ Temps total: {overall_elapsed:.1f}s")
print(f"⏱️ Fin: {datetime.now().strftime('%H:%M:%S')}")

if failed_steps:
    print(f"\n❌ {len(failed_steps)} étape(s) échouée(s):")
    for step in failed_steps:
        print(f"   • {step}")
    sys.exit(1)
else:
    print(f"\n✅ Toutes les 4 étapes complétées avec succès!")
    
    if overall_elapsed < 600:
        print(f"✅ Synchronisation < 10 minutes")
    else:
        print(f"⚠️ Synchronisation > 10 minutes (L'étape 1 est lente due au rate-limit Discogs)")

print("=" * 80 + "\n")
