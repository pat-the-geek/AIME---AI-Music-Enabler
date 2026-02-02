#!/usr/bin/env python3
"""Audit complet de la base et enrichissement"""

import sys
sys.path.insert(0, '/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend')

from app.database import SessionLocal
from app.models import Album, Image
from app.services.spotify_service import SpotifyService
from app.services.euria_service import EuriaService
from sqlalchemy import func
import asyncio

async def enrich_albums():
    db = SessionLocal()
    
    # Compter les problèmes
    albums_no_images = db.query(Album).filter(~Album.images.any()).all()
    albums_no_euria = db.query(Album).filter(Album.euria_id == None).all()
    albums_no_artists = db.query(Album).filter(~Album.artists.any()).all()
    
    print('📊 AUDIT COMPLET')
    print('='*60)
    print('Albums à enrichir:')
    print('  - Sans images Spotify: {}'.format(len(albums_no_images)))
    print('  - Sans euriA: {}'.format(len(albums_no_euria)))
    print('  - Sans artistes: {}'.format(len(albums_no_artists)))
    
    total_albums = db.query(func.count(Album.id)).scalar()
    print('\\nTotal albums en base: {}'.format(total_albums))
    
    # Enrichissement
    print('\\n🔄 Enrichissement en cours...')
    
    spotify_service = SpotifyService()
    euria_service = EuriaService()
    
    enriched_count = 0
    error_count = 0
    
    # Enrichir les albums sans images
    for album in albums_no_images[:50]:  # Limiter à 50 pour ne pas surcharger
        try:
            print('\\n  📀 {} ({})'.format(album.title[:40], album.id), end='')
            
            # Chercher sur Spotify
            if album.artists:
                artist_name = album.artists[0].name
                spotify_result = spotify_service.search_album(album.title, artist_name)
                if spotify_result:
                    image_url = spotify_result.get('image_url')
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
                            print(' ✅ Image Spotify ajoutée', end='')
                            enriched_count += 1
        except Exception as e:
            error_count += 1
            print(' ❌ Erreur: {}'.format(str(e)[:30]), end='')
    
    db.commit()
    print('\\n\\n📈 Résultats:')
    print('  - Images Spotify ajoutées: {}'.format(enriched_count))
    print('  - Erreurs: {}'.format(error_count))
    
    db.close()

if __name__ == '__main__':
    asyncio.run(enrich_albums())
