#!/usr/bin/env python3
"""Script pour relancer la synchronisation Discogs avec la nouvelle pagination."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album

# Nettoyer les albums Discogs
db = SessionLocal()
discogs_count = db.query(Album).filter(Album.source == 'discogs').count()
print(f"📊 Albums Discogs actuels: {discogs_count}")

if discogs_count > 0:
    print("🗑️ Suppression des albums Discogs...")
    db.query(Album).filter(Album.source == 'discogs').delete()
    db.commit()
    print(f"✅ {discogs_count} albums supprimés")

db.close()

# Lancer la synchronisation via le service backend
print("\n" + "=" * 80)
print("🔄 Lancement de la synchronisation Discogs...")
print("=" * 80)

import json
from backend.app.services.discogs_service import DiscogsService
from backend.app.services.spotify_service import SpotifyService  
from backend.app.services.ai_service import AIService

# Charger les secrets
with open('./config/secrets.json', 'r') as f:
    secrets = json.load(f)

# Initialiser les services
discogs_config = secrets.get('discogs', {})
spotify_config = secrets.get('spotify', {})
ai_config = secrets.get('euria', {})

discogs_service = DiscogsService(
    api_key=discogs_config.get('api_key'),
    username=discogs_config.get('username')
)

# Récupérer la collection
print("\n📡 Récupération collection Discogs avec la NOUVELLE pagination...")
albums_data = discogs_service.get_collection(limit=None)
print(f"\n✅ {len(albums_data)} albums récupérés de Discogs")

# Compter Tame Impala
tame_impala = [a for a in albums_data if any('Tame Impala' in str(artist) for artist in a.get('artists', []))]
print(f"\n🎵 Albums Tame Impala trouvés: {len(tame_impala)}")
for album in tame_impala:
    print(f"  - {album['title']} ({album['year']})")

print("\n" + "=" * 80)
