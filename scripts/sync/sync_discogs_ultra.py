#!/usr/bin/env python3
"""Synchronisation Discogs ULTRA-RAPIDE - SQL direct."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Artist, Image, Metadata
from backend.app.services.discogs_service import DiscogsService
from sqlalchemy import insert
import json
import time

start_time = time.time()

print("=" * 80)
print("🚀 SYNCHRONISATION DISCOGS ULTRA-RAPIDE")
print("=" * 80)

# Charger les secrets
with open('./config/secrets.json') as f:
    secrets = json.load(f)

discogs_config = secrets.get('discogs', {})
service = DiscogsService(
    api_key=discogs_config.get('api_key'),
    username=discogs_config.get('username')
)

# PHASE 1: Récupérer la collection
print("\n📡 Récupération collection...")
fetch_start = time.time()
try:
    albums_data = service.get_collection(limit=None)
    print(f"✅ {len(albums_data)} albums en {time.time() - fetch_start:.1f}s\n")
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

# PHASE 2: Préparer les données
print("📋 Préparation des données...")
db = SessionLocal()
synced = 0
errors = 0
tame_impala = []

# Préparer les artistes
artist_names_set = set()
for album_data in albums_data:
    for artist_name in album_data.get('artists', []):
        if artist_name and artist_name.strip():
            artist_names_set.add(artist_name)

# Créer les artistes (bulk insert)
if artist_names_set:
    existing_artists = {}
    for artist_name in artist_names_set:
        artist = db.query(Artist).filter_by(name=artist_name).first()
        if not artist:
            artist = Artist(name=artist_name)
            db.add(artist)
        existing_artists[artist_name] = artist
    db.commit()
    print(f"  ✓ {len(existing_artists)} artistes créés")

# Récupérer les IDs existants
existing_discogs_ids = set()
for album in db.query(Album.discogs_id).filter(Album.discogs_id != None).all():
    existing_discogs_ids.add(album[0])

print(f"  ✓ {len(existing_discogs_ids)} albums existants ignorés\n")

# PHASE 3: Import des albums
print(f"📥 Import par batch...\n")

albums_to_insert = []
relations_to_insert = []
images_to_insert = []
metadata_to_insert = []

for idx, album_data in enumerate(albums_data, 1):
    try:
        release_id = str(album_data['release_id'])
        
        # Passer les doublons
        if release_id in existing_discogs_ids:
            continue
        
        # Déterminer support
        support = "Unknown"
        if album_data.get('formats'):
            fmt = album_data['formats'][0]
            if 'Vinyl' in fmt or 'LP' in fmt:
                support = "Vinyle"
            elif 'CD' in fmt:
                support = "CD"
            elif 'Digital' in fmt:
                support = "Digital"
        
        # Année
        year = album_data.get('year')
        if year == 0:
            year = None
        
        # Préparer album pour insert
        album_record = {
            'title': album_data['title'],
            'year': year,
            'support': support,
            'source': 'discogs',
            'discogs_id': release_id,
            'discogs_url': album_data.get('discogs_url')
        }
        
        albums_to_insert.append((album_record, album_data))
        synced += 1
        
        # Afficher Tame Impala
        if any('Tame Impala' in str(a) for a in album_data.get('artists', [])):
            tame_impala.append(f"{album_data['title']} ({year})")
        
        if synced % 50 == 0:
            print(f"  📋 {synced} albums préparés...")
        
    except Exception as e:
        errors += 1
        if errors <= 3:
            print(f"  ⚠️ Album {idx}: {str(e)[:50]}")
        continue

print(f"\n💾 Insertion en BD...")

# Bulk insert des albums avec relations
batch_size = 50
for batch_idx in range(0, len(albums_to_insert), batch_size):
    batch = albums_to_insert[batch_idx:batch_idx + batch_size]
    
    for album_record, album_data in batch:
        try:
            # Créer album
            album = Album(**album_record)
            db.add(album)
            db.flush()
            
            # Ajouter artistes
            for artist_name in album_data.get('artists', []):
                if artist_name and artist_name.strip() and artist_name in existing_artists:
                    # Vérifier la relation n'existe pas
                    if existing_artists[artist_name] not in album.artists:
                        album.artists.append(existing_artists[artist_name])
            
            # Ajouter image
            if album_data.get('cover_image'):
                image = Image(
                    url=album_data['cover_image'],
                    image_type='album',
                    source='discogs',
                    album_id=album.id
                )
                db.add(image)
            
            # Ajouter métadonnées
            metadata = Metadata(
                album_id=album.id,
                labels=','.join(album_data.get('labels', [])) if album_data.get('labels') else None
            )
            db.add(metadata)
            
        except Exception as e:
            db.rollback()
            db = SessionLocal()
            continue
    
    # Commit batch
    try:
        db.commit()
        print(f"  ✓ Batch {batch_idx // batch_size + 1}/{(len(albums_to_insert) + batch_size - 1) // batch_size}")
    except Exception as e:
        print(f"  ⚠️ Erreur commit: {e}")
        db.rollback()
        db = SessionLocal()
        continue

# Résultats
elapsed = time.time() - start_time

if tame_impala:
    print(f"\n🎵 Tame Impala trouvés ({len(tame_impala)}):")
    for album in tame_impala:
        print(f"  ✓ {album}")

print(f"\n" + "=" * 80)
print(f"✅ SYNCHRONISATION TERMINÉE en {elapsed:.1f}s")
print(f"=" * 80)
print(f"📊 Résultats:")
print(f"  Albums sur BD: {synced}")
print(f"  Erreurs: {errors}")
print(f"  Vitesse: {synced / max(elapsed, 1):.1f} albums/sec")

if elapsed < 300:
    print(f"  ⏱️ Temps: {elapsed:.1f}s ✅ (< 5 min)")
else:
    print(f"  ⏱️ Temps: {elapsed:.1f}s ⚠️ (> 5 min)")

db.close()
print("=" * 80)
