#!/usr/bin/env python3
"""Check if Everybody Knows has artist image data"""
from app.database import SessionLocal
from app.models import Album, Artist, Image
from sqlalchemy.orm import joinedload

db = SessionLocal()

# Trouver Everybody Knows par The Young Gods
album = db.query(Album).options(
    joinedload(Album.artists)
).filter(Album.title.like('%Everybody Knows%')).first()

if album:
    print(f'Album: {album.title}')
    print(f'Album ID: {album.id}')
    print(f'Artists: {[a.name for a in album.artists]}')
    print(f'Album image: {album.image_url[:60] if album.image_url else None}')
    
    # Vérifier image d'artiste
    for artist in album.artists:
        print(f'\n🎤 Artiste: {artist.name} (ID: {artist.id})')
        artist_image = db.query(Image).filter(
            Image.artist_id == artist.id,
            Image.image_type == 'artist'
        ).first()
        if artist_image:
            print(f'   ✅ Image artiste: {artist_image.url[:60]}...')
        else:
            print(f'   ❌ Pas d\'image artiste trouvée')
else:
    print('Album non trouvé')

db.close()
