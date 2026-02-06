#!/usr/bin/env python3
"""Script pour tester la synchronisation Discogs améliorée avec Spotify et IA."""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config import get_settings
from app.services.discogs_service import DiscogsService
from app.services.spotify_service import SpotifyService
from app.services.ai_service import AIService


async def test_enhanced_sync():
    """Tester la synchronisation avec Spotify et IA."""
    
    print("🔧 Chargement de la configuration...")
    settings = get_settings()
    secrets = settings.secrets
    
    # Initialiser les services
    discogs_config = secrets.get('discogs', {})
    spotify_config = secrets.get('spotify', {})
    ai_config = secrets.get('euria', {})
    
    discogs = DiscogsService(
        api_key=discogs_config.get('api_key'),
        username=discogs_config.get('username')
    )
    
    spotify = SpotifyService(
        client_id=spotify_config.get('client_id'),
        client_secret=spotify_config.get('client_secret')
    )
    
    ai = AIService(
        url=ai_config.get('url'),
        bearer=ai_config.get('bearer')
    )
    
    print("\n📀 Récupération d'un album test de Discogs...")
    albums = discogs.get_collection(limit=1)
    
    if not albums:
        print("❌ Aucun album récupéré")
        return
    
    album = albums[0]
    print(f"\n✅ Album récupéré: {album['title']}")
    print(f"   Artiste(s): {', '.join(album['artists'])}")
    print(f"   Année: {album.get('year', 'N/A')}")
    
    # Test Spotify
    print("\n🎵 Test recherche Spotify...")
    try:
        artist_name = album['artists'][0] if album['artists'] else ""
        spotify_url = await spotify.search_album_url(artist_name, album['title'])
        
        if spotify_url:
            print(f"✅ URL Spotify trouvée: {spotify_url}")
        else:
            print("⚠️  Album non trouvé sur Spotify")
    except Exception as e:
        print(f"❌ Erreur Spotify: {e}")
    
    # Test IA
    print("\n🤖 Test génération description IA...")
    try:
        artist_name = album['artists'][0] if album['artists'] else ""
        ai_info = await ai.generate_album_info(artist_name, album['title'])
        
        if ai_info:
            print(f"✅ Description IA générée:")
            print(f"   {ai_info[:200]}...")
        else:
            print("⚠️  Aucune description IA générée")
    except Exception as e:
        print(f"❌ Erreur IA: {e}")
    
    print("\n✅ Test terminé!")


if __name__ == "__main__":
    asyncio.run(test_enhanced_sync())
