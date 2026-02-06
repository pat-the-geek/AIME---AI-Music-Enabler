#!/usr/bin/env python3
"""Vérifier les URLs d'images dans la base de données."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

db_path = os.path.join(os.path.dirname(__file__), 'data', 'musique.db')
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)
session = Session()

from app.models.album import Album

albums = session.query(Album).limit(30).all()

print('=== Vérification des image_url ===')
valid_count = 0
for album in albums:
    if album.image_url and len(album.image_url) > 10:
        valid_count += 1
        status = '✓ OK'
    else:
        status = '✗ VIDE'
    print(f'{status}: {album.title[:40]:40} | {str(album.image_url)[:70]}')
    
print(f'\n=== Statistiques ===')
total = session.query(Album).count()
with_url = session.query(Album).filter(Album.image_url.isnot(None)).count()
with_valid_url = session.query(Album).filter(Album.image_url.like('http%')).count()
empty_or_null = total - with_valid_url

print(f'Total albums: {total}')
print(f'Avec image_url NOT NULL: {with_url}')
print(f'Avec URL valide (http): {with_valid_url}')
print(f'Vides ou NULL: {empty_or_null}')
print(f'Pourcentage valides: {(with_valid_url/total*100):.1f}%')

session.close()
