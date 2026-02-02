#!/usr/bin/env python3
"""Enrichir les albums sans images avec Spotify"""

import sys
import os
import json
from pathlib import Path

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app.models import Album, Image
from app.services.spotify_service import SpotifyService

def enrich_albums_with_spotify():
    db = SessionLocal()
    
    # Charger les secrets
    secrets_path = Path(__file__).parent / 'config' / 'secrets.json'
    if not secrets_path.exists():
        secrets_path = Path(__file__).parent.parent / 'config' / 'secrets.json'
    
    try:
        with open(secrets_path) as f:
            secrets = json.load(f)
        spotify_config = secrets.get('spotify', {})
        spotify = SpotifyService(
            client_id=spotify_config.get('client_id'),
            client_secret=spotify_config.get('client_secret')
        )
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
    
    for album in albums_no_images:
        try:
            # Récupérer le premier artiste
            artists = [a.name for a in album.artists]
            
            if not artists:
                print('  ⚠️  {} | AUCUN ARTISTE'.format(album.title[:40]))
                fail_count += 1
                continue
            
            artist_name = artists[0]
            
            # Rechercher sur Spotify
            result = spotify.search_album(album.title, artist_name)
            
            if result and result.get('image_url'):
                # Vérifier que l'image n'existe pas déjà
                existing = db.query(Image).filter_by(
                    album_id=album.id,
                    source='spotify'
                ).first()
                
                if not existing:
                    image = Image(
                        album_id=album.id,
                        source='spotify',
                        url=result['image_url']
                    )
                    db.add(image)
                    db.commit()
                    print('  ✅ {} | {} | Image ajoutée'.format(
                        album.id,
                        album.title[:50]
                    ))
                    success_count += 1
                else:
                    print('  ℹ️  {} | {} | Image Spotify déjà présente'.format(
                        album.id,
                        album.title[:50]
                    ))
            else:
                print('  ❌ {} | {} | Pas trouvé sur Spotify'.format(
                    album.id,
                    album.title[:50]
                ))
                fail_count += 1
                
        except Exception as e:
            print('  ⚠️  {} | {} | Erreur: {}'.format(
                album.id,
                album.title[:50],
                str(e)[:40]
            ))
            fail_count += 1
    
    print('\n' + '='*70)
    print('✅ Résultats:')
    print('  - Images Spotify ajoutées: {}'.format(success_count))
    print('  - Problèmes: {}'.format(fail_count))
    print('='*70)
    
    db.close()

if __name__ == '__main__':
    enrich_albums_with_spotify()
