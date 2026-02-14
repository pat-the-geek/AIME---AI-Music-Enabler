"""Script pour enrichir les albums Led Zeppelin avec des URLs Apple Music directes via Euria."""
import sys
import os
import requests
import time
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import Album, Artist
from app.core.config import get_settings

# Charger les secrets depuis config
settings = get_settings()
secrets = settings.secrets
euria_config = secrets.get('euria', {})

# Configuration Euria
EURIA_API_URL = euria_config.get('url', 'https://api.infomaniak.com/2/ai/106561/openai/v1/chat/completions')
EURIA_BEARER_TOKEN = euria_config.get('bearer')

def generate_apple_music_url_via_euria(artist_name: str, album_title: str) -> str:
    """Génère une URL Apple Music via l'API Euria."""
    
    if not EURIA_BEARER_TOKEN:
        print("⚠️ EURIA_BEARER_TOKEN non trouvé dans .env")
        return None
    
    prompt = f"""Tu es un assistant spécialisé dans la recherche d'URLs Apple Music.

Trouve l'URL EXACTE Apple Music pour cet album:
- Artiste: {artist_name}
- Album: {album_title}

IMPORTANT:
1. Retourne UNIQUEMENT l'URL Apple Music (format: https://music.apple.com/fr/album/...)
2. Si tu trouves l'album, retourne l'URL directe avec l'ID de l'album
3. Si tu ne trouves pas, retourne exactement: "NOT_FOUND"
4. Ne retourne RIEN d'autre que l'URL ou "NOT_FOUND"

Exemple de réponse attendue:
https://music.apple.com/fr/album/led-zeppelin-iv/1469711138
"""
    
    headers = {
        "Authorization": f"Bearer {EURIA_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(EURIA_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        
        # Vérifier si c'est une URL Apple Music valide
        if content.startswith('https://music.apple.com/') and '/album/' in content:
            return content
        else:
            return None
            
    except Exception as e:
        print(f"   ❌ Erreur Euria: {e}")
        return None


def enrich_led_zeppelin_albums():
    db = SessionLocal()
    
    print('\n' + '='*80)
    print('🍎 ENRICHISSEMENT URLS APPLE MUSIC - LED ZEPPELIN')
    print('='*80 + '\n')
    
    # Trouver tous les albums Led Zeppelin
    artist = db.query(Artist).filter(Artist.name.like('%Led Zeppelin%')).first()
    
    if not artist:
        print("❌ Led Zeppelin introuvable")
        return
    
    albums = db.query(Album).join(Album.artists).filter(Artist.id == artist.id).all()
    
    print(f"📀 {len(albums)} albums trouvés\n")
    
    updated = 0
    for idx, album in enumerate(albums, 1):
        artist_name = album.artists[0].name if album.artists else "Led Zeppelin"
        
        # Vérifier si l'URL actuelle est une URL de recherche
        is_search_url = album.apple_music_url and 'search?term=' in album.apple_music_url
        
        if is_search_url or not album.apple_music_url:
            print(f"[{idx}/{len(albums)}] 🔍 {album.title}")
            print(f"   URL actuelle: {album.apple_music_url[:80]}..." if album.apple_music_url else "   Pas d'URL")
            
            # Essayer de générer une URL directe via Euria
            direct_url = generate_apple_music_url_via_euria(artist_name, album.title)
            
            if direct_url:
                album.apple_music_url = direct_url
                db.commit()
                print(f"   ✅ URL directe trouvée: {direct_url}")
                updated += 1
            else:
                print(f"   ⚠️ URL directe non trouvée, conservation de l'URL de recherche")
            
            print()
            
            # Délai pour ne pas surcharger l'API
            time.sleep(0.5)
        else:
            print(f"[{idx}/{len(albums)}] ✅ {album.title} - URL directe déjà présente")
    
    print('='*80)
    print(f'✅ ENRICHISSEMENT TERMINÉ: {updated} URLs directes ajoutées')
    print('='*80)
    
    db.close()

if __name__ == "__main__":
    enrich_led_zeppelin_albums()
