#!/usr/bin/env python3
"""Audit et enrichissement des données importées"""

import sys
sys.path.insert(0, '/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend')

from app.database import SessionLocal
from app.models import Album, Image
from sqlalchemy import func

def run_audit():
    db = SessionLocal()
    
    # Statistiques globales
    total_albums = db.query(func.count(Album.id)).scalar()
    albums_with_images = db.query(func.count(Album.id)).filter(Album.images.any()).scalar()
    albums_no_images = total_albums - albums_with_images
    albums_no_artists = db.query(func.count(Album.id)).filter(~Album.artists.any()).scalar()
    
    print('\n📊 AUDIT COMPLET DE LA BASE')
    print('='*70)
    print('Total albums: {}'.format(total_albums))
    print('Albums avec images: {}/{}'.format(albums_with_images, total_albums))
    print('Albums sans images: {}'.format(albums_no_images))
    print('Albums sans artistes: {}'.format(albums_no_artists))
    
    # Albums récents
    print('\n📀 Derniers albums (20 plus récents):')
    print('='*70)
    recent = db.query(Album).order_by(Album.id.desc()).limit(20).all()
    
    problems = []
    for album in recent:
        images = len(album.images)
        artists = [a.name for a in album.artists]
        artist_str = ', '.join(artists) if artists else '⚠️ AUCUN'
        
        line = '  ID {}: {} | Artistes: {} | Images: {}'.format(
            album.id,
            album.title[:35].ljust(35),
            artist_str[:30].ljust(30),
            images
        )
        print(line)
        
        if not artists or images == 0:
            problems.append(album)
    
    print('\n⚠️  PROBLÈMES DÉTECTÉS:')
    print('='*70)
    print('Albums à enrichir: {}'.format(len(problems)))
    
    if problems:
        print('\nDétails:')
        for album in problems:
            issues = []
            if not album.artists:
                issues.append('artistes manquants')
            if len(album.images) == 0:
                issues.append('pas d\'image')
            print('  - {} | {}'.format(album.title[:40], ', '.join(issues)))
    
    db.close()
    return problems

if __name__ == '__main__':
    problems = run_audit()
    print('\n' + '='*70)
    print('✅ Audit terminé')
