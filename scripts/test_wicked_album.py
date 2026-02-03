#!/usr/bin/env python3
"""Test de recherche de l'album Wicked sur Spotify"""

import sys
import os
import asyncio
from pathlib import Path

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

from app.services.spotify_service import SpotifyService
from app.core.config import get_settings


async def test_wicked_search():
    """Tester la recherche de l'album Wicked"""
    
    settings = get_settings()
    secrets = settings.secrets
    
    # Initialiser Spotify
    spotify = SpotifyService(
        client_id=secrets.get('spotify', {}).get('client_id', ''),
        client_secret=secrets.get('spotify', {}).get('client_secret', '')
    )
    
    print("\n" + "="*80)
    print("🔍 TEST RECHERCHE ALBUM WICKED SUR SPOTIFY")
    print("="*80)
    
    # Titre exact tel qu'il apparaît probablement dans Roon
    test_cases = [
        ("Various Artists", "Wicked: One Wonderful Night (Live) – The Soundtrack"),
        ("Various Artists", "Wicked: One Wonderful Night (Live) - The Soundtrack"),
        ("Various Artists", "Wicked One Wonderful Night Live The Soundtrack"),
        ("Original Cast", "Wicked: One Wonderful Night (Live) – The Soundtrack"),
        ("Wicked Cast", "Wicked: One Wonderful Night (Live) – The Soundtrack"),
        ("Stephen Schwartz", "Wicked: One Wonderful Night (Live) – The Soundtrack"),
    ]
    
    for artist_name, album_title in test_cases:
        print(f"\n{'─'*80}")
        print(f"🎤 Artiste: {artist_name}")
        print(f"📀 Album: {album_title}")
        print(f"{'─'*80}")
        
        try:
            # Test avec search_album_details
            details = await spotify.search_album_details(artist_name, album_title)
            if details:
                print(f"✅ TROUVÉ avec search_album_details!")
                print(f"   - URL: {details.get('spotify_url')}")
                print(f"   - Année: {details.get('year')}")
                print(f"   - Image: {details.get('image_url')[:80]}..." if details.get('image_url') else None)
            else:
                print(f"❌ NON TROUVÉ avec search_album_details")
            
            # Test avec search_album_image
            image = await spotify.search_album_image(artist_name, album_title)
            if image:
                print(f"✅ TROUVÉ avec search_album_image!")
                print(f"   - Image: {image[:80]}...")
            else:
                print(f"❌ NON TROUVÉ avec search_album_image")
                
        except Exception as e:
            print(f"❌ ERREUR: {e}")
    
    # Test avec l'ID Spotify direct
    print(f"\n{'='*80}")
    print(f"🔗 TEST AVEC ID SPOTIFY DIRECT")
    print(f"{'='*80}")
    
    album_id = "39ixJY2rOByyed4OmCmAe2"
    print(f"\nID Spotify: {album_id}")
    
    try:
        import httpx
        token = await spotify._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{spotify.api_base_url}/albums/{album_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"\n✅ Album trouvé par ID:")
            print(f"   - Nom: {data.get('name')}")
            print(f"   - Artistes: {[a['name'] for a in data.get('artists', [])]}")
            print(f"   - Année: {data.get('release_date', '')[:4]}")
            print(f"   - URL: {data.get('external_urls', {}).get('spotify')}")
            print(f"   - Image: {data.get('images', [{}])[0].get('url', 'N/A')[:80]}...")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    asyncio.run(test_wicked_search())
