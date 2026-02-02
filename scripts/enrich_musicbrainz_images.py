#!/usr/bin/env python3
"""Enrichir les albums sans images via MusicBrainz"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal
from app.models import Album, Image
import httpx
import time

def get_musicbrainz_album_image(album_title: str, artist_name: str) -> str:
    """Rechercher une image d'album sur MusicBrainz"""
    try:
        # MusicBrainz API ne retourne pas les images directement
        # Mais nous pouvons chercher les 'coverartarchive.org' images
        search_query = '{} {}'.format(album_title, artist_name)
        
        # Rechercher sur MusicBrainz
        headers = {'User-Agent': 'AIMusic/1.0'}
        response = httpx.get(
            'https://musicbrainz.org/ws/2/release',
            params={'query': search_query, 'limit': 1, 'fmt': 'json'},
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('releases') and len(data['releases']) > 0:
            release = data['releases'][0]
            release_id = release.get('id')
            
            if release_id:
                # Chercher l'image via Cover Art Archive
                try:
                    cover_response = httpx.get(
                        'https://coverartarchive.org/release/{}/front'.format(release_id),
                        timeout=5
                    )
                    if cover_response.status_code == 200:
                        return cover_response.url
                except:
                    pass
        
        return None
    except Exception as e:
        return None

def main():
    db = SessionLocal()
    
    # Trouver les albums sans images
    albums_no_images = db.query(Album).filter(~Album.images.any()).all()
    
    print('\n🎵 ENRICHISSEMENT MUSICBRAINZ')
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
            
            # Rechercher sur MusicBrainz
            image_url = get_musicbrainz_album_image(album.title, artist_name)
            
            if image_url:
                # Vérifier que l'image n'existe pas déjà
                existing = db.query(Image).filter_by(
                    album_id=album.id,
                    source='musicbrainz'
                ).first()
                
                if not existing:
                    image = Image(
                        album_id=album.id,
                        source='musicbrainz',
                        url=image_url
                    )
                    db.add(image)
                    db.commit()
                    print('  ✅ {} | {}'.format(album.id, album.title[:50]))
                    success_count += 1
                    
                    # Rate limiting
                    time.sleep(0.5)
            else:
                fail_count += 1
        
        except Exception as e:
            fail_count += 1
        
        # Afficher la progression
        if (idx + 1) % 100 == 0:
            print('  ... {} albums traités ({} succès)'.format(idx + 1, success_count))
    
    print('\n' + '='*70)
    print('✅ Résultats:')
    print('  - Images MusicBrainz ajoutées: {}'.format(success_count))
    print('  - Échecs: {}'.format(fail_count))
    print('='*70)
    
    db.close()

if __name__ == '__main__':
    main()
