"""Analyse détaillée des URLs Apple Music pour Led Zeppelin."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()
artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()

if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    print('\n' + '='*80)
    print('🔍 ANALYSE COMPLÈTE - Albums Led Zeppelin')
    print('='*80 + '\n')
    
    search_urls = []
    for album in albums:
        print(f'📀 {album.title}')
        print(f'   ID: {album.id}')
        print(f'   URL: {album.apple_music_url}')
        
        # Vérifier le format de l'URL
        if 'search?term=' in album.apple_music_url:
            print(f'   ❌ TYPE: URL de RECHERCHE (ne fonctionne pas dans l\'app)')
            search_urls.append(album)
        elif 'album/id' in album.apple_music_url:
            print(f'   ✅ TYPE: URL universelle (devrait fonctionner)')
        elif '/album/' in album.apple_music_url:
            print(f'   ✅ TYPE: URL directe')
        else:
            print(f'   ❓ TYPE: Format inconnu')
        print()
    
    print('='*80)
    if search_urls:
        print(f'\n⚠️ PROBLÈME DÉTECTÉ: {len(search_urls)} albums avec URLs de recherche\n')
        print('Ces albums ne fonctionnent PAS dans l\'application Apple Music:')
        for album in search_urls:
            print(f'  - {album.title} (ID: {album.id})')
        print('\n💡 Solution: Utiliser des URLs directes avec les IDs Apple Music')
    else:
        print('✅ Tous les albums ont des URLs correctes')
    print('='*80)

db.close()
