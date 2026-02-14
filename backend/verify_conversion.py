#!/usr/bin/env python3
"""Vérifier les URLs converties."""

import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

# Vérifier plusieurs artistes
artists_to_check = ['Nirvana', 'The Who', 'Radiohead', 'The Doors', 'Pink Floyd']

print('\n✅ VÉRIFICATION DES URLS CONVERTIES\n')

for artist_name in artists_to_check:
    artist = db.query(Artist).filter(Artist.name.like(f'%{artist_name}%')).first()
    if artist:
        albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).limit(1).all()
        if albums:
            album = albums[0]
            url_type = 'SEARCH ✅' if 'search' in album.apple_music_url else 'DIRECT ID ❌'
            print(f'{artist_name:20} | {album.title[:40]:40} | {url_type}')

db.close()
