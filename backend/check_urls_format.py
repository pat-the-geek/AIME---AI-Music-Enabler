"""Vérifier les URLs exactes stockées et les tester."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

print('\n' + '='*80)
print('🔗 URLs STOCKÉES - Vérification')
print('='*80 + '\n')

artists_to_check = ['Led Zeppelin', 'Feu ! Chatterton']

for artist_name in artists_to_check:
    artist = db.query(Artist).filter(Artist.name.like(f'%{artist_name}%')).first()
    
    if artist:
        albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
        
        print(f'\n📀 {artist_name}\n')
        
        for album in albums:
            print(f'Album: {album.title}')
            print(f'  Spotify:      {album.spotify_url[:60]}...' if album.spotify_url else '  Spotify:      ❌')
            if album.apple_music_url:
                print(f'  Apple Music:  {album.apple_music_url[:60]}...')
                if 'search' in album.apple_music_url:
                    print(f'              → RECHERCHE (fallback)')
                elif 'music.apple.com' in album.apple_music_url and '/album/id' in album.apple_music_url:
                    print(f'              → DIRECT ID')
                else:
                    print(f'              → FORMAT: {album.apple_music_url.split("music.apple.com")[-1][:30]}...')
            else:
                print(f'  Apple Music:  ❌')
            print()

db.close()
