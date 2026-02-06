#!/usr/bin/env python3
"""Rapport d'audit complet avec recommandations"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal
from app.models import Album, Image, Track
from sqlalchemy import func
from datetime import datetime

def generate_audit_report():
    db = SessionLocal()
    
    # Statistiques globales
    total_albums = db.query(func.count(Album.id)).scalar()
    total_tracks = db.query(func.count(Track.id)).scalar()
    
    albums_with_images = db.query(func.count(Album.id)).filter(Album.images.any()).scalar()
    albums_no_images = total_albums - albums_with_images
    
    albums_with_tracks = db.query(func.count(Album.id)).filter(Album.tracks.any()).scalar()
    albums_no_tracks = total_albums - albums_with_tracks
    
    albums_no_artists = db.query(func.count(Album.id)).filter(~Album.artists.any()).scalar()
    
    # Par source
    albums_by_source = db.query(Album.source, func.count(Album.id)).group_by(Album.source).all()
    
    print('\n' + '='*80)
    print('📊 RAPPORT D\'AUDIT - BASE DE DONNÉES MUSIQUE')
    print('='*80)
    print('Date: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print()
    
    print('📈 STATISTIQUES GLOBALES')
    print('-'*80)
    print('Total albums: {:>6} | Total pistes: {:>6}'.format(total_albums, total_tracks))
    print('Albums avec images: {:>4}/{:<4} ({:>5.1f}%)'.format(
        albums_with_images, total_albums, 100*albums_with_images/total_albums if total_albums > 0 else 0
    ))
    print('Albums avec pistes: {:>4}/{:<4} ({:>5.1f}%)'.format(
        albums_with_tracks, total_albums, 100*albums_with_tracks/total_albums if total_albums > 0 else 0
    ))
    print()
    
    print('⚠️  PROBLÈMES DÉTECTÉS')
    print('-'*80)
    print('Albums sans images: {:>5} ({:>5.1f}%)'.format(
        albums_no_images, 100*albums_no_images/total_albums if total_albums > 0 else 0
    ))
    print('Albums sans artistes: {:>3} ({:>5.1f}%)'.format(
        albums_no_artists, 100*albums_no_artists/total_albums if total_albums > 0 else 0
    ))
    print('Albums sans pistes: {:>5} ({:>5.1f}%)'.format(
        albums_no_tracks, 100*albums_no_tracks/total_albums if total_albums > 0 else 0
    ))
    print()
    
    print('🏷️  ALBUMS PAR SOURCE')
    print('-'*80)
    for source, count in sorted(albums_by_source, key=lambda x: x[1], reverse=True):
        pct = 100*count/total_albums if total_albums > 0 else 0
        print('  {:<15} {:>6} ({:>5.1f}%)'.format(source, count, pct))
    print()
    
    # Images par source
    print('🖼️  IMAGES PAR SOURCE')
    print('-'*80)
    image_sources = db.query(Image.source, func.count(Image.id)).group_by(Image.source).all()
    total_images = sum(count for _, count in image_sources)
    for source, count in sorted(image_sources, key=lambda x: x[1], reverse=True):
        pct = 100*count/total_images if total_images > 0 else 0
        print('  {:<15} {:>6} ({:>5.1f}%)'.format(source, count, pct))
    print()
    
    # Albums sans images - grouper par source
    print('🎯 ALBUMS SANS IMAGES - PAR SOURCE')
    print('-'*80)
    albums_no_img_by_source = db.query(
        Album.source, func.count(Album.id)
    ).filter(~Album.images.any()).group_by(Album.source).all()
    
    for source, count in sorted(albums_no_img_by_source, key=lambda x: x[1], reverse=True):
        pct = 100*count/albums_no_images if albums_no_images > 0 else 0
        print('  {:<15} {:>6} ({:>5.1f}% des albums sans images)'.format(source, count, pct))
    print()
    
    # Albums récents sans images
    print('📀 DERNIERS ALBUMS SANS IMAGES (20 plus récents)')
    print('-'*80)
    recent_no_img = db.query(Album).filter(~Album.images.any()).order_by(Album.id.desc()).limit(20).all()
    for album in recent_no_img:
        artists = ', '.join([a.name for a in album.artists]) if album.artists else 'AUCUN'
        print('  ID {:<4} | {:<50} | {:<30}'.format(
            album.id, album.title[:48], artists[:28]
        ))
    print()
    
    print('='*80)
    print('💡 RECOMMANDATIONS')
    print('='*80)
    print('''
1. ✅ Images Spotify: {} albums pourraient être enrichis via Spotify Search
   -> Ces albums n'ont PAS d'image dans la base

2. 📋 Données complètes: Auditer les albums sans artistes ({} albums)
   -> Potentiellement des erreurs d'import

3. 🔄 Traçabilité: Vérifier les albums d'autres sources (Roon, Spotify)
   -> Source LastFM: {} albums sans images
   -> Source Discogs: {} albums sans images

4. 🎯 Priorités:
   - Corriger les problèmes de données d'abord
   - Enrichir avec Spotify ensuite (si l'album est trouvé)
   - Garder les images existantes intactes
'''.format(
        albums_no_images,
        albums_no_artists,
        db.query(func.count(Album.id)).filter(
            (Album.source == 'lastfm') & (~Album.images.any())
        ).scalar(),
        db.query(func.count(Album.id)).filter(
            (Album.source == 'discogs') & (~Album.images.any())
        ).scalar()
    ))
    
    print('='*80)
    
    db.close()

if __name__ == '__main__':
    generate_audit_report()
