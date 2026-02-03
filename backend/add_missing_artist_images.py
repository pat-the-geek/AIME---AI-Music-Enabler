#!/usr/bin/env python3
"""
Ajouter l'image manquante de Tame Impala
"""
import asyncio
from app.database import SessionLocal
from app.services.spotify_service import SpotifyService
from app.core.config import get_settings
from app.models import Image, Artist

async def add_missing_artist_images():
    settings = get_settings()
    secrets = settings.secrets
    
    spotify = SpotifyService(
        client_id=secrets.get('spotify', {}).get('client_id', ''),
        client_secret=secrets.get('spotify', {}).get('client_secret', '')
    )
    
    db = SessionLocal()
    
    # Trouver tous les artistes sans images
    print("\n🔍 Recherche des artistes sans images...\n")
    
    artists = db.query(Artist).all()
    added_count = 0
    
    for artist in artists:
        # Vérifier si cet artiste a déjà une image
        existing_image = db.query(Image).filter(
            Image.artist_id == artist.id,
            Image.image_type == 'artist'
        ).first()
        
        if not existing_image:
            # Essayer de trouver l'image sur Spotify
            print(f"🔍 Recherche image Spotify pour '{artist.name}'...")
            artist_image = await spotify.search_artist_image(artist.name)
            
            if artist_image:
                img = Image(
                    url=artist_image,
                    image_type='artist',
                    source='spotify',
                    artist_id=artist.id
                )
                db.add(img)
                print(f"   ✅ Image ajoutée: {artist_image[:60]}...")
                added_count += 1
            else:
                print(f"   ❌ Aucune image trouvée")
    
    if added_count > 0:
        db.commit()
        print(f"\n✅ {added_count} images d'artiste ajoutées!")
    else:
        print(f"\n✅ Tous les artistes ont déjà des images!")
    
    db.close()

asyncio.run(add_missing_artist_images())
