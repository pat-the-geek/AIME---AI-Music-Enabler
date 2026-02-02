#!/usr/bin/env python3
"""Test de la pagination Discogs."""
import discogs_client
import json
import time

# Charger les secrets
with open('../config/secrets.json', 'r') as f:
    secrets = json.load(f)

discogs_config = secrets.get('discogs', {})
client = discogs_client.Client('MusicTrackerApp/4.0', user_token=discogs_config.get('api_key'))

user = client.identity()
print(f'👤 Utilisateur: {user.username}')
print(f'📀 Albums dans la collection: {user.num_collection}')

collection = user.collection_folders[0].releases
print(f'📁 Folder: {user.collection_folders[0].name}')
print(f'📊 Count dans folder: {user.collection_folders[0].count}')

# Tester la pagination
print(f'\n🔍 Type de collection: {type(collection)}')
print(f'📄 Page size: {collection.per_page if hasattr(collection, "per_page") else "N/A"}')
print(f'📄 Pages: {collection.pages if hasattr(collection, "pages") else "N/A"}')

# Compter les releases disponibles
count = 0
print('\n📊 Itération sur la collection...')
for release in collection:
    count += 1
    if count >= 60:  # Limiter pour ne pas faire toutes les requêtes
        print(f'\n⚠️ Arrêt après {count} releases (limite de test)')
        break
    if count % 10 == 0:
        print(f'... {count} releases traités')
    time.sleep(0.5)  # Rate limiting

print(f'\n📊 Total releases itérés: {count}')
print(f'📊 Attendu selon Discogs API: {user.num_collection}')

if count < user.num_collection:
    print(f'\n⚠️ PROBLÈME: Seulement {count} releases itérés sur {user.num_collection} attendus')
    print('La pagination pourrait ne pas fonctionner correctement')
