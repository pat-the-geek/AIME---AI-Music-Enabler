"""Script pour rechercher manuellement les URLs Apple Music directes pour Led Zeppelin."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

# Mapping manuel des URLs Apple Music correctes pour Led Zeppelin
# Ces URLs ont été vérifiées et fonctionnent
apple_music_urls = {
    'Led Zeppelin IV': 'https://music.apple.com/fr/album/led-zeppelin-iv-remaster/580708175',
    'Led Zeppelin': 'https://music.apple.com/fr/album/led-zeppelin-remaster/580707539',
    'Houses of the Holy (hd Remastered Edition)': 'https://music.apple.com/fr/album/houses-of-the-holy-2014-remaster/1440831163',
    'Led Zeppelin Iii (remaster)': 'https://music.apple.com/fr/album/led-zeppelin-iii/1469919435',
}

print('\n' + '='*80)
print('🔧 CORRECTION DES URLs APPLE MUSIC - LED ZEPPELIN')
print('='*80 + '\n')

artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()

if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    updated = 0
    for album in albums:
        # Vérifier si c'est une URL de recherche (problématique)
        if album.apple_music_url and 'search?term=' in album.apple_music_url:
            # Essayer de trouver une URL directe dans notre mapping
            if album.title in apple_music_urls:
                old_url = album.apple_music_url
                album.apple_music_url = apple_music_urls[album.title]
                db.commit()
                
                print(f'✅ {album.title}')
                print(f'   Ancienne URL (RECHERCHE): {old_url[:60]}...')
                print(f'   Nouvelle URL (DIRECTE): {album.apple_music_url}')
                print()
                updated += 1
            else:
                print(f'⚠️ {album.title}')
                print(f'   URL de recherche: {album.apple_music_url[:60]}...')
                print(f'   Pas de mapping trouvé - besoin d\'une recherche manuelle')
                print()
    
    print('='*80)
    print(f'✅ {updated} URLs mises à jour')
    print('='*80)

db.close()
