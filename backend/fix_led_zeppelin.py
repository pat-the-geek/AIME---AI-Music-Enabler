"""Script pour corriger les titres des albums Led Zeppelin et régénérer les URLs."""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Album
from app.services.apple_music_service import AppleMusicService
from app.services.spotify_service import SpotifyService
import asyncio

db = SessionLocal()

# Configuration Spotify
from app.core.config import get_settings
settings = get_settings()
secrets = settings.secrets
spotify_config = secrets.get('spotify', {})

spotify_service = SpotifyService(
    client_id=spotify_config.get('client_id'),
    client_secret=spotify_config.get('client_secret')
)

async def fix_led_zeppelin():
    print('\n' + '='*80)
    print('🔧 CORRECTION DES ALBUMS LED ZEPPELIN')
    print('='*80 + '\n')
    
    # Albums à corriger
    corrections = [
        {'id': 1181, 'old': 'Untitled', 'new': 'Led Zeppelin IV'},
        {'id': 1536, 'old': 'IV', 'new': 'Led Zeppelin IV'},
    ]
    
    for correction in corrections:
        album = db.query(Album).filter_by(id=correction['id']).first()
        
        if album:
            print(f'📝 Album ID {album.id}:')
            print(f'   Ancien titre: "{correction["old"]}"')
            print(f'   Nouveau titre: "{correction["new"]}"')
            
            # Mettre à jour le titre
            album.title = correction['new']
            
            # Régénérer l'URL Apple Music
            artist_name = album.artists[0].name if album.artists else "Led Zeppelin"
            apple_music_url = AppleMusicService.generate_url_for_album(artist_name, album.title)
            if apple_music_url:
                album.apple_music_url = apple_music_url
                print(f'   🍎 Nouvelle URL Apple Music: {apple_music_url}')
            
            # Régénérer l'URL Spotify
            spotify_details = await spotify_service.search_album_details(artist_name, album.title)
            if spotify_details and spotify_details.get('spotify_url'):
                album.spotify_url = spotify_details['spotify_url']
                print(f'   🎵 Nouvelle URL Spotify: {spotify_details["spotify_url"]}')
                if spotify_details.get('year'):
                    album.year = spotify_details['year']
                    print(f'   📅 Année: {spotify_details["year"]}')
            
            db.commit()
            print(f'   ✅ Mise à jour terminée\n')
        else:
            print(f'   ❌ Album ID {correction["id"]} introuvable\n')
    
    print('='*80)
    print('✅ CORRECTION TERMINÉE')
    print('='*80)

# Exécuter la correction
asyncio.run(fix_led_zeppelin())
db.close()
