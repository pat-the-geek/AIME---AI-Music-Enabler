#!/usr/bin/env python3
"""ÉTAPE 1: Récupère les données Discogs et crée un fichier JSON."""
import sys
sys.path.insert(0, './backend')

from backend.app.services.discogs_service import DiscogsService
import json
import time
from datetime import datetime

print("\n" + "=" * 80)
print("📡 ÉTAPE 1: RÉCUPÉRATION DISCOGS")
print("=" * 80)

# Charger les secrets
with open('./config/secrets.json') as f:
    secrets = json.load(f)

# Créer le service
service = DiscogsService(
    api_key=secrets['discogs']['api_key'],
    username=secrets['discogs']['username']
)

# Récupérer la collection
print("\n🔄 Récupération de la collection Discogs...")
start_time = time.time()
albums_data = service.get_collection(limit=None)
elapsed = time.time() - start_time

print(f"✅ {len(albums_data)} albums récupérés en {elapsed:.1f}s\n")

# Préparer les données pour export
data_to_export = {
    'metadata': {
        'created_at': datetime.now().isoformat(),
        'total_albums': len(albums_data),
        'source': 'discogs',
        'steps_completed': ['fetch']
    },
    'albums': []
}

# Convertir avec visualisation
print("📋 Préparation des données...")
for idx, album in enumerate(albums_data, 1):
    # Afficher progression tous les 50 albums
    if idx % 50 == 0:
        print(f"  ✓ {idx}/{len(albums_data)} albums traités")
    
    # Extraire les données de base
    album_record = {
        'release_id': str(album['release_id']),
        'title': album['title'],
        'year': album.get('year') or None,
        'artists': album.get('artists', []),
        'formats': album.get('formats', []),
        'labels': album.get('labels', []),
        'cover_image': album.get('cover_image'),
        'discogs_url': album.get('discogs_url'),
        # Champs à enrichir dans étape 2
        'support': 'Unknown',
        'enriched': False
    }
    
    data_to_export['albums'].append(album_record)

# Sauvegarder en JSON
output_file = './discogs_data_step1.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data_to_export, f, ensure_ascii=False, indent=2)

print(f"\n✅ Étape 1 complétée")
print("=" * 80)
print(f"📊 Résumé:")
print(f"  Albums: {len(albums_data)}")
print(f"  Temps: {elapsed:.1f}s")
print(f"  Fichier: {output_file}")
print("=" * 80 + "\n")
