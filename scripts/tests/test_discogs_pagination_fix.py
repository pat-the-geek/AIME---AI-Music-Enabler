#!/usr/bin/env python3
"""Test de la pagination Discogs avec la nouvelle approche."""
import json
import sys
sys.path.insert(0, './backend')

from backend.app.services.discogs_service import DiscogsService

# Charger les secrets
with open('./config/secrets.json', 'r') as f:
    secrets = json.load(f)

discogs_config = secrets.get('discogs', {})

# Créer le service
service = DiscogsService(
    api_key=discogs_config.get('api_key'),
    username=discogs_config.get('username')
)

print("=" * 80)
print("🧪 Test nouvelle pagination Discogs")
print("=" * 80)

# Récupérer la collection COMPLÈTE
print("\n🔍 Récupération COMPLÈTE de la collection...")
albums_full = service.get_collection(limit=None)
print(f"\n✅ Total albums récupérés: {len(albums_full)}")

# Chercher les albums Tame Impala
tame_impala_albums = [a for a in albums_full if 'Tame Impala' in a.get('title', '') or any('Tame Impala' in str(artist) for artist in a.get('artists', []))]
print(f"\n🎵 Albums Tame Impala dans la collection: {len(tame_impala_albums)}")
for i, album in enumerate(tame_impala_albums, 1):
    print(f"  {i}. {album['title']} ({album['year']}) - Artists: {album['artists']}")

# Vérifier les premiers et derniers albums
print(f"\n📊 Premiers albums récupérés:")
for i, album in enumerate(albums_full[:3], 1):
    print(f"  {i}. {album['title']} - {album['artists']}")

print(f"\n📊 Derniers albums récupérés:")
for i, album in enumerate(albums_full[-3:], 1):
    print(f"  {i}. {album['title']} - {album['artists']}")

print("\n" + "=" * 80)
