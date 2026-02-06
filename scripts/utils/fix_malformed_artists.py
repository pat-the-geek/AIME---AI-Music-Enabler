#!/usr/bin/env python3
"""Corriger les artistes mal formatés (collaborations)"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal
from app.models import Album, Artist
from sqlalchemy import and_

def fix_malformed_artists():
    """Séparer les artistes dans un seul champ en plusieurs artistes"""
    db = SessionLocal()
    
    print('\n🎤 CORRECTION DES ARTISTES MAL FORMATÉS')
    print('='*70)
    
    # Albums avec artistes problématiques
    problematic_albums = [
        (374, 'Anna & Quido Hölbling, Ján Slávik, Daniela Ruso, Vladimir Ruso'),
        (590, 'Emanuel Ax, Leonidas Kavakos, Yo-Yo Ma'),
        (612, 'Katherine Jenkins, Kiri Te Kanawa, Philharmonia Orchestra, Anthony Ingliss'),
        (690, 'Christina Aguilera, Lil\' Kim, Mýa and P!nk'),
        (1068, 'Quentin Tarantino, Harvey Keitel, Steve Buscemi, Lawrence Tierney and Eddie Bunker'),
        (1151, 'Tan Dun, Itzhak Perlman, Ancient Rao Ensemble of Changsha Museum & China Philharmonic Orchestra and Chorus'),
        (1206, 'John McLaughlin, Jaco Pastorius, Tony Williams'),
    ]
    
    changes = 0
    
    for album_id, artist_string in problematic_albums:
        album = db.query(Album).filter_by(id=album_id).first()
        
        if not album:
            continue
        
        # Récupérer l'artiste actuel
        current_artists = [a.name for a in album.artists]
        
        # Vérifier si c'est déjà bien séparé
        if len(album.artists) > 1:
            print('  ✅ Album {} | Déjà séparé: {}'.format(
                album_id, 
                ', '.join([a.name[:30] for a in album.artists[:3]])
            ))
            continue
        
        # Sinon, séparer les artistes
        if len(album.artists) == 1 and ',' in album.artists[0].name:
            artist_names = [a.strip() for a in album.artists[0].name.split(',')]
            
            # Supprimer l'artiste actuel
            current_artist = album.artists[0]
            album.artists.remove(current_artist)
            
            # Ajouter les nouveaux artistes
            for artist_name in artist_names:
                artist_name = artist_name.strip()
                if artist_name:
                    # Chercher ou créer l'artiste
                    artist = db.query(Artist).filter_by(name=artist_name).first()
                    if not artist:
                        artist = Artist(name=artist_name)
                        db.add(artist)
                    
                    if artist not in album.artists:
                        album.artists.append(artist)
            
            db.commit()
            print('  🔧 Album {} | Séparé en {} artistes'.format(album_id, len(artist_names)))
            changes += 1
    
    print('\n' + '='*70)
    print('✅ Corrections appliquées: {}'.format(changes))
    print('='*70)
    
    db.close()

if __name__ == '__main__':
    fix_malformed_artists()
