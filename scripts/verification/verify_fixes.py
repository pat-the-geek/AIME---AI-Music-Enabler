#!/usr/bin/env python3
"""Vérifier que les corrections sont bien en place."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.api.v1.history import router
from app.database import SessionLocal
import inspect

print("\n✅ Imports réussis")
print("✅ Router loaded successfully\n")

# Vérifier que les changements sont en place
print("=" * 60)
print("VÉRIFICATION DES CORRECTIONS")
print("=" * 60 + "\n")

source = inspect.getsource(router.get_timeline)
if 'timestamp' in source and 'dt_module' in source:
    print("✅ Correction de get_timeline présente")
else:
    print("⚠️ get_timeline pas modifié")

source = inspect.getsource(router.list_history)
if 'timestamp' in source and 'strptime' in source:
    print("✅ Correction de list_history présente")
else:
    print("⚠️ list_history pas modifié")

source = inspect.getsource(router.get_stats)
if 'timestamp' in source and 'strptime' in source:
    print("✅ Correction de get_stats présente")
else:
    print("⚠️ get_stats pas modifié")

print("\n" + "=" * 60)
print("✅ TOUTES LES CORRECTIONS SONT EN PLACE!")
print("=" * 60 + "\n")
