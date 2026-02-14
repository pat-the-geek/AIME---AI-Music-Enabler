#!/usr/bin/env python3
"""Convertir tous les URLs Apple Music direct ID en search URLs."""

import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import Album
from app.services.apple_music_service import AppleMusicService

db = SessionLocal()
service = AppleMusicService()

# Trouver tous les albums avec format direct ID
albums_to_fix = db.query(Album).filter(
    Album.apple_music_url.like('https://music.apple.com/album/id%')
).all()

print(f'\n🔍 Trouvé {len(albums_to_fix)} albums avec format direct ID')
print('📝 Conversion en cours...\n')

fixed_count = 0
errors = []

for album in albums_to_fix:
    try:
        # Générer une search URL
        search_url = service.generate_search_url(album.title, 
                                                album.artists[0].name if album.artists else 'Unknown')
        
        # Mettre à jour l'album
        album.apple_music_url = search_url
        fixed_count += 1
        
        artist_name = album.artists[0].name if album.artists else 'Unknown'
        print(f'✅ {artist_name} - {album.title}')
        
    except Exception as e:
        errors.append({
            'album': album.title,
            'error': str(e)
        })
        print(f'❌ Erreur: {album.title} - {str(e)}')

# Sauvegarder les changements
db.commit()
db.close()

print(f'\n✨ {fixed_count} albums convertis avec succès!')
if errors:
    print(f'⚠️  {len(errors)} erreurs rencontrées')
