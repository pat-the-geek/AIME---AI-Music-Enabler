#!/usr/bin/env python3
"""Vérifier et enrichir les imports du jour"""

import sys
sys.path.insert(0, '/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend')

from app.database import SessionLocal
from app.models import ListeningHistory, Album, Artist, Track, Image
from app.services.spotify_service import SpotifyService
from datetime import datetime, timedelta
from sqlalchemy import desc

def check_todays_imports():
    db = SessionLocal()
    
    # Imports d'aujourd'hui (2 février 2026)
    today = datetime(2026, 2, 2)
    tomorrow = today + timedelta(days=1)
    
    imports_today = db.query(ListeningHistory).filter(
        ListeningHistory.timestamp >= today,
        ListeningHistory.timestamp < tomorrow
    ).order_by(desc(ListeningHistory.timestamp)).all()
    
    print('📊 Imports du 2 février 2026: {} scrobbles\n'.format(len(imports_today)))
    
    if not imports_today:
        print('❌ Aucun import trouvé pour aujourd\'hui')
        db.close()
        return
    
    # Vérifier les albums
    albums_info = {}
    for lh in imports_today:
        if lh.album_id:
            if lh.album_id not in albums_info:
                albums_info[lh.album_id] = {
                    'album': lh.album,
                    'count': 0,
                    'artists': [],
                    'images': 0,
                    'has_euria': False
                }
            albums_info[lh.album_id]['count'] += 1
            if lh.album:
                albums_info[lh.album_id]['artists'] = [a.name for a in lh.album.artists]
                albums_info[lh.album_id]['images'] = len(lh.album.images)
                albums_info[lh.album_id]['has_euria'] = lh.album.euria_id is not None
    
    print('📀 Albums importés: {}\n'.format(len(albums_info)))
    
    # Afficher l'état de chaque album
    albums_to_enrich = []
    for album_id, info in sorted(albums_info.items(), key=lambda x: x[1]['count'], reverse=True):
        album = info['album']
        print('  Album: {} (ID: {})'.format(album.title, album.id))
        print('    - Artistes: {}'.format(', '.join(info['artists']) if info['artists'] else 'AUCUN'))
        print('    - Images: {} | euriA: {}'.format(
            info['images'],
            '✅' if info['has_euria'] else '❌'
        ))
        
        # Vérifier les problèmes
        problems = []
        if not info['artists']:
            problems.append('ARTISTES MANQUANTS')
        if info['images'] == 0:
            problems.append('PAS D\'IMAGE')
        if not info['has_euria']:
            problems.append('EURIA MANQUANT')
        
        if problems:
            print('    ⚠️  PROBLÈMES: ' + ', '.join(problems))
            albums_to_enrich.append(album)
        
        print()
    
    db.close()
    return albums_to_enrich

if __name__ == '__main__':
    albums_to_enrich = check_todays_imports()
    print('\n' + '='*60)
    print('Albums à enrichir: {}'.format(len(albums_to_enrich)))
