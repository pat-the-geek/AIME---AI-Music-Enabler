"""Script pour vérifier et corriger les albums de Led Zeppelin."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

# Trouver Led Zeppelin
artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()

if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    print('\n' + '='*80)
    print('🎸 ALBUMS LED ZEPPELIN - ANALYSE')
    print('='*80 + '\n')
    
    problematic_titles = {
        'Untitled': 'Led Zeppelin IV',
        'IV': 'Led Zeppelin IV',
        'Led Zeppelin': 'Led Zeppelin'  # Premier album, OK
    }
    
    for album in albums:
        status = '❌' if album.title in ['Untitled', 'IV'] else '✅'
        print(f'{status} ID {album.id}: "{album.title}"')
        print(f'   Source: {album.source}')
        print(f'   Discogs ID: {album.discogs_id}')
        print(f'   Apple Music: {album.apple_music_url[:80] if album.apple_music_url else "NULL"}...')
        print(f'   Spotify: {album.spotify_url[:60] if album.spotify_url else "NULL"}...')
        
        if album.title in ['Untitled', 'IV']:
            print(f'   💡 Devrait être: "Led Zeppelin IV"')
        
        print()
    
    print('='*80)
    print('\n📋 RÉSUMÉ:')
    print('   • "Untitled" → devrait être "Led Zeppelin IV" (album le plus célèbre)')
    print('   • "IV" → devrait être "Led Zeppelin IV"')
    print('   • Roon utilise "Untitled" car l\'album n\'a pas de titre officiel')
    print('   • Mais pour Apple Music/Spotify, il faut "Led Zeppelin IV"')
    print('='*80)

db.close()
