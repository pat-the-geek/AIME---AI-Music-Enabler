#!/usr/bin/env python3
"""Synchronisation Discogs RAPIDE avec SQL brut."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal, engine
from backend.app.services.discogs_service import DiscogsService
import json
import time
from sqlalchemy import text

start_time = time.time()

print("=" * 80)
print("⚡ SYNC DISCOGS - MODE SQL BRUT")
print("=" * 80)

# Charger les secrets
with open('./config/secrets.json', 'r') as f:
    secrets = json.load(f)

discogs_config = secrets.get('discogs', {})
service = DiscogsService(
    api_key=discogs_config.get('api_key'),
    username=discogs_config.get('username')
)

# Récupérer la collection
print("\n📡 Récupération collection...")
fetch_start = time.time()
try:
    albums_data = service.get_collection(limit=None)
    print(f"✅ {len(albums_data)} albums en {time.time() - fetch_start:.1f}s\n")
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

# Préparation
db = SessionLocal()
synced = 0
errors = 0
tame_impala = []

# Récupérer les IDs existants
existing_ids = set()
for row in db.execute(text("SELECT discogs_id FROM albums WHERE discogs_id IS NOT NULL")).fetchall():
    if row[0]:
        existing_ids.add(str(row[0]))

print(f"📊 {len(existing_ids)} albums existants\n")

# Récupérer les artistes existants
artist_cache = {}
for row in db.execute(text("SELECT id, name FROM artists")).fetchall():
    artist_cache[row[1]] = row[0]

print("📥 Import par batch SQL...\n")

# Préparer les données batch
albums_batch = []
album_artist_batch = []
images_batch = []
metadata_batch = []
artist_counter = 0

for idx, album_data in enumerate(albums_data, 1):
    try:
        release_id = str(album_data['release_id'])
        
        # Passer les doublons
        if release_id in existing_ids:
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
        
        year = album_data.get('year')
        if year == 0:
            year = None
        
        # Préparer album dict
        album_dict = {
            'title': album_data['title'][:250],
            'year': year,
            'support': support,
            'source': 'discogs',
            'discogs_id': release_id,
            'discogs_url': (album_data.get('discogs_url') or '')[:500]
        }
        
        # Traiter artistes
        artists_for_album = []
        for artist_name in album_data.get('artists', []):
            if not artist_name or not artist_name.strip():
                continue
            
            if artist_name not in artist_cache:
                # Créer nouvel artiste
                db.execute(text(
                    "INSERT INTO artists (name) VALUES (:name)"
                ), {'name': artist_name[:250]})
                db.commit()
                # Récupérer l'ID
                result = db.execute(text(
                    "SELECT id FROM artists WHERE name = :name"
                ), {'name': artist_name[:250]}).first()
                if result:
                    artist_cache[artist_name] = result[0]
            
            if artist_name in artist_cache:
                artists_for_album.append(artist_cache[artist_name])
        
        if not artists_for_album:
            continue
        
        # Insérer album
        db.execute(text(
            "INSERT INTO albums (title, year, support, source, discogs_id, discogs_url) "
            "VALUES (:title, :year, :support, :source, :discogs_id, :discogs_url)"
        ), album_dict)
        db.commit()
        
        # Récupérer l'ID de l'album
        album_id = db.execute(text(
            "SELECT id FROM albums WHERE discogs_id = :discogs_id"
        ), {'discogs_id': release_id}).first()
        
        if not album_id:
            continue
        
        album_id = album_id[0]
        
        # Insérer relations artistes
        for artist_id in artists_for_album:
            db.execute(text(
                "INSERT OR IGNORE INTO album_artist (album_id, artist_id) VALUES (:album_id, :artist_id)"
            ), {'album_id': album_id, 'artist_id': artist_id})
        
        # Insérer image
        if album_data.get('cover_image'):
            db.execute(text(
                "INSERT INTO images (url, image_type, source, album_id) "
                "VALUES (:url, :image_type, :source, :album_id)"
            ), {
                'url': album_data['cover_image'][:1000],
                'image_type': 'album',
                'source': 'discogs',
                'album_id': album_id
            })
        
        # Insérer metadata
        labels = ','.join(album_data.get('labels', []))[:1000] if album_data.get('labels') else None
        db.execute(text(
            "INSERT OR IGNORE INTO metadata (album_id, labels) VALUES (:album_id, :labels)"
        ), {'album_id': album_id, 'labels': labels})
        
        db.commit()
        synced += 1
        
        # Vérifier Tame Impala
        if any('Tame Impala' in str(a) for a in album_data.get('artists', [])):
            tame_impala.append(f"{album_data['title']} ({year})")
        
        if synced % 50 == 0:
            elapsed = time.time() - start_time
            rate = synced / max(elapsed, 0.1)
            print(f"  ✓ {synced} albums ({rate:.1f}/sec)")
        
    except Exception as e:
        errors += 1
        db.rollback()
        if errors <= 3:
            print(f"  ⚠️ Album #{idx}: {str(e)[:60]}")
        continue

# Résultats
elapsed = time.time() - start_time

if tame_impala:
    print(f"\n🎵 Tame Impala trouvés ({len(tame_impala)}):")
    for album in tame_impala[:10]:
        print(f"  ✓ {album}")

print(f"\n" + "=" * 80)
print(f"✅ SYNCHRONISATION TERMINÉE")
print("=" * 80)
print(f"📊 Résultats:")
print(f"  Albums importés: {synced}")
print(f"  Erreurs: {errors}")
print(f"  Temps: {elapsed:.1f}s")
print(f"  Vitesse: {synced / max(elapsed, 1):.1f} albums/s")

if elapsed < 300:
    print(f"  ⏱️ ✅ Complété en < 5 minutes")
else:
    print(f"  ⏱️ ⚠️ Dépassement du délai 5 min")

db.close()
print("=" * 80)
