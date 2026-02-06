#!/usr/bin/env python3
"""Vérifie que les descriptions Euria et images d'artiste ont été appliquées."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Image, Artist

db = SessionLocal()

# Afficher les 5 Tame Impala avec descriptions
ids = [35382589, 6403240, 22806698, 22474430, 27194601]
print('\n✅ VÉRIFICATION - TAME IMPALA AVEC DESCRIPTIONS + IMAGES')
print('=' * 80)

for release_id in ids:
    album = db.query(Album).filter_by(discogs_id=str(release_id)).first()
    
    if album:
        print(f'\n🎵 {album.title}')
        
        # Description Euria
        if album.ai_description:
            print(f'   📝 Description Euria: ✓ {album.ai_description[:70]}...')
        else:
            print(f'   📝 Description Euria: ❌ Non renseignée')
        
        # Images Discogs album
        images = db.query(Image).filter_by(album_id=album.id, source='discogs').count()
        print(f'   🖼️  Images album Discogs: {images}')
        
        # Images d'artiste
        artists = album.artists
        artist_has_image = False
        for artist in artists:
            artist_images = db.query(Image).filter_by(
                artist_id=artist.id,
                image_type='artist',
                source='discogs'
            ).all()
            if artist_images:
                print(f'   👤 Artiste {artist.name}: ✓ {len(artist_images)} image(s)')
                artist_has_image = True
        
        if not artist_has_image and artists:
            print(f'   👤 Artistes ({len(artists)}): ❌ Pas d\'images Discogs')

print('\n' + '=' * 80)

# Résumé global
total_with_desc = db.query(Album).filter(Album.ai_description.isnot(None)).count()
total_artist_imgs = db.query(Image).filter_by(image_type='artist', source='discogs').count()

print(f'\n📊 STATISTIQUES GLOBALES:')
print(f'   Albums avec descriptions AI: {total_with_desc}')
print(f'   Images artiste Discogs: {total_artist_imgs}')

print('\n' + '=' * 80 + '\n')

db.close()
