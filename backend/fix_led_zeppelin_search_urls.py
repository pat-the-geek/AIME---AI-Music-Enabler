"""Convertir les URLs de Led Zeppelin du format music:// en URLs de recherche."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist
from urllib.parse import quote

db = SessionLocal()

artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()

if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    updated = 0
    
    print(f'\n🔄 Conversion des URLs Led Zeppelin vers format recherche\n')
    
    for album in albums:
        if album.apple_music_url and album.apple_music_url.startswith('music://'):
            # Créer une URL de recherche
            search_term = f"{album.title} Led Zeppelin"
            new_url = f"https://music.apple.com/search?term={quote(search_term)}"
            
            album.apple_music_url = new_url
            updated += 1
            
            print(f'✅ {album.title}')
            print(f'   Nouveau: {new_url[:70]}...\n')
    
    db.commit()
    print(f'✨ {updated} albums mis à jour')

db.close()
