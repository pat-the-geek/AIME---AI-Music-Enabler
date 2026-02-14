"""Analyser les albums de Feu ! Chatterton et comparaison avec Led Zeppelin."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

print('\n' + '='*80)
print('🔍 ANALYSE: Albums avec problèmes Apple Music')
print('='*80 + '\n')

artists_to_check = ['Led Zeppelin', 'Feu ! Chatterton']

for artist_name in artists_to_check:
    artist = db.query(Artist).filter(Artist.name.like(f'%{artist_name}%')).first()
    
    if artist:
        albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
        
        print(f'\n📀 {artist_name} ({len(albums)} albums)\n')
        
        spotify_working = 0
        apple_music_ok = 0
        
        for album in albums:
            spotify_status = '✅' if album.spotify_url else '❌'
            apple_status = '✅' if album.apple_music_url else '❌'
            
            print(f'{spotify_status} Spotify  {apple_status} Apple Music  →  {album.title}')
            
            if album.spotify_url:
                spotify_working += 1
            if album.apple_music_url and 'search' not in album.apple_music_url:
                apple_music_ok += 1
        
        print(f'\n  Résumé:')
        print(f'  - Spotify URLs: {spotify_working}/{len(albums)}')
        print(f'  - Apple Music URLs: {apple_music_ok}/{len(albums)} (directes)')
        print()

print('='*80)
print('\n💡 ANALYSE:')
print('Si Spotify fonctionne mais Apple Music ne fonctionne pas,')
print('c\'est probablement que:')
print('  1. Les albums n\'existent pas sur Apple Music (ou pas les mêmes versions)')
print('  2. Les IDs Apple Music stockés sont incorrects')
print('  3. Les versions/éditions ne correspondent pas')
print()
print('SOLUTION: Utiliser des URLs de recherche Apple Music comme fallback')
print('='*80)

db.close()
