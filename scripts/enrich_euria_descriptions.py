#!/usr/bin/env python3
"""Enrichir les albums avec les descriptions euriA"""

import sys
import os
import json
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal
from app.models import Album

def enrich_with_euria_descriptions():
    """Chercher les descriptions euriA pour les albums"""
    db = SessionLocal()
    
    print('\n📝 ENRICHISSEMENT DESCRIPTIONS EURIA')
    print('='*70)
    
    # Chercher un fichier avec les descriptions euriA
    euria_path = Path(__file__).parent.parent / 'data' / 'euria_descriptions.json'
    
    if not euria_path.exists():
        print('⚠️  Fichier euriA descriptions non trouvé: {}'.format(euria_path))
        print('   Création d\'un template...')
        
        # Créer un template
        albums = db.query(Album).limit(10).all()
        template = {
            "template": "Format: titre de l'album -> description",
            "data": {
                album.title: "Description à remplir pour {}".format(album.title)
                for album in albums
            }
        }
        
        # Sauvegarder le template
        euria_path.parent.mkdir(parents=True, exist_ok=True)
        with open(euria_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        print('   ✅ Template créé: {}'.format(euria_path))
        print('   Remplissez les descriptions et relancez le script')
        db.close()
        return
    
    # Charger les descriptions
    with open(euria_path, 'r', encoding='utf-8') as f:
        euria_data = json.load(f)
    
    descriptions = euria_data.get('data', {})
    
    if not descriptions:
        print('⚠️  Aucune description euriA trouvée')
        db.close()
        return
    
    # Appliquer les descriptions aux albums
    applied_count = 0
    for album_title, description in descriptions.items():
        album = db.query(Album).filter_by(title=album_title).first()
        
        if album and description and not album.ai_description:
            album.ai_description = description
            db.commit()
            applied_count += 1
    
    print('✅ Descriptions appliquées: {}'.format(applied_count))
    print('='*70)
    
    db.close()

if __name__ == '__main__':
    enrich_with_euria_descriptions()
