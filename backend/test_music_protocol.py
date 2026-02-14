"""Script pour tester et convertir les URLs Led Zeppelin au format itms:// natif Apple Music."""
import sys
import re
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

print('\n' + '='*80)
print('🔧 CONVERSION AU FORMAT NATIF APPLE MUSIC (itms://)')
print('='*80 + '\n')

# Trouver Led Zeppelin
artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()

if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    print(f'📀 Traitement de {len(albums)} albums Led Zeppelin\n')
    print('Test des différents formats d\'URLs:\n')
    
    # Prendre un album comme test
    test_album = albums[0]
    test_url = test_album.apple_music_url
    
    # Extraire l'ID
    match = re.search(r'/id(\d+)', test_url)
    if match:
        album_id = match.group(1)
        
        print(f'Album test: {test_album.title}')
        print(f'ID Apple Music: {album_id}\n')
        
        print('Formats disponibles:\n')
        print(f'1. Format actuel (https://):')
        print(f'   {test_url}')
        print()
        print(f'2. Format natif iTunes Store (itms://):')
        print(f'   itms://itunes.apple.com/album/id{album_id}')
        print()
        print(f'3. Format natif Apple Music (music://):')
        print(f'   music://itunes.apple.com/album/id{album_id}')
        print()
        print(f'4. Format court Apple Music:')
        print(f'   https://music.apple.com/album/{album_id}')
        print()
        
        print('='*80)
        print('💡 RECOMMANDATION:')
        print()
        print('Le format "music://" est natif à Apple Music et devrait fonctionner')
        print('dans l\'application, même si le format https:// fonctionne dans Safari.')
        print()
        print('Voulez-vous convertir tous les albums Led Zeppelin au format music:// ?')
        print('='*80)
        print()
        
        # Montrer ce que ça donnerait pour tous les albums
        print('Aperçu de la conversion pour tous les albums:\n')
        for idx, album in enumerate(albums[:3], 1):
            url = album.apple_music_url
            match = re.search(r'/id(\d+)', url)
            if match:
                aid = match.group(1)
                new_url = f'music://itunes.apple.com/album/id{aid}'
                print(f'{idx}. {album.title[:50]}')
                print(f'   Avant: {url}')
                print(f'   Après: {new_url}')
                print()
        
        if len(albums) > 3:
            print(f'   ... et {len(albums)-3} autres albums')

db.close()
