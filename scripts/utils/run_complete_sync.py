#!/usr/bin/env python3
"""Orchestration complète: 4-step Discogs Sync + Phase 4 Enrichment."""
import subprocess
import time
from pathlib import Path

print("\n" + "=" * 90)
print("🎵 PROCESSUS COMPLET DISCOGS - 4-STEP + PHASE 4 ENRICHMENT")
print("=" * 90)

scripts = [
    ("Step 1", "step1_fetch_discogs.py", "Fetch from Discogs API"),
    ("Step 2", "step2_enrich_data.py", "Enrich local data"),
    ("Step 3", "step3_import_db.py", "Import to database"),
    ("Step 4", "refresh_complete.py", "Refresh + Enrich (Euria + Artist Images)"),
]

timing = {}
total_start = time.time()

for step_num, script, description in scripts:
    script_path = Path(script)
    
    if not script_path.exists():
        print(f"\n⚠️  {step_num}: {script} not found, skipping...")
        continue
    
    print(f"\n{'=' * 90}")
    print(f"▶️  {step_num}: {description}")
    print(f"    Exécution: python3 {script}")
    print("─" * 90)
    
    step_start = time.time()
    
    try:
        result = subprocess.run(
            ["python3", script],
            capture_output=False,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        elapsed = time.time() - step_start
        timing[step_num] = elapsed
        
        if result.returncode == 0:
            print(f"✅ {step_num} complété en {elapsed:.1f}s")
        else:
            print(f"❌ {step_num} échoué avec code {result.returncode}")
            
    except subprocess.TimeoutExpired:
        print(f"❌ {step_num} timeout après 10 minutes")
        timing[step_num] = 600
    except Exception as e:
        print(f"❌ {step_num} erreur: {e}")

# Résumé final
print(f"\n{'=' * 90}")
print("✅ PROCESSUS COMPLET TERMINÉ")
print("=" * 90)

total_elapsed = time.time() - total_start

print(f"\n📊 TIMING DÉTAILLÉ:")
for step, duration in timing.items():
    percent = int(duration / total_elapsed * 100) if total_elapsed > 0 else 0
    bar_length = 30
    filled = int(bar_length * duration / total_elapsed) if total_elapsed > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"  {step:<12} [{bar}] {duration:>7.1f}s ({percent:>3}%)")

print(f"\n⏱️  TEMPS TOTAL: {total_elapsed:.1f} secondes ({total_elapsed/60:.1f} minutes)")

if total_elapsed <= 300:
    print(f"   ✅ Objectif <5 minutes ATTEINT!")
else:
    print(f"   ⚠️  Dépasse l'objectif de 5 minutes par {total_elapsed-300:.0f}s")

print("\n" + "=" * 90)
print("📖 Prochaines étapes:")
print("   1. Éditez data/euria_descriptions.json pour ajouter descriptions")
print("   2. Éditez data/artist_images.json pour ajouter images artiste")
print("   3. Relancez: python3 refresh_complete.py")
print("   4. Vérifiez: python3 verify_enrichment.py")
print("=" * 90 + "\n")
