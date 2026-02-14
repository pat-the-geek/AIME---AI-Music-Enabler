"""Script pour tester différents formats d'URLs Apple Music pour Led Zeppelin."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

print('\n' + '='*80)
print('🔍 TEST DES FORMATS D\'URLs APPLE MUSIC')
print('='*80 + '\n')

# Trouver un album Led Zeppelin pour tester
artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()
if artist:
    album = db.query(Album).join(Album.artists).filter(
        Artist.id == artist.id,
        Album.title == 'Led Zeppelin IV'
    ).first()
    
    if album:
        current_url = album.apple_music_url
        album_id = '580708175'
        
        print(f'Album: {album.title}')
        print(f'URL actuelle: {current_url}\n')
        
        print('Formats d\'URLs possibles:')
        print()
        
        formats = [
            ('Région FR (actuel)', f'https://music.apple.com/fr/album/led-zeppelin-iv-remaster/{album_id}'),
            ('Région CH (Suisse)', f'https://music.apple.com/ch/album/led-zeppelin-iv-remaster/{album_id}'),
            ('Région US', f'https://music.apple.com/us/album/led-zeppelin-iv-remaster/{album_id}'),
            ('Sans région', f'https://music.apple.com/album/led-zeppelin-iv-remaster/{album_id}'),
            ('ID seulement', f'https://music.apple.com/album/{album_id}'),
            ('Protocole music://', f'music://music.apple.com/album/{album_id}'),
            ('iTunes URL', f'https://itunes.apple.com/album/id{album_id}'),
            ('iTunes music://', f'itms://itunes.apple.com/album/id{album_id}'),
        ]
        
        for idx, (name, url) in enumerate(formats, 1):
            print(f'{idx}. {name}:')
            print(f'   {url}')
            print()
        
        print('='*80)
        print('💡 RECOMMANDATION:')
        print()
        print('Pour Apple Music, essayez ces formats par ordre de priorité:')
        print('1. Sans région: https://music.apple.com/album/...')
        print('2. Protocole music://: music://music.apple.com/album/...')
        print('3. iTunes itms://: itms://itunes.apple.com/album/id...')
        print()
        print('Le format actuel avec "/fr/" peut ne pas fonctionner si vous êtes')
        print('dans une autre région (ex: Suisse = /ch/, USA = /us/)')
        print('='*80)

db.close()
