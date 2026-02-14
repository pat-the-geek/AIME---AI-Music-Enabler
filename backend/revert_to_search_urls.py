"""Revenir au format de recherche pour Led Zeppelin (comme les autres albums)."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist
from urllib.parse import quote

db = SessionLocal()

print('\n' + '='*80)
print('🔧 CONVERSION AU FORMAT DE RECHERCHE (comme les autres albums)')
print('='*80 + '\n')

artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()

if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    print(f'📀 Conversion de {len(albums)} albums Led Zeppelin\n')
    print('Note: On utilise le format de recherche qui fonctionne pour tous les autres albums\n')
    
    updated = 0
    for album in albums:
        artist_name = album.artists[0].name if album.artists else "Led Zeppelin"
        album_title = album.title
        
        # Générer une URL de recherche comme pour les autres albums
        search_query = f"{album_title} {artist_name}".strip()
        encoded_query = quote(search_query)
        new_url = f"https://music.apple.com/search?term={encoded_query}"
        
        if new_url != album.apple_music_url:
            print(f'✅ {album.title}')
            print(f'   Avant: {album.apple_music_url}')
            print(f'   Après: {new_url}')
            print()
            
            album.apple_music_url = new_url
            db.commit()
            updated += 1
    
    print('='*80)
    print(f'✅ {updated} albums convertis au format de recherche')
    print('='*80)
    print()
    print('💡 Ce format fonctionne pour tous les autres albums')
    print('   Les IDs Apple Music directs ne semblent pas fonctionner pour Led Zeppelin')
    print('='*80)

db.close()
