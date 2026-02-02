#!/usr/bin/env python3
"""Vérifier les données brutes de Last.fm."""
import sys
import os

# Ajouter les chemins nécessaires
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

# Importer les modules après avoir ajouté les chemins
import requests
import json
from pathlib import Path

# Charger les secrets manuellement
secrets_path = Path(__file__).parent.parent / 'config' / 'secrets.json'
with open(secrets_path) as f:
    secrets = json.load(f)

# Charger les secrets manuellement
secrets_path = Path(__file__).parent.parent / 'config' / 'secrets.json'
with open(secrets_path) as f:
    secrets = json.load(f)

lastfm_config = secrets.get('lastfm', {})
api_key = lastfm_config.get('api_key')
username = lastfm_config.get('username')

# Récupérer les scrobbles récents
params = {
    'method': 'user.getRecentTracks',
    'user': username,
    'api_key': api_key,
    'limit': 10,
    'format': 'json'
}

response = requests.post('https://ws.audioscrobbler.com/2.0/', params=params, timeout=10)
result = response.json()

print('\n📡 DONNÉES BRUTES DE LAST.FM:\n')
if 'recenttracks' in result:
    tracks = result['recenttracks']['track']
    if not isinstance(tracks, list):
        tracks = [tracks]
    
    for i, track in enumerate(tracks[:10], 1):
        print(f'{i}. 🎵 Track: {track.get("name")}')
        
        # Artiste
        artist_data = track.get('artist', {})
        if isinstance(artist_data, dict):
            artist = artist_data.get('#text', 'Unknown')
        else:
            artist = str(artist_data)
        print(f'   🎤 Artiste Last.fm: {artist}')
        
        # Album
        album_data = track.get('album', {})
        if isinstance(album_data, dict):
            album = album_data.get('#text', 'Unknown')
        else:
            album = str(album_data)
        print(f'   📀 Album Last.fm: {album}')
        print()

# Vérifier l'info d'album spécifique
print('\n🔍 VÉRIFICATION ALBUM "More Songs About Buildings and Food":\n')
params2 = {
    'method': 'album.getInfo',
    'artist': 'Talking Heads',
    'album': 'More Songs About Buildings and Food',
    'api_key': api_key,
    'format': 'json'
}

response2 = requests.post('https://ws.audioscrobbler.com/2.0/', params=params2, timeout=10)
result2 = response2.json()

if 'album' in result2:
    album_info = result2['album']
    artist_info = album_info.get('artist', 'Unknown')
    print(f'Artiste selon album.getInfo: {artist_info}')
    
    if 'image' in album_info:
        images = album_info['image']
        print(f'\nImages Last.fm:')
        for img in images:
            size = img.get('size', 'unknown')
            url = img.get('#text', 'no url')
            print(f'  - {size}: {url[:80]}...' if len(url) > 80 else f'  - {size}: {url}')
