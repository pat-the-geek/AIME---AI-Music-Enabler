#!/usr/bin/env python3
"""Identifier les releases Discogs qui retournent 404."""
import discogs_client
import json

with open('config/secrets.json', 'r') as f:
    secrets = json.load(f)

api_key = secrets['discogs']['api_key']
client = discogs_client.Client('MusicTrackerApp/4.0', user_token=api_key)

user = client.identity()
collection = user.collection_folders[0].releases

print(f'🔍 Analyse des releases 404 dans votre collection Discogs')
print(f'📊 Total releases: {user.num_collection}\n')

releases_404 = []
position = 0

for release in collection:
    position += 1
    try:
        # Tenter d'accéder aux données du release
        release_data = release.release
        _ = release_data.title  # Force l'accès
        
        if position % 50 == 0:
            print(f'✓ {position} releases vérifiés...')
            
    except Exception as e:
        if '404' in str(e):
            releases_404.append({
                'position': position,
                'error': str(e),
                'release_id': getattr(release, 'id', 'unknown')
            })
            print(f'❌ Position {position}: {e}')

print(f'\n{"="*70}')
print(f'📋 RÉSUMÉ')
print(f'{"="*70}')
print(f'✅ Releases valides: {position - len(releases_404)}')
print(f'❌ Releases 404: {len(releases_404)}')
print(f'📊 Taux de succès: {(position - len(releases_404))/position*100:.1f}%')

if releases_404:
    print(f'\n🔍 DÉTAILS DES RELEASES 404:')
    print(f'{"="*70}')
    for idx, rel in enumerate(releases_404, 1):
        print(f'{idx}. Position: {rel["position"]} | Error: {rel["error"]}')

print(f'\n💡 EXPLICATION:')
print(f'Ces releases ont été supprimés de Discogs ou rendus privés.')
print(f'C\'est normal et ne pose pas de problème - ils sont ignorés lors de la synchro.')
