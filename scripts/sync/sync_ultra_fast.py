#!/usr/bin/env python3
"""ULTRA-RAPIDE: Récupère tout, construit SQL en mémoire, insère."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal, engine
from backend.app.services.discogs_service import DiscogsService
from sqlalchemy import text
import json
import time

start = time.time()

print("=" * 80)
print("⚡⚡ SYNC ULTRA-RAPIDE - SQL BATCH")
print("=" * 80)

# Charger secrets
with open('./config/secrets.json') as f:
    secrets = json.load(f)

service = DiscogsService(
    api_key=secrets['discogs']['api_key'],
    username=secrets['discogs']['username']
)

# PHASE 1: Récupérer TOUT d'un coup
print("\n📡 Récupération Discogs...")
t1 = time.time()
albums_data = service.get_collection(limit=None)
print(f"✅ {len(albums_data)} albums en {time.time() - t1:.1f}s\n")

# PHASE 2: Préparer les données EN MÉMOIRE
print("🔧 Préparation données...")
db = SessionLocal()

# Récupérer les IDs existants et artistes UNE FOIS
existing_ids = set()
for row in db.execute(text("SELECT discogs_id FROM albums WHERE discogs_id IS NOT NULL")).fetchall():
    if row[0]:
        existing_ids.add(str(row[0]))

all_artists = {}  # name -> id
for row in db.execute(text("SELECT id, name FROM artists")).fetchall():
    all_artists[row[1]] = row[0]

print(f"  ✓ {len(existing_ids)} albums existants")
print(f"  ✓ {len(all_artists)} artistes en cache\n")

# PHASE 3: Construire les données
synced = 0
errors = 0
tame_impala_list = []
albums_to_insert = []
artist_inserts = []
relations = []
images = []
metadata_list = []

print("📋 Préparation batch insert...")

for algo, album_data in enumerate(albums_data, 1):
    try:
        rid = str(album_data['release_id'])
        
        # Skip doublon
        if rid in existing_ids:
            continue
        
        # Support
        support = "Unknown"
        if album_data.get('formats'):
            fmt = album_data['formats'][0]
            if 'Vinyl' in fmt or 'LP' in fmt:
                support = "Vinyle"
            elif 'CD' in fmt:
                support = "CD"
            elif 'Digital' in fmt:
                support = "Digital"
        
        year = album_data.get('year') or None
        if year == 0:
            year = None
        
        # Builder l'album
        album_tuple = (
            album_data['title'][:250],
            year,
            support,
            'discogs',
            rid,
            (album_data.get('discogs_url') or '')[:500]
        )
        albums_to_insert.append(album_tuple)
        synced += 1
        
        # Artistes
        artiste_names = []
        for artist_name in album_data.get('artists', []):
            if artist_name and artist_name.strip():
                artiste_names.append(artist_name[:250])
                
                # Ajouter artiste s'il manque
                if artist_name not in all_artists:
                    artist_inserts.append((artist_name[:250],))
                    all_artists[artist_name] = None  # Placeholder
        
        # Garder pour les relations
        if artiste_names:
            images.append((
                album_data.get('cover_image')[:1000] if album_data.get('cover_image') else None,
                rid,
                ','.join(album_data.get('labels', []))[:1000] if album_data.get('labels') else None,
                artiste_names
            ))
        
        # Tame Impala
        if any('Tame Impala' in a for a in artiste_names):
            tame_impala_list.append(f"{album_data['title']} ({year})")
        
    except Exception as e:
        errors += 1
        if errors <= 3:
            print(f"  ⚠️ {str(e)[:50]}")

print(f"  ✓ {synced} albums à importer\n")

# PHASE 4: INSÉRER PAR BATCH
print("💾 Insertion en batch...")

# Insérer les artistes manquants
if artist_inserts:
    db.execute(text(
        "INSERT OR IGNORE INTO artists (name) VALUES " + 
        ", ".join(["(:name_%d)" % i for i in range(len(artist_inserts))])
    ), {f"name_{i}": name[0] for i, name in enumerate(artist_inserts)})
    db.commit()
    print(f"  ✓ {len(artist_inserts)} artistes créés")

# Récupérer les IDs artistes
new_artists = {}
for row in db.execute(text("SELECT id, name FROM artists WHERE name NOT IN ({})".format(
    ",".join(f"'{a}'" for a in all_artists.keys())
) if all_artists else "SELECT id, name FROM artists")).fetchall():
    new_artists[row[1]] = row[0]

all_artists.update(new_artists)

# Insérer albums en chunk
batch_size = 100
for i in range(0, len(albums_to_insert), batch_size):
    batch = albums_to_insert[i:i+batch_size]
    placeholders = ", ".join(
        [f"(:title_{j}, :year_{j}, :support_{j}, :source_{j}, :discogs_id_{j}, :url_{j})" 
         for j in range(len(batch))]
    )
    params = {}
    for j, (title, year, support, source, did, url) in enumerate(batch):
        params[f"title_{j}"] = title
        params[f"year_{j}"] = year
        params[f"support_{j}"] = support
        params[f"source_{j}"] = source
        params[f"discogs_id_{j}"] = did
        params[f"url_{j}"] = url
    
    db.execute(text(
        f"INSERT INTO albums (title, year, support, source, discogs_id, discogs_url) VALUES {placeholders}"
    ), params)
    db.commit()
    print(f"  ✓ Batch {i//batch_size + 1}/{(len(albums_to_insert) + batch_size - 1)//batch_size}")

# Récupérer les IDs albums
album_mapping = {}
for row in db.execute(text("SELECT id, discogs_id FROM albums WHERE source = 'discogs'")).fetchall():
    if row[1]:
        album_mapping[str(row[1])] = row[0]

# Insérer images et métadonnées
for cover_url, rid, labels, artist_names in images:
    album_id = album_mapping.get(rid)
    if not album_id:
        continue
    
    if cover_url:
        db.execute(text(
            "INSERT INTO images (url, image_type, source, album_id) VALUES (:url, :type, :source, :album_id)"
        ), {'url': cover_url, 'type': 'album', 'source': 'discogs', 'album_id': album_id})
    
    db.execute(text(
        "INSERT OR IGNORE INTO metadata (album_id, labels) VALUES (:album_id, :labels)"
    ), {'album_id': album_id, 'labels': labels})
    
    # Ajouter artistes
    for artist_name in artist_names:
        artist_id = all_artists.get(artist_name)
        if artist_id:
            db.execute(text(
                "INSERT OR IGNORE INTO album_artist (album_id, artist_id) VALUES (:album_id, :artist_id)"
            ), {'album_id': album_id, 'artist_id': artist_id})

db.commit()

elapsed = time.time() - start

# Résultats
if tame_impala_list:
    print(f"\n🎵 Tame Impala ({len(tame_impala_list)}):")
    for album in tame_impala_list[:5]:
        print(f"  ✓ {album}")

print(f"\n" + "=" * 80)
print(f"✅ TERMINÉ en {elapsed:.1f}s")
print("=" * 80)
print(f"📊 {synced} albums importés")
print(f"⏱️ {synced / max(elapsed, 1):.1f} albums/sec")

if elapsed < 300:
    print(f"✅ < 5 minutes")
else:
    print(f"⚠️ > 5 minutes")

db.close()
print("=" * 80)
