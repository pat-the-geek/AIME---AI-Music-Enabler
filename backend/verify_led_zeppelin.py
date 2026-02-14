"""Vérification finale des URLs Apple Music pour Led Zeppelin."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()
artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()

if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    print('\n' + '='*80)
    print('✅ VÉRIFICATION FINALE - URLs Apple Music Led Zeppelin')
    print('='*80 + '\n')
    
    all_direct = True
    for album in albums:
        is_direct = '/album/' in album.apple_music_url
        status = '✅' if is_direct else '❌'
        url_type = 'DIRECTE' if is_direct else 'RECHERCHE'
        
        print(f'{status} {album.title}')
        print(f'   Type: {url_type}')
        print(f'   URL: {album.apple_music_url}')
        print()
        
        if not is_direct:
            all_direct = False
    
    print('='*80)
    if all_direct:
        print('🎉 SUCCÈS: Tous les albums ont des URLs directes Apple Music !')
        print('Les boutons Apple Music devraient maintenant fonctionner correctement.')
    else:
        print('⚠️ Certains albums ont encore des URLs de recherche')
    print('='*80)

db.close()
