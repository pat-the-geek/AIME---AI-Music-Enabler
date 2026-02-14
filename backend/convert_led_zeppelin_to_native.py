"""Script pour convertir les URLs Led Zeppelin au format natif Apple Music (music://)."""
import sys
import re
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

print('\n' + '='*80)
print('🔧 CONVERSION AU FORMAT NATIF APPLE MUSIC (music://)')
print('='*80 + '\n')

# Trouver Led Zeppelin
artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()

if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    print(f'📀 Conversion de {len(albums)} albums Led Zeppelin\n')
    
    updated = 0
    for album in albums:
        url = album.apple_music_url
        
        # Extraire l'ID de l'album
        match = re.search(r'/id(\d+)', url)
        if match:
            album_id = match.group(1)
            
            # Créer l'URL au format natif Apple Music
            new_url = f'music://itunes.apple.com/album/id{album_id}'
            
            if new_url != url:
                print(f'✅ {album.title}')
                print(f'   Avant: {url}')
                print(f'   Après: {new_url}')
                print()
                
                album.apple_music_url = new_url
                db.commit()
                updated += 1
    
    print('='*80)
    print(f'✅ {updated} albums convertis au format natif Apple Music')
    print('='*80)
    print()
    print('💡 Le protocole "music://" est natif à Apple Music et devrait')
    print('   ouvrir directement dans l\'application Apple Music.')
    print('='*80)

db.close()
