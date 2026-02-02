#!/usr/bin/env python3
"""Validation et correction des données importées"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal
from app.models import Album, Artist, Track, ListeningHistory
from sqlalchemy import and_, func
from datetime import datetime, timedelta

def validate_and_correct():
    db = SessionLocal()
    
    print('\n' + '='*80)
    print('🔍 VALIDATION ET CORRECTION DES DONNÉES')
    print('='*80)
    print('Date: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print()
    
    corrections_count = 0
    issues = []
    
    # 1. Vérifier les albums avec des artistes mal formés
    print('1️⃣  Vérification des artistes...')
    albums = db.query(Album).all()
    for album in albums:
        if album.artists:
            # Vérifier qu'aucun artiste ne contient de séparateur duplicaté
            for artist in album.artists:
                if ',' in artist.name or ' & ' in artist.name:
                    if artist.name.count(',') > 1 or artist.name.count(' & ') > 1:
                        issues.append('  ⚠️  Album {} | Artiste mal formaté: {}'.format(
                            album.id, artist.name
                        ))
    
    if not issues:
        print('   ✅ Tous les artistes sont bien formés')
    else:
        for issue in issues[:10]:
            print(issue)
    
    # 2. Vérifier les doublons d'albums
    print('\n2️⃣  Vérification des doublons...')
    duplicate_titles = db.query(
        Album.title, func.count(Album.id)
    ).group_by(Album.title).having(func.count(Album.id) > 1).all()
    
    if duplicate_titles:
        print('   ⚠️  Albums avec titres identiques:')
        for title, count in duplicate_titles[:5]:
            print('       {} | {} copies'.format(title[:50], count))
    else:
        print('   ✅ Pas de doublons détectés')
    
    # 3. Vérifier les pistes orphelines (sans album)
    print('\n3️⃣  Vérification des pistes orphelines...')
    orphan_tracks = db.query(func.count(Track.id)).filter(Track.album_id == None).scalar()
    if orphan_tracks > 0:
        print('   ⚠️  {} pistes sans album'.format(orphan_tracks))
    else:
        print('   ✅ Toutes les pistes ont un album')
    
    # 4. Vérifier les problèmes d'historique
    print('\n4️⃣  Vérification de l\'historique d\'écoute...')
    
    # Albums scrobblés
    total_history = db.query(func.count(ListeningHistory.id)).scalar()
    unique_tracks = db.query(func.distinct(ListeningHistory.track_id)).count()
    
    print('   ✅ {} scrobbles | {} pistes écoutées'.format(total_history, unique_tracks))
    
    # Vérifier les imports aujourd'hui
    today = datetime.now().date()
    today_imports = db.query(func.count(ListeningHistory.id)).scalar()
    
    print('   📊 Total scrobbles en base: {}'.format(today_imports))
    
    # 5. Résumé des données
    print('\n5️⃣  RÉSUMÉ DES DONNÉES')
    print('-'*80)
    
    total_albums = db.query(func.count(Album.id)).scalar()
    total_artists = db.query(func.count(Artist.id)).scalar()
    total_tracks = db.query(func.count(Track.id)).scalar()
    total_history = db.query(func.count(ListeningHistory.id)).scalar()
    
    print('  Albums: {} | Artistes: {} | Pistes: {} | Historique: {}'.format(
        total_albums, total_artists, total_tracks, total_history
    ))
    
    # Statistiques par artiste (top 5)
    print('\n6️⃣  TOP ARTISTES')
    print('-'*80)
    top_artists = db.query(
        Artist.name, func.count(Album.id)
    ).join(Album.artists).group_by(Artist.name).order_by(
        func.count(Album.id).desc()
    ).limit(5).all()
    
    for idx, (artist_name, count) in enumerate(top_artists, 1):
        print('  {}. {} | {} albums'.format(idx, artist_name[:50], count))
    
    print('\n' + '='*80)
    print('✅ VALIDATION TERMINÉE')
    print('='*80)
    
    db.close()

if __name__ == '__main__':
    validate_and_correct()
