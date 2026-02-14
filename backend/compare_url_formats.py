"""Comparer le format des URLs entre albums qui fonctionnent et Led Zeppelin."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

print('\n' + '='*80)
print('🔍 COMPARAISON: Albums qui fonctionnent vs Led Zeppelin')
print('='*80 + '\n')

# Quelques albums populaires qui devraient fonctionner
test_artists = ['Nirvana', 'Pink Floyd', 'Radiohead']
print('Albums qui FONCTIONNENT (pour comparaison):\n')

working_formats = set()
for artist_name in test_artists:
    artist = db.query(Artist).filter(Artist.name.like(f'%{artist_name}%')).first()
    if artist:
        album = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).first()
        if album and album.apple_music_url:
            print(f'✅ {album.title} - {artist_name}')
            print(f'   URL: {album.apple_music_url}')
            
            # Analyser le format
            url = album.apple_music_url
            if url.startswith('music://'):
                working_formats.add('music://')
            elif url.startswith('https://music.apple.com/album/id'):
                working_formats.add('https://...album/id{ID}')
            elif 'search?term=' in url:
                working_formats.add('search URL')
            else:
                working_formats.add('autre')
            print()

print('='*80)
print('\nAlbums Led Zeppelin (NE FONCTIONNENT PAS):\n')

led_formats = set()
artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()
if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).limit(3).all()
    for album in albums:
        print(f'❌ {album.title}')
        print(f'   URL: {album.apple_music_url}')
        
        # Analyser le format
        url = album.apple_music_url
        if url.startswith('music://'):
            led_formats.add('music://')
        elif url.startswith('https://music.apple.com/album/id'):
            led_formats.add('https://...album/id{ID}')
        elif 'search?term=' in url:
            led_formats.add('search URL')
        else:
            led_formats.add('autre')
        print()

print('='*80)
print('\n📊 ANALYSE DES FORMATS:\n')
print(f'Formats utilisés par les albums qui FONCTIONNENT: {", ".join(working_formats)}')
print(f'Formats utilisés par Led Zeppelin: {", ".join(led_formats)}')
print()

if led_formats == working_formats:
    print('⚠️ Les formats sont IDENTIQUES!')
    print('   Le problème ne vient PAS du format d\'URL.')
    print('   Hypothèses:')
    print('   1. Les IDs Apple Music de Led Zeppelin sont incorrects')
    print('   2. Les albums ne sont pas disponibles dans votre région')
    print('   3. Le problème vient du frontend (ouverture des liens)')
else:
    print('💡 Les formats sont DIFFÉRENTS!')
    print('   Il faut aligner Led Zeppelin sur le format qui fonctionne.')

print('='*80)

db.close()
