#!/usr/bin/env python3
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Image, Metadata

db = SessionLocal()

# Chercher les 5 albums Tame Impala par Discogs ID
ids = [35382589, 6403240, 22806698, 22474430, 27194601]

print(f'\n✅ Vérification des 5 albums Tame Impala Discogs:')
print('=' * 80)

for release_id in ids:
    album = db.query(Album).filter_by(discogs_id=str(release_id)).first()
    
    if album:
        print(f'\n✓ {album.title} ({album.year})')
        print(f'  Source: {album.source} | Support: {album.support}')
        
        # Images
        images = db.query(Image).filter_by(album_id=album.id, source='discogs').all()
        if images:
            print(f'  Image Discogs: {images[0].url[:60]}...')
        else:
            print(f'  Image Discogs: ❌ Aucune')
        
        # Metadata
        metadata = db.query(Metadata).filter_by(album_id=album.id).first()
        if metadata and metadata.labels:
            print(f'  Labels: {metadata.labels[:60]}...')
    else:
        print(f'\n✗ Album {release_id}: ❌ NOT FOUND')

print("\n" + "=" * 80)

# Compter tous les albums Discogs
discogs_albums = db.query(Album).filter_by(source='discogs').count()
print(f'\n📊 Résumé:')
print(f'  Total albums Discogs: {discogs_albums}')

db.close()
