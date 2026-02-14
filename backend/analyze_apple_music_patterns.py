#!/usr/bin/env python3
"""Analyser tous les patterns d'URL Apple Music pour détecter les problèmes."""

import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import Album
from collections import defaultdict

db = SessionLocal()

# Analyser les types d'URLs Apple Music
url_patterns = defaultdict(int)
problematic_albums = []

albums = db.query(Album).filter(Album.apple_music_url != None, Album.apple_music_url != '').all()

for album in albums:
    url = album.apple_music_url
    artist_name = album.artists[0].name if album.artists else 'Unknown'
    
    if url.startswith('music://'):
        url_patterns['music:// protocol'] += 1
        problematic_albums.append({
            'type': 'music:// protocol',
            'title': album.title,
            'artist': artist_name,
            'url': url[:80] + '...' if len(url) > 80 else url
        })
    elif url.startswith('https://music.apple.com/search'):
        url_patterns['search URL'] += 1
    elif url.startswith('https://music.apple.com/') and '/album/' in url:
        url_patterns['direct album ID'] += 1
        # Vérifier si c'est un format direct ID suspect
        if '/album/id' in url:
            problematic_albums.append({
                'type': 'direct /album/id format',
                'title': album.title,
                'artist': artist_name,
                'url': url[:80] + '...' if len(url) > 80 else url
            })
    elif not url.startswith('https://'):
        url_patterns['invalid format'] += 1
        problematic_albums.append({
            'type': 'invalid format',
            'title': album.title,
            'artist': artist_name,
            'url': url[:80] + '...' if len(url) > 80 else url
        })
    else:
        url_patterns['other'] += 1

print('\n📊 ANALYSE DES FORMATS D\'URL APPLE MUSIC:\n')
for pattern, count in sorted(url_patterns.items(), key=lambda x: x[1], reverse=True):
    print(f'{pattern}: {count}')

if problematic_albums:
    print(f'\n⚠️  ALBUMS POTENTIELLEMENT PROBLÉMATIQUES: {len(problematic_albums)}')
    print('\nExemples (premiers 20):')
    for i, album in enumerate(problematic_albums[:20], 1):
        print(f'\n  {i}. [{album["type"]}] {album["artist"]} - {album["title"]}')
        print(f'     URL: {album["url"]}')

db.close()
