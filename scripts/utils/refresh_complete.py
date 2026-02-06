#!/usr/bin/env python3
"""Rafraîchissement complet: Normalise les noms + métadonnées + descriptions Euria + images artiste."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Image, Metadata, Artist
from backend.app.services.roon_normalization_service import RoonNormalizationService
import json
import time
from pathlib import Path

print("\n" + "=" * 80)
print("🔄 RAFRAÎCHISSEMENT COMPLET - PHASE 4 FINALE")
print("   Noms + Métadonnées + Descriptions Euria + Images Artiste")
print("=" * 80)

# Charger les données Discogs enrichies
json_file = './discogs_data_step2.json'
print(f"\n📖 Chargement des données enrichies ({json_file})...")

try:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"⚠️ Fichier {json_file} non trouvé")
    sys.exit(0)

albums_data = data['albums']
print(f"✅ {len(albums_data)} albums chargés du JSON\n")

# Charger les descriptions Euria si disponibles
euria_descriptions = {}
euria_file = Path('./data/euria_descriptions.json')
if euria_file.exists():
    try:
        with open(euria_file, 'r', encoding='utf-8') as f:
            euria_data = json.load(f)
            euria_descriptions = euria_data.get('data', {})
        print(f"📝 {len(euria_descriptions)} descriptions Euria chargées")
    except Exception as e:
        print(f"⚠️ Erreur chargement Euria: {e}")
else:
    print(f"⚠️ Fichier descriptions Euria non trouvé: {euria_file}")

# Charger les images d'artiste si disponibles
artist_images = {}
artist_img_file = Path('./data/artist_images.json')
if artist_img_file.exists():
    try:
        with open(artist_img_file, 'r', encoding='utf-8') as f:
            artist_data = json.load(f)
            artist_images = artist_data.get('data', {})
        print(f"🖼️  {len(artist_images)} images artiste chargées")
    except Exception as e:
        print(f"⚠️ Erreur chargement images artiste: {e}")
else:
    print(f"💡 Fichier images artiste non trouvé: {artist_img_file} (optionnel)")

print("")

# Connecter la BD
db = SessionLocal()
start_time = time.time()

# Créer le service de normalisation
norm_service = RoonNormalizationService()

print("🔄 Rafraîchissement force update...")
updated_count = 0
not_found = 0
errors = 0

for idx, album_data in enumerate(albums_data, 1):
    try:
        release_id = str(album_data['release_id'])
        
        # Chercher l'album dans la BD par Discogs ID
        album = db.query(Album).filter_by(discogs_id=release_id).first()
        
        if not album:
            not_found += 1
            continue
        
        # NORMALISER LE NOM
        canonical_title = norm_service._apply_corrections(album.title)
        if canonical_title != album.title:
            album.title = canonical_title
            updated_count += 1
        
        # METTRE À JOUR LES IMAGES (force: supprimer l'ancienne, ajouter la nouvelle)
        if album_data.get('cover_image'):
            # Supprimer les anciennes images Discogs
            db.query(Image).filter(
                Image.album_id == album.id,
                Image.source == 'discogs'
            ).delete()
            
            # Ajouter la nouvelle
            image = Image(
                url=album_data['cover_image'][:1000],
                image_type='album',
                source='discogs',
                album_id=album.id
            )
            db.add(image)
            updated_count += 1
        
        # METTRE À JOUR LE SUPPORT SUR L'ALBUM
        if album_data.get('support') and album.support != album_data.get('support'):
            album.support = album_data.get('support')
            updated_count += 1
        
        # AJOUTER LA DESCRIPTION EURIA SI DISPONIBLE
        if album.title in euria_descriptions:
            description = euria_descriptions[album.title].strip()
            # Ne pas appliquer les descriptions template (qui commencent par "[Remplir")
            if (description and 
                not description.startswith('[Remplir') and 
                not album.ai_description):
                album.ai_description = description[:2000]  # Limité à 2000 chars
                updated_count += 1
        
        # AJOUTER LES IMAGES D'ARTISTE SI DISPONIBLES
        if album_data.get('artists'):
            for artist_name in album_data['artists']:
                # Chercher l'artiste en BD
                artist = db.query(Artist).filter_by(name=artist_name).first()
                if artist and artist_name in artist_images:
                    artist_img_url = artist_images[artist_name].strip()
                    # Ne pas appliquer les URLs template (qui commencent par "[URL" ou "[")
                    if (artist_img_url and 
                        not artist_img_url.startswith('[') and
                        artist_img_url.startswith('http')):  # Vérifier que c'est une URL valide
                        # Vérifier si l'image existe déjà
                        existing_img = db.query(Image).filter_by(
                            artist_id=artist.id,
                            image_type='artist',
                            source='discogs'
                        ).first()
                        
                        if not existing_img:
                            # Ajouter l'image d'artiste
                            artist_image = Image(
                                url=artist_img_url[:1000],
                                image_type='artist',
                                source='discogs',
                                artist_id=artist.id
                            )
                            db.add(artist_image)
                            updated_count += 1
        
        # METTRE À JOUR LES MÉTADONNÉES (force: supprimer/recreer)
        if album_data.get('labels'):
            labels_str = ','.join(album_data.get('labels', []))[:1000]
            
            # Supprimer metadata ancienne
            db.query(Metadata).filter_by(album_id=album.id).delete()
            
            # Créer nouvelle
            metadata = Metadata(album_id=album.id, labels=labels_str)
            db.add(metadata)
            updated_count += 1
        
        # Commit par batch
        if idx % 50 == 0:
            db.commit()
            percent = int((idx / len(albums_data)) * 100)
            bar_length = 30
            filled = int(bar_length * idx / len(albums_data))
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"  [{bar}] {idx}/{len(albums_data)} ({percent}%) - {updated_count} changements")
        
    except Exception as e:
        errors += 1
        db.rollback()
        db = SessionLocal()
        if errors <= 3:
            print(f"  ❌ Erreur album {idx}: {str(e)[:80]}")
        continue

# Dernier commit
try:
    db.commit()
except Exception as e:
    print(f"❌ Erreur dernier commit: {e}")
    db.rollback()

elapsed = time.time() - start_time

# Résultats
print(f"\n✅ Rafraîchissement complété")
print("=" * 80)
print(f"📊 Résumé détaillé:")
print(f"  Changements effectués: {updated_count} migrations")
print(f"  Albums traités: {236-not_found}/236 trouvés")
print(f"  Albums non trouvés: {not_found}")
print(f"  Erreurs: {errors}")
print(f"  Temps: {elapsed:.1f}s")
print(f"  Taux succès: {int((236-not_found-errors)/236*100)}%")

# Statistiques détaillées
print(f"\n  📝 Descriptions Euria:")
print(f"     Disponibles: {len(euria_descriptions)}")
print(f"     (seront appliquées si trouvées en matching)")

print(f"\n  🖼️  Images Artiste:")
print(f"     Disponibles: {len(artist_images)}")
print(f"     (seront appliquées si artistes trouvés)")

if updated_count > 0:
    print(f"\n✅ {updated_count} changements appliqués à la phase 4!")
else:
    print(f"\n💡 Aucun changement détecté (vérifier fichiers descriptions/images)")

print("=" * 80 + "\n")

db.close()
