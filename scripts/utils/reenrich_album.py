#!/usr/bin/env python3
"""Ré-enrichir l'album avec la bonne image."""
import sys
import os
import asyncio
import json
from pathlib import Path

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app.models import Album, Image
from app.services.spotify_service import SpotifyService

async def reenrich_album():
    db = SessionLocal()
    
    try:
        # Charger les secrets
        secrets_path = Path(__file__).parent.parent / 'config' / 'secrets.json'
        with open(secrets_path) as f:
            secrets = json.load(f)
        
        spotify_config = secrets.get('spotify', {})
        spotify_service = SpotifyService(
            client_id=spotify_config.get('client_id'),
            client_secret=spotify_config.get('client_secret')
        )
        
        # Récupérer l'album
        album = db.query(Album).filter_by(title="More Songs About Buildings and Food").first()
        
        if not album:
            print("❌ Album non trouvé")
            return
        
        print(f"\n📀 Album: {album.title}")
        print(f"   🎤 Artistes: {[a.name for a in album.artists]}")
        print(f"   🖼️  Images actuelles: {len(album.images)}")
        
        # Chercher la bonne image sur Spotify
        artist = album.artists[0].name if album.artists else "Unknown"
        image_url = await spotify_service.search_album_image(artist, album.title)
        
        if image_url:
            print(f"\n✅ Image Spotify trouvée:")
            print(f"   {image_url}")
            
            # Vérifier si cette image existe déjà
            existing = db.query(Image).filter_by(
                album_id=album.id,
                source='spotify',
                url=image_url
            ).first()
            
            if not existing:
                # Ajouter l'image
                img = Image(
                    url=image_url,
                    image_type='album',
                    source='spotify',
                    album_id=album.id
                )
                db.add(img)
                db.commit()
                print(f"✅ Image ajoutée à l'album!")
            else:
                print(f"ℹ️  Image déjà présente")
        else:
            print(f"\n❌ Aucune image trouvée sur Spotify")
        
        print(f"\n📊 Images finales: {len(album.images)}")
        for img in album.images:
            print(f"   - {img.source}: {img.url[:80]}...")
        
    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(reenrich_album())
