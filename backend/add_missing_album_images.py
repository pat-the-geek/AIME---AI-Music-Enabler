#!/usr/bin/env python3
"""
Ajouter les images manquantes à tous les albums via Spotify
"""
import asyncio
import sys
sys.path.insert(0, '/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend')

from app.database import SessionLocal
from app.services.spotify_service import SpotifyService
from app.services.lastfm_image_service import LastFMImageService
from app.core.config import get_settings
from app.models import Album, Artist, album_artist
from sqlalchemy.orm import joinedload

async def add_missing_album_images():
    settings = get_settings()
    secrets = settings.secrets
    
    spotify = SpotifyService(
        client_id=secrets.get('spotify', {}).get('client_id', ''),
        client_secret=secrets.get('spotify', {}).get('client_secret', '')
    )
    lastfm = LastFMImageService(api_key=secrets.get('lastfm', {}).get('api_key', ''))
    
    db = SessionLocal()
    
    # Trouver tous les albums sans images
    print("\n🔍 Recherche des albums sans images...\n")
    
    albums_without_images = db.query(Album).options(
        joinedload(Album.artists)
    ).filter(
        (Album.image_url.is_(None)) | (Album.image_url == '')
    ).all()
    
    print(f"📀 {len(albums_without_images)} albums sans images trouvés")
    
    added_count = 0
    failed_count = 0
    
    for idx, album in enumerate(albums_without_images, 1):
        artist_name = album.artists[0].name if album.artists else "Unknown"
        print(f"\n[{idx}/{len(albums_without_images)}] 🔍 {artist_name} - {album.title}")
        image_url = None
        if settings.image_album_source == "lastfm":
            image_url = await lastfm.get_album_image(artist_name, album.title)
            source_label = "Last.fm"
        else:
            image_url = await spotify.search_album_image(artist_name, album.title)
            source_label = "Spotify"
        if image_url:
            album.image_url = image_url
            db.commit()
            print(f"   ✅ Image ajoutée ({source_label}): {image_url[:60]}...")
            added_count += 1
        else:
            print(f"   ❌ Aucune image trouvée sur {source_label}")
            failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ {added_count} images d'album ajoutées!")
    print(f"❌ {failed_count} albums sans image trouvée")
    print(f"{'='*60}\n")
    
    db.close()

asyncio.run(add_missing_album_images())
