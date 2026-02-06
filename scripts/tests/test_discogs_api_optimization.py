#!/usr/bin/env python3
"""Test de l'optimisation API Discogs - Skip appels API pour albums existants."""

import sys
import time
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.config import get_settings
from app.services.discogs_service import DiscogsService

# Initialiser le service
print("🔧 Initialisation DiscogsService...")
settings = get_settings()
discogs_config = settings.secrets.get('discogs', {})
discogs_service = DiscogsService(
    api_key=discogs_config.get('api_key'),
    username=discogs_config.get('username')
)

# Simuler 200 IDs existants
print("\n📊 Test: Récupération collection avec 200+ IDs à skipper...")
skip_ids = {str(i) for i in range(1, 201)}  # IDs fictifs 1-200

start = time.time()
albums = discogs_service.get_collection(limit=10, skip_ids=skip_ids)
elapsed = time.time() - start

print(f"\n✅ Résultats:")
print(f"   ⏱️  Temps: {elapsed:.2f}s")
print(f"   📀 Albums retournés: {len(albums)}")
print(f"   ✨ Nouveaux albums trouvés: {len(albums)}")

if elapsed < 5:
    print(f"   ✅ OPTIMISATION EFFICACE: Moins de 5s pour récupérer ({elapsed:.2f}s)")
else:
    print(f"   ⚠️  TOUJOURS LENT: {elapsed:.2f}s")

# Afficher les IDs récupérés
if albums:
    print(f"\n📋 Premiers albums trouvés:")
    for album in albums[:3]:
        print(f"   - {album.get('title', 'Unknown')}: ID={album.get('release_id')}")
