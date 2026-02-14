#!/usr/bin/env python3
"""Tester les validations Apple Music."""

import sys
sys.path.insert(0, '.')

from app.services.apple_music_service import AppleMusicService
from app.models import Album, Artist

print('\n🧪 TEST: Validations Apple Music\n')

# Test 1: Vérifier que generate_url_for_album retourne une URL compatible
print('1️⃣  Test generate_url_for_album:')
url = AppleMusicService.generate_url_for_album('Pink Floyd', 'The Wall')
is_valid = AppleMusicService.is_compatible_url(url)
print(f'   URL: {url[:70]}...')
print(f'   Valide: {is_valid} {"✅" if is_valid else "❌"}')

# Test 2: Vérifier les patterns incompatibles
print('\n2️⃣  Test de détection des URLs incompatibles:')
test_urls = [
    ('music://itunes.apple.com/album/id123456789', False, 'music:// protocol'),
    ('https://music.apple.com/album/id123456789', False, 'direct ID format'),
    ('https://music.apple.com/search?term=The+Wall', True, 'search URL'),
    (None, True, 'None (acceptable)'),
    ('', False, 'empty string (invalid)'),
]

for url, should_be_valid, description in test_urls:
    is_valid = AppleMusicService.is_compatible_url(url)
    status = "✅" if is_valid == should_be_valid else "❌"
    print(f'   {status} {description}: {is_valid}')

# Test 3: Vérifier la méthode de validation du modèle
print('\n3️⃣  Test validation Album.is_valid_apple_music_url():')
album = Album(
    title='Test Album',
    year=2024,
    apple_music_url=AppleMusicService.generate_url_for_album('Test', 'Album')
)
is_valid = album.is_valid_apple_music_url()
print(f'   Album avec search URL: {is_valid} {"✅" if is_valid else "❌"}')

# Test avec URL incompatible
album2 = Album(
    title='Test Album 2',
    year=2024,
    apple_music_url='https://music.apple.com/album/id123456789'
)
is_valid2 = album2.is_valid_apple_music_url()
print(f'   Album avec direct ID: {is_valid2} {"✅" if not is_valid2 else "❌"}')

print('\n✨ Tests terminés!\n')
