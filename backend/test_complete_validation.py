#!/usr/bin/env python3
"""Test complet du système de validation Apple Music."""

import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import Album, Artist
from app.services.apple_music_service import AppleMusicService

db = SessionLocal()

print('\n🔍 TEST COMPLET: Système de validation Apple Music\n')
print('=' * 70)

# Test 1: Vérifier que AUCUN album n'a d'URL incompatible
print('\n1️⃣  Audit complet de la base de données:')
total_albums = db.query(Album).count()
compatible_count = 0
incompatible_count = 0

for album in db.query(Album).filter(Album.apple_music_url != None, Album.apple_music_url != '').all():
    if AppleMusicService.is_compatible_url(album.apple_music_url):
        compatible_count += 1
    else:
        incompatible_count += 1
        print(f'   ⚠️  TROUVÉ: {album.title} - {album.apple_music_url[:60]}...')

print(f'\n   Total albums: {total_albums}')
print(f'   URLs compatibles: {compatible_count} ✅')
print(f'   URLs incompatibles: {incompatible_count} ❌')

if incompatible_count == 0:
    print('\n   ✨ PARFAIT! Aucune URL incompatible détectée!')
else:
    print(f'\n   ⚠️  {incompatible_count} URLs invalides trouvées!')

# Test 2: Tester la génération d'URLs pour quelques albums
print('\n2️⃣  Test de génération d\'URLs pour albums existants:')
artists = db.query(Artist).limit(3).all()
for artist in artists:
    if artist.albums:
        album = artist.albums[0]
        generated_url = AppleMusicService.generate_url_for_album(artist.name, album.title)
        is_valid = AppleMusicService.is_compatible_url(generated_url)
        status = '✅' if is_valid else '❌'
        print(f'   {status} {artist.name} - {album.title}')
        if not is_valid:
            print(f'      Generated: {generated_url}')

# Test 3: Vérifier la validation du modèle
print('\n3️⃣  Test validation Album.is_valid_apple_music_url():')
sample_albums = db.query(Album).filter(Album.apple_music_url != None).limit(5).all()
all_valid = True
for album in sample_albums:
    is_valid = album.is_valid_apple_music_url()
    if not is_valid:
        all_valid = False
        print(f'   ❌ {album.title}: INVALIDE')

if all_valid:
    print(f'   ✅ Les {len(sample_albums)} albums testés sont tous valides!')

print('\n' + '=' * 70)
print(f'\n✨ Tests complétés!\n')

db.close()
