#!/usr/bin/env python3
"""Test: Vérifier que les albums skipped n'appellent pas release()."""

import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.config import get_settings
from app.services.discogs_service import DiscogsService

print("🔧 Test: Skip IDs ne doivent pas appeler self.client.release()")
print("=" * 70)

settings = get_settings()
discogs_config = settings.secrets.get('discogs', {})

# Compter les appels API
api_call_count = 0

def mock_release(release_id):
    """Mock de release qui compte les appels."""
    global api_call_count
    api_call_count += 1
    
    return MagicMock(
        id=release_id,
        artists=[MagicMock(name=f'Artist {release_id}')],
        title=f'Album {release_id}',
        year=2020,
        images=[MagicMock(uri='http://example.com/image.jpg')],
        formats=[MagicMock(name='Vinyl')],
        genres=['Rock'],
        url='http://example.com'
    )

# Initialiser et patcher
discogs_service = DiscogsService(
    api_key=discogs_config.get('api_key'),
    username=discogs_config.get('username')
)

# Créer des IDs fictifs à skipper
skip_ids = {str(i) for i in range(1000001, 1000051)}  # 50 IDs fictifs

print(f"📊 Configuration:")
print(f"   ✓ Skip IDs: {len(skip_ids)} (1000001-1000050)")
print(f"   ✓ Limite: 10 albums max")
print()

# Patch pour compter les appels
with patch.object(discogs_service.client, 'release', side_effect=mock_release):
    print(f"⏱️  Exécution avec skip_ids...")
    start = time.time()
    api_call_count = 0
    
    # Cette requête devrait faire 0 appels API si le skip fonctionne
    # car tous les IDs seront skipped
    albums = discogs_service.get_collection(limit=10, skip_ids=skip_ids)
    
    elapsed = time.time() - start

print()
print(f"✅ RÉSULTATS:")
print(f"   ⏱️  Temps total: {elapsed:.2f}s")
print(f"   📍 Albums trouvés: {len(albums)}")
print(f"   🔗 Appels API release(): {api_call_count}")
print()

if api_call_count < 10:
    print(f"   ✅ EFFICACE: Seulement {api_call_count} appels API (attendu: <10)")
else:
    print(f"   ⚠️  INEFFICACE: {api_call_count} appels API (trop)")

if elapsed < 30:
    print(f"   ✅ RAPIDE: {elapsed:.2f}s < 30s")
else:
    print(f"   ⚠️  LENT: {elapsed:.2f}s > 30s")
