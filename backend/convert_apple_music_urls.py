"""Script pour convertir toutes les URLs Apple Music au format universel (sans région)."""
import sys
import re
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album

db = SessionLocal()

print('\n' + '='*80)
print('🔧 CONVERSION DES URLs APPLE MUSIC AU FORMAT UNIVERSEL')
print('='*80 + '\n')

# Pattern pour extraire l'ID de l'album depuis différents formats d'URLs
patterns = [
    r'music\.apple\.com/[a-z]{2}/album/[^/]+/(\d+)',  # /fr/album/name/123
    r'music\.apple\.com/album/[^/]+/(\d+)',            # /album/name/123
    r'music\.apple\.com/album/(\d+)',                  # /album/123
]

albums = db.query(Album).filter(Album.apple_music_url.isnot(None)).all()

print(f'📀 Traitement de {len(albums)} albums\n')

updated = 0
errors = 0

for album in albums:
    url = album.apple_music_url
    
    # Ignorer les URLs de recherche
    if 'search?term=' in url:
        continue
    
    # Ne convertir que les URLs avec une région spécifique (/fr/, /ch/, etc.)
    if not re.search(r'music\.apple\.com/[a-z]{2}/album/', url):
        continue
    
    # Extraire l'ID de l'album
    album_id = None
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            album_id = match.group(1)
            break
    
    if album_id:
        # Créer l'URL universelle (sans région) avec le nom d'album extrait
        # Format: https://music.apple.com/album/id{ID}
        new_url = f'https://music.apple.com/album/id{album_id}'
        
        if new_url != url:
            old_url = url
            album.apple_music_url = new_url
            db.commit()
            
            if updated < 10:  # Afficher les 10 premiers pour vérification
                print(f'✅ {album.title[:50]}...')
                print(f'   Avant: {old_url}')
                print(f'   Après: {new_url}')
                print()
            
            updated += 1
    else:
        if errors < 5:
            print(f'⚠️ Impossible d\'extraire l\'ID: {album.title}')
            print(f'   URL: {url}')
            print()
        errors += 1

if updated > 10:
    print(f'... et {updated - 10} autres albums')
    print()

print('='*80)
print(f'✅ {updated} URLs converties au format universel')
if errors > 0:
    print(f'⚠️ {errors} URLs non traitées (format non reconnu)')
print('='*80)
print()
print('💡 Format universel utilisé: https://music.apple.com/album/id{ID}')
print('   Ce format fonctionne dans toutes les régions et s\'adapte automatiquement')
print('   à la région de l\'utilisateur.')
print('='*80)

db.close()
