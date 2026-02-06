#!/usr/bin/env python3
"""
Ajouter les images manquantes pour The Young Gods (album + artiste)
"""
import asyncio
import sys
sys.path.insert(0, '/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend')

from app.database import SessionLocal
from app.services.spotify_service import SpotifyService
from app.core.config import get_settings
from app.models import Album, Artist, Image, album_artist
from sqlalchemy.orm import joinedload

async def add_young_gods_images():
    settings = get_settings()
    secrets = settings.secrets
    
    spotify = SpotifyService(
        client_id=secrets.get('spotify', {}).get('client_id', ''),
        client_secret=secrets.get('spotify', {}).get('client_secret', '')
    )
    
    db = SessionLocal()
    
    # Trouver The Young Gods
    print("\n🔍 Recherche des albums The Young Gods...\n")
    
    artist = db.query(Artist).filter(Artist.name == 'The Young Gods').first()
    if not artist:
        print("❌ The Young Gods non trouvés!")
        db.close()
        return
    
    print(f"✅ Artiste trouvé: {artist.name} (ID: {artist.id})\n")
    
    # PARTIE 1: Ajouter images d'albums manquantes
    albums_without_images = db.query(Album).join(album_artist).options(
        joinedload(Album.artists)
    ).filter(
        album_artist.c.artist_id == artist.id,
        (Album.image_url.is_(None)) | (Album.image_url == '')
    ).all()
    
    print(f"📀 {len(albums_without_images)} albums sans images trouvés\n")
    
    album_added_count = 0
    album_failed_count = 0
    
    for idx, album in enumerate(albums_without_images, 1):
        print(f"[{idx}/{len(albums_without_images)}] 🔍 Album: {album.title}")
        
        # Essayer de trouver l'image sur Spotify
        image_url = await spotify.search_album_image('The Young Gods', album.title)
        
        if image_url:
            album.image_url = image_url
            db.commit()
            print(f"   ✅ Image album ajoutée: {image_url[:60]}...")
            album_added_count += 1
        else:
            print(f"   ❌ Aucune image album trouvée")
            album_failed_count += 1
    
    # PARTIE 2: Ajouter image d'artiste manquante (BUG FIX!)
    print(f"\n{'='*60}\n🎤 Vérification image d'artiste...\n")
    
    existing_artist_image = db.query(Image).filter(
        Image.artist_id == artist.id,
        Image.image_type == 'artist'
    ).first()
    
    if existing_artist_image:
        print(f"✅ Image d'artiste déjà présente: {existing_artist_image.url[:60]}...")
    else:
        print(f"❌ Pas d'image d'artiste trouvée!")
        print(f"🔍 Recherche image Spotify pour '{artist.name}'...\n")
        
        artist_image = await spotify.search_artist_image(artist.name)
        
        if artist_image:
            img = Image(
                url=artist_image,
                image_type='artist',
                source='spotify',
                artist_id=artist.id
            )
            db.add(img)
            db.commit()
            print(f"✅ Image d'artiste ajoutée: {artist_image[:60]}...\n")
        else:
            print(f"❌ Aucune image d'artiste trouvée sur Spotify\n")
    
    print(f"\n{'='*60}")
    print(f"✅ {album_added_count} images d'album The Young Gods ajoutées!")
    if album_failed_count > 0:
        print(f"❌ {album_failed_count} albums sans image trouvée")
    print(f"{'='*60}\n")
    
    db.close()

asyncio.run(add_young_gods_images())
