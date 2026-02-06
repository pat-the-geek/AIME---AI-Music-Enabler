#!/usr/bin/env python3
"""Scheduler pour amélioration automatique périodique des données"""

import sys
import os
import schedule
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal
from app.models import Album, Image
from sqlalchemy import func

def daily_data_improvement():
    """Exécuter le pipeline d'amélioration quotidiennement"""
    print('\n' + '='*70)
    print('📅 AMÉLIORATION QUOTIDIENNE - {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M')))
    print('='*70)
    
    db = SessionLocal()
    
    try:
        # 1. Compter les albums à améliorer
        total = db.query(func.count(Album.id)).scalar()
        no_images = db.query(func.count(Album.id)).filter(~Album.images.any()).scalar()
        no_description = db.query(func.count(Album.id)).filter(Album.ai_description == None).scalar()
        no_genre = db.query(func.count(Album.id)).filter(Album.genre == None).scalar()
        
        print('\n📊 Statistiques:')
        print('  Total albums: {}'.format(total))
        print('  Sans images: {} ({:.0f}%)'.format(no_images, 100*no_images/total if total > 0 else 0))
        print('  Sans description: {} ({:.0f}%)'.format(no_description, 100*no_description/total if total > 0 else 0))
        print('  Sans genre: {} ({:.0f}%)'.format(no_genre, 100*no_genre/total if total > 0 else 0))
        
        # 2. Exécuter les améliorations
        print('\n🔄 Exécution des améliorations:')
        
        # Enrichir les images
        improved = 0
        albums_no_img = db.query(Album).filter(~Album.images.any()).limit(50).all()
        
        for album in albums_no_img:
            # Essayer d'ajouter une image
            if _try_add_image(db, album):
                improved += 1
                print('  ✅ Image ajoutée: {}'.format(album.title[:40]))
        
        print('\n  ✅ Images ajoutées: {}/{}'.format(improved, len(albums_no_img)))
        
    except Exception as e:
        print('❌ Erreur: {}'.format(str(e)))
    
    finally:
        db.close()

def _try_add_image(db, album: Album) -> bool:
    """Essayer d'ajouter une image à un album"""
    try:
        import httpx
        
        if not album.artists:
            return False
        
        artist_name = album.artists[0].name
        
        # Essayer MusicBrainz
        headers = {'User-Agent': 'AIMusic/1.0'}
        response = httpx.get(
            'https://musicbrainz.org/ws/2/release',
            params={
                'query': '{} {}'.format(album.title, artist_name),
                'limit': 1,
                'fmt': 'json'
            },
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('releases'):
                release_id = data['releases'][0].get('id')
                if release_id:
                    cover_response = httpx.get(
                        'https://coverartarchive.org/release/{}/front'.format(release_id),
                        timeout=5
                    )
                    if cover_response.status_code == 200:
                        image = Image(
                            album_id=album.id,
                            source='musicbrainz',
                            url=str(cover_response.url)
                        )
                        db.add(image)
                        db.commit()
                        return True
    except:
        pass
    
    return False

def schedule_improvements():
    """Planifier les améliorations automatiques"""
    
    # Exécuter chaque jour à 02:00 du matin
    schedule.every().day.at("02:00").do(daily_data_improvement)
    
    print('✅ Scheduler configuré:')
    print('  • Amélioration quotidienne à 02:00')
    print('  • Enrichissement images via MusicBrainz')
    print('  • Vérification de la qualité des données')
    
    # Boucle de scheduler
    print('\n🚀 Scheduler démarré. Appuyer sur Ctrl+C pour arrêter.\n')
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    try:
        schedule_improvements()
    except KeyboardInterrupt:
        print('\n\n✅ Scheduler arrêté')
