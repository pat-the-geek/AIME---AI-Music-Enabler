"""Analyser les albums de Feu ! Chatterton."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

print('\n' + '='*80)
print('🔍 ANALYSE - Albums Feu ! Chatterton')
print('='*80 + '\n')

# Chercher Feu ! Chatterton
artist = db.query(Artist).filter(Artist.name.like('%Feu%Chatterton%')).first()

if artist:
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    print(f'Artiste trouvé: {artist.name}')
    print(f'Nombre d\'albums: {len(albums)}\n')
    
    for album in albums:
        print(f'📀 {album.title}')
        print(f'   ID: {album.id}')
        print(f'   Apple Music URL: {album.apple_music_url}')
        print(f'   Spotify URL: {album.spotify_url}')
        
        # Vérifier le format de l'URL
        if album.apple_music_url:
            if 'search?term=' in album.apple_music_url:
                print(f'   ⚠️ Apple Music: URL de RECHERCHE')
            elif 'music://' in album.apple_music_url:
                print(f'   ℹ️ Apple Music: Format protocole (music://)')
            elif '/id' in album.apple_music_url or '/album' in album.apple_music_url:
                print(f'   ℹ️ Apple Music: URL directe')
        else:
            print(f'   ❌ Apple Music: AUCUNE URL')
        
        print()
else:
    print('❌ Artiste "Feu ! Chatterton" non trouvé')
    print('\nRecherche avec d\'autres variantes...\n')
    
    # Chercher avec d'autres variantes
    variants = ['Feu', 'Chatterton', 'Feu !']
    for variant in variants:
        artists = db.query(Artist).filter(Artist.name.like(f'%{variant}%')).all()
        if artists:
            print(f'💡 Trouvé avec "{variant}":')
            for artist in artists[:5]:  # Afficher max 5
                print(f'   - {artist.name}')
            print()

print('='*80)

db.close()
