#!/usr/bin/env python3
"""Script pour nettoyer les images dupliquées d'albums."""
import sys
from app.database import SessionLocal
from app.models import Image

session = SessionLocal()
try:
    # Supprimer l'image Spotify incorrecte (ID 2540)
    img_spotify = session.query(Image).filter_by(id=2540).first()
    if img_spotify:
        print(f'[DEBUG] Suppression image Spotify ID=2540 (source={img_spotify.source})')
        session.delete(img_spotify)
    
    # Supprimer l'ancien Last.fm (ID 2538)
    img_lastfm_old = session.query(Image).filter_by(id=2538).first()
    if img_lastfm_old:
        print(f'[DEBUG] Suppression ancien Last.fm ID=2538')
        session.delete(img_lastfm_old)
    
    session.commit()
    print('[DEBUG] ✅ Images supprimées avec succès', flush=True)
    
    # Vérification
    images = session.query(Image).filter_by(album_id=2173, image_type='album').all()
    print(f'[DEBUG] Images restantes: {len(images)}', flush=True)
    for img in images:
        print(f'[DEBUG]   - ID={img.id}, source={img.source}, url={img.url[:60]}...', flush=True)
finally:
    session.close()
