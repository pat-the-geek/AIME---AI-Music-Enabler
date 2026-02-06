#!/usr/bin/env python3
"""Script simple pour tester la pagination Discogs corrigée."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Artist
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Nettoyer les albums Discogs
print("=" * 80)
print("🧹 Nettoyage des anciens albums Discogs...")
print("=" * 80)

db = SessionLocal()
old_count = db.query(Album).filter(Album.source == 'discogs').count()
db.query(Album).filter(Album.source == 'discogs').delete()
db.commit()
print(f"✅ {old_count} anciens albums supprimés\n")

# Récupérer la collection directement
print("=" * 80)
print("📡 Récupération de la collection Discogs (nouvelle pagination)...")
print("=" * 80 + "\n")

from backend.app.services.discogs_service import DiscogsService
import json

with open('./config/secrets.json', 'r') as f:
    secrets = json.load(f)

discogs_config = secrets.get('discogs', {})
service = DiscogsService(
    api_key=discogs_config.get('api_key'),
    username=discogs_config.get('username')
)

# Récupérer TOUS les albums
try:
    albums = service.get_collection(limit=None)
    print(f"\n✅ Total: {len(albums)} albums récupérés\n")
    
    # Rechercher Tame Impala
    tame_albums = [a for a in albums if any('Tame Impala' in str(art) for art in a.get('artists', []))]
    print(f"🎵 Albums 'Tame Impala': {len(tame_albums)}")
    for album in tame_albums:
        print(f"   • {album['title']} ({album['year']}) - {album['artists']}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

db.close()
print("\n" + "=" * 80)
