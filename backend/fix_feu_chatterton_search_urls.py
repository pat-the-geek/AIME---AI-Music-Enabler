"""Convertir les URLs invalides de Feu ! Chatterton en URLs de recherche."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist
from urllib.parse import quote

db = SessionLocal()

artist = db.query(Artist).filter(Artist.name.like('%Feu ! Chatterton%')).first()

if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    updated = 0
    
    print(f'\n🔄 Conversion des URLs Feu ! Chatterton vers format recherche\n')
    
    for album in albums:
        # Vérifier si l'album n'a pas d'URL ou que c'est un ID qui ne fonctionne pas
        # On va convertir L'oiseleur et Live À Paris en URLs de recherche aussi
        # car les IDs directs ne semblent pas fonctionner
        if album.apple_music_url and not 'search' in album.apple_music_url:
            search_term = f"{album.title} Feu ! Chatterton"
            new_url = f"https://music.apple.com/search?term={quote(search_term)}"
            
            album.apple_music_url = new_url
            updated += 1
            
            print(f'✅ {album.title}')
            print(f'   Ancien: {album.apple_music_url if "search" not in album.apple_music_url else ""}')
            print(f'   Nouveau: {new_url[:70]}...\n')
        elif album.apple_music_url and 'search' in album.apple_music_url:
            print(f'✔️  {album.title} (déjà en URL recherche)\n')
    
    db.commit()
    print(f'✨ {updated} albums convertis vers URL de recherche')

db.close()
