#!/usr/bin/env python3
"""Rafraîchissement: Met à jour les métadonnées des albums importés avec les données enrichies."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Image, Metadata
import json
from sqlalchemy import text

print("\n" + "=" * 80)
print("🔄 RAFRAÎCHISSEMENT - MISE À JOUR DES MÉTADONNÉES")
print("=" * 80)

# Charger les données Discogs enrichies
json_file = './discogs_data_step2.json'
print(f"\n📖 Chargement des données enrichies ({json_file})...")

try:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"⚠️ Fichier {json_file} non trouvé")
    print("   Le rafraîchissement nécessite les données enrichies de l'étape 2")
    sys.exit(0)

albums_data = data['albums']
print(f"✅ {len(albums_data)} albums chargés du JSON\n")

# Connecter la BD
db = SessionLocal()

print("🔄 Mise à jour des métadonnées en BD...")
updated = 0
not_found = 0
errors = 0

for idx, album_data in enumerate(albums_data, 1):
    try:
        release_id = str(album_data['release_id'])
        
        # Chercher l'album dans la BD par Discogs ID
        album = db.query(Album).filter_by(discogs_id=release_id).first()
        
        if not album:
            not_found += 1
            if not_found <= 5:
                print(f"  ⚠️ Album non trouvé: {album_data['title']} (ID: {release_id})")
            continue
        
        # Vérifier et mettre à jour les données
        changed = False
        
        # Mettre à jour le support si nécessaire
        if album.support in ("Unknown", None) and album_data.get('support'):
            album.support = album_data['support']
            changed = True
        
        # Ajouter/mettre à jour l'image si nécessaire
        if album_data.get('cover_image'):
            existing_image = db.query(Image).filter_by(album_id=album.id, image_type='album', source='discogs').first()
            
            if not existing_image:
                image = Image(
                    url=album_data['cover_image'][:1000],
                    image_type='album',
                    source='discogs',
                    album_id=album.id
                )
                db.add(image)
                changed = True
        
        # Ajouter/mettre à jour les métadonnées si nécessaire
        if album_data.get('labels'):
            metadata = db.query(Metadata).filter_by(album_id=album.id).first()
            
            labels_str = ','.join(album_data.get('labels', []))[:1000] if album_data.get('labels') else None
            
            if metadata:
                if metadata.labels != labels_str:
                    metadata.labels = labels_str
                    changed = True
            else:
                metadata = Metadata(album_id=album.id, labels=labels_str)
                db.add(metadata)
                changed = True
        
        if changed:
            db.add(album)
            updated += 1
            db.commit()
        
        if idx % 50 == 0:
            percent = int((idx / len(albums_data)) * 100)
            bar_length = 30
            filled = int(bar_length * idx / len(albums_data))
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"  [{bar}] {idx}/{len(albums_data)} ({percent}%)")
        
    except Exception as e:
        errors += 1
        db.rollback()
        db = SessionLocal()
        if errors <= 3:
            print(f"  ❌ Erreur album {idx}: {str(e)[:50]}")
        continue

# Résultats
print(f"\n✅ Rafraîchissement complété")
print("=" * 80)
print(f"📊 Résumé:")
print(f"  Albums mis à jour: {updated}/{len(albums_data)}")
print(f"  Albums non trouvés: {not_found}")
print(f"  Erreurs: {errors}")
print(f"  Taux succès: {(updated / len(albums_data) * 100):.1f}%")

if updated > 0:
    print(f"\n✅ Métadonnées rafraîchies avec succès!")
elif not_found > 0:
    print(f"\n⚠️ Aucun album Discogs trouvé dans la BD")
    print(f"   Vérifiez que l'import (étape 3) s'est bien déroulé")

print("=" * 80 + "\n")

db.close()
