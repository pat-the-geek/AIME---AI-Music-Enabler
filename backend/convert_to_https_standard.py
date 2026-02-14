"""Revenir au format https:// standard pour Led Zeppelin."""
import sys
import re
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

print('\n' + '='*80)
print('🔧 RETOUR AU FORMAT HTTPS:// STANDARD')
print('='*80 + '\n')

# Le protocole music:// ne fonctionne pas avec window.open() dans le frontend
# On revient au format https:// standard

artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()

if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    print(f'📀 Conversion de {len(albums)} albums Led Zeppelin\n')
    print('Note: Le protocole music:// ne fonctionne pas avec window.open()')
    print('On revient au format https:// standard\n')
    
    updated = 0
    for album in albums:
        url = album.apple_music_url
        
        # Extraire l'ID de l'album
        match = re.search(r'id(\d+)', url)
        if match:
            album_id = match.group(1)
            
            # Format standard sans région spécifique
            # On teste le format court: https://music.apple.com/album/{ID}
            new_url = f'https://music.apple.com/album/{album_id}'
            
            if new_url != url:
                print(f'✅ {album.title}')
                print(f'   Avant: {url}')
                print(f'   Après: {new_url}')
                print()
                
                album.apple_music_url = new_url
                db.commit()
                updated += 1
    
    print('='*80)
    print(f'✅ {updated} albums convertis au format https:// standard')
    print('='*80)
    print()
    print('💡 Format utilisé: https://music.apple.com/album/{ID}')
    print('   (sans "id" dans le chemin, format plus court)')
    print('='*80)

db.close()
