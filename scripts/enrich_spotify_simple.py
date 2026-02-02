#!/usr/bin/env python3
"""Enrichir les albums sans images avec Spotify (approche simplifiée)"""

import sys
import os
import json
from pathlib import Path
import httpx

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app.models import Album, Image

def get_spotify_album_image(client_id: str, client_secret: str, album_title: str, artist_name: str) -> str:
    """Rechercher une image d'album sur Spotify via l'API REST"""
    try:
        # Obtenir le token
        auth_response = httpx.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=10
        )
        auth_response.raise_for_status()
        access_token = auth_response.json()["access_token"]
        
        # Rechercher l'album
        search_query = '{} artist:{}'.format(album_title, artist_name)
        search_response = httpx.get(
            "https://api.spotify.com/v1/search",
            params={"q": search_query, "type": "album", "limit": 1},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        search_response.raise_for_status()
        data = search_response.json()
        
        albums = data.get("albums", {}).get("items", [])
        if albums and albums[0].get("images"):
            return albums[0]["images"][0]["url"]
        
        return None
    except Exception as e:
        return None

def main():
    db = SessionLocal()
    
    # Charger les secrets
    secrets_path = Path(__file__).parent.parent / 'config' / 'secrets.json'
    
    try:
        with open(secrets_path) as f:
            secrets = json.load(f)
        spotify_config = secrets.get('spotify', {})
        client_id = spotify_config.get('client_id')
        client_secret = spotify_config.get('client_secret')
    except Exception as e:
        print('❌ Erreur lors du chargement des credentials Spotify: {}'.format(e))
        return
    
    # Trouver les albums sans images
    albums_no_images = db.query(Album).filter(~Album.images.any()).all()
    
    print('\n🎵 ENRICHISSEMENT SPOTIFY')
    print('='*70)
    print('Albums à enrichir: {}'.format(len(albums_no_images)))
    print('='*70)
    
    success_count = 0
    fail_count = 0
    
    for idx, album in enumerate(albums_no_images):
        try:
            artists = [a.name for a in album.artists]
            
            if not artists:
                fail_count += 1
                continue
            
            artist_name = artists[0]
            
            # Rechercher sur Spotify
            image_url = get_spotify_album_image(client_id, client_secret, album.title, artist_name)
            
            if image_url:
                # Vérifier que l'image n'existe pas déjà
                existing = db.query(Image).filter_by(
                    album_id=album.id,
                    source='spotify'
                ).first()
                
                if not existing:
                    image = Image(
                        album_id=album.id,
                        source='spotify',
                        url=image_url
                    )
                    db.add(image)
                    db.commit()
                    print('  ✅ {} | {}'.format(album.id, album.title[:50]))
                    success_count += 1
            else:
                fail_count += 1
        
        except Exception as e:
            fail_count += 1
        
        # Afficher la progression
        if (idx + 1) % 50 == 0:
            print('  ... {} albums traités ({} succès)'.format(idx + 1, success_count))
    
    print('\n' + '='*70)
    print('✅ Résultats:')
    print('  - Images Spotify ajoutées: {}'.format(success_count))
    print('  - Problèmes: {}'.format(fail_count))
    print('='*70)
    
    db.close()

if __name__ == '__main__':
    main()
