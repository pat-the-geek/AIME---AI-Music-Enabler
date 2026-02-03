#!/usr/bin/env python3
"""Test de récupération des images pour Durand Bernarr / BLOOM"""

import sys
import os
import asyncio
from pathlib import Path

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app.models import Artist, Album, Image
from app.services.spotify_service import SpotifyService
from app.core.config import get_settings


async def test_durand_bernarr():
    """Tester la récupération d'images pour Durand Bernarr"""
    
    settings = get_settings()
    secrets = settings.secrets
    
    # Initialiser Spotify
    spotify = SpotifyService(
        client_id=secrets.get('spotify', {}).get('client_id', ''),
        client_secret=secrets.get('spotify', {}).get('client_secret', '')
    )
    
    db = SessionLocal()
    
    try:
        # 1. Tester la recherche directe sur Spotify
        print("\n" + "="*70)
        print("🔍 TEST RECHERCHE SPOTIFY DIRECTE")
        print("="*70)
        
        artist_name = "Durand Bernarr"
        album_title = "BLOOM"
        
        print(f"\n🎤 Recherche artiste '{artist_name}'...")
        artist_image = await spotify.search_artist_image(artist_name)
        if artist_image:
            print(f"✅ Image artiste trouvée: {artist_image}")
        else:
            print(f"❌ Aucune image artiste trouvée")
        
        print(f"\n📀 Recherche album '{album_title}' par '{artist_name}'...")
        album_details = await spotify.search_album_details(artist_name, album_title)
        if album_details:
            print(f"✅ Album trouvé:")
            print(f"   - URL: {album_details.get('spotify_url')}")
            print(f"   - Année: {album_details.get('year')}")
            print(f"   - Image: {album_details.get('image_url')}")
        else:
            print(f"❌ Aucun album trouvé")
        
        # 2. Vérifier l'état dans la base de données
        print("\n" + "="*70)
        print("🗄️ ÉTAT ACTUEL DANS LA BASE DE DONNÉES")
        print("="*70)
        
        artist = db.query(Artist).filter_by(name=artist_name).first()
        if artist:
            print(f"\n🎤 Artiste trouvé (ID: {artist.id})")
            artist_images = db.query(Image).filter_by(
                artist_id=artist.id,
                image_type='artist'
            ).all()
            print(f"   - Images: {len(artist_images)}")
            for img in artist_images:
                print(f"     • {img.source}: {img.url}")
        else:
            print(f"\n❌ Artiste '{artist_name}' non trouvé en base")
        
        album = db.query(Album).filter(
            Album.title == album_title,
            Album.artists.any(Artist.name == artist_name)
        ).first()
        
        if album:
            print(f"\n📀 Album trouvé (ID: {album.id})")
            print(f"   - URL Spotify: {album.spotify_url or 'Aucune'}")
            print(f"   - Année: {album.year or 'Inconnue'}")
            album_images = db.query(Image).filter_by(
                album_id=album.id,
                image_type='album'
            ).all()
            print(f"   - Images: {len(album_images)}")
            for img in album_images:
                print(f"     • {img.source}: {img.url}")
        else:
            print(f"\n❌ Album '{album_title}' non trouvé en base")
        
        # 3. Simuler l'enrichissement automatique
        print("\n" + "="*70)
        print("🔄 SIMULATION ENRICHISSEMENT AUTOMATIQUE")
        print("="*70)
        
        if artist and album:
            # Enrichir l'artiste si nécessaire
            has_artist_image = db.query(Image).filter_by(
                artist_id=artist.id,
                image_type='artist'
            ).first() is not None
            
            if not has_artist_image:
                print(f"\n🎤 Enrichissement artiste '{artist_name}'...")
                artist_image = await spotify.search_artist_image(artist_name)
                if artist_image:
                    img = Image(
                        url=artist_image,
                        image_type='artist',
                        source='spotify',
                        artist_id=artist.id
                    )
                    db.add(img)
                    db.commit()
                    print(f"✅ Image artiste ajoutée!")
                else:
                    print(f"❌ Impossible de trouver l'image")
            else:
                print(f"\n✓ Artiste possède déjà une image")
            
            # Enrichir l'album si nécessaire
            has_album_image = db.query(Image).filter_by(
                album_id=album.id,
                image_type='album',
                source='spotify'
            ).first() is not None
            
            if not has_album_image or not album.spotify_url:
                print(f"\n📀 Enrichissement album '{album_title}'...")
                album_details = await spotify.search_album_details(artist_name, album_title)
                if album_details:
                    if not album.spotify_url and album_details.get("spotify_url"):
                        album.spotify_url = album_details["spotify_url"]
                        print(f"✅ URL Spotify ajoutée: {album.spotify_url}")
                    
                    if not album.year and album_details.get("year"):
                        album.year = album_details["year"]
                        print(f"✅ Année ajoutée: {album.year}")
                    
                    if not has_album_image and album_details.get("image_url"):
                        img = Image(
                            url=album_details["image_url"],
                            image_type='album',
                            source='spotify',
                            album_id=album.id
                        )
                        db.add(img)
                        print(f"✅ Image album ajoutée!")
                    
                    db.commit()
                else:
                    print(f"❌ Impossible de trouver les détails de l'album")
            else:
                print(f"\n✓ Album possède déjà une image et une URL Spotify")
        
        # 4. Afficher l'état final
        print("\n" + "="*70)
        print("📊 ÉTAT FINAL")
        print("="*70)
        
        if artist:
            artist_images = db.query(Image).filter_by(
                artist_id=artist.id,
                image_type='artist'
            ).all()
            print(f"\n🎤 Artiste: {artist.name}")
            print(f"   - Images: {len(artist_images)}")
        
        if album:
            album_images = db.query(Image).filter_by(
                album_id=album.id,
                image_type='album'
            ).all()
            print(f"\n📀 Album: {album.title}")
            print(f"   - URL Spotify: {album.spotify_url or 'Aucune'}")
            print(f"   - Année: {album.year or 'Inconnue'}")
            print(f"   - Images: {len(album_images)}")
        
        print("\n" + "="*70)
        
    finally:
        db.close()


if __name__ == '__main__':
    asyncio.run(test_durand_bernarr())
