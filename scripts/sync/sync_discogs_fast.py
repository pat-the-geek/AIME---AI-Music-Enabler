#!/usr/bin/env python3
"""Synchronisation Discogs OPTIMISÉE - < 5 minutes."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Artist, Image, Metadata
from backend.app.services.discogs_service import DiscogsService
import json
import time

start_time = time.time()

print("=" * 80)
print("🔄 SYNCHRONISATION DISCOGS OPTIMISÉE")
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
print("\n📡 Récupération collection Discogs...")
fetch_start = time.time()
try:
    albums_data = service.get_collection(limit=None)
    print(f"✅ {len(albums_data)} albums trouvés en {time.time() - fetch_start:.1f}s\n")
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

# PHASE 2: Utiliser une SEULE session pour tout
db = SessionLocal()
synced = 0
errors = 0
tame_impala = []
batch_size = 30

print(f"📥 Import dans la BD (batch size: {batch_size})...\n")

# Pré-calculer tous les artistes une fois
print("🎤 Pré-calcul des artistes...")
artist_cache = {}
for album_data in albums_data:
    for artist_name in album_data.get('artists', []):
        if artist_name and artist_name.strip() and artist_name not in artist_cache:
            artist = db.query(Artist).filter_by(name=artist_name).first()
            if not artist:
                artist = Artist(name=artist_name)
                db.add(artist)
            artist_cache[artist_name] = artist

db.commit()
print(f"✅ {len(artist_cache)} artistes prêts\n")

# PHASE 3: Import par batch
batch = []

for idx, album_data in enumerate(albums_data, 1):
    try:
        # Vérifier doublon
        release_id = str(album_data['release_id'])
        if db.query(Album).filter(Album.discogs_id == release_id).limit(1).first():
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
        
        # Créer album
        album = Album(
            title=album_data['title'],
            year=year,
            support=support,
            source='discogs',
            discogs_id=release_id,
            discogs_url=album_data.get('discogs_url')
        )
        
        # Ajouter artistes (sans append, directement)
        for artist_name in album_data.get('artists', []):
            if artist_name and artist_name.strip():
                if artist_name in artist_cache:
                    album.artists.append(artist_cache[artist_name])
        
        # Image
        if album_data.get('cover_image'):
            image = Image(
                url=album_data['cover_image'],
                image_type='album',
                source='discogs',
                album_id=None  # Sera défini après flush
            )
            album.images.append(image)
        
        # Métadonnées
        metadata = Metadata(
            album_id=None,  # Sera défini après flush
            labels=','.join(album_data.get('labels', [])) if album_data.get('labels') else None
        )
        album.album_metadata = metadata
        
        db.add(album)
        batch.append(album)
        
        # Vérifier Tame Impala
        if any('Tame Impala' in str(a) for a in album_data.get('artists', [])):
            tame_impala.append(f"{album.title} ({year})")
        
        # Commit par batch
        if len(batch) >= batch_size:
            db.commit()
            synced += len(batch)
            print(f"📀 {synced} albums ({time.time() - start_time:.1f}s)...")
            batch = []
        
    except Exception as e:
        errors += 1
        db.rollback()
        db = SessionLocal()  # Nouvelle session après erreur
        if errors <= 3:
            print(f"⚠️ Album {idx}: {str(e)[:50]}")
        continue

# Commit final
if batch:
    db.commit()
    synced += len(batch)

# Afficher Tame Impala trovés
if tame_impala:
    print(f"\n🎵 Tame Impala trouvés ({len(tame_impala)}):")
    for album in tame_impala:
        print(f"  ✓ {album}")

# Résultats
elapsed = time.time() - start_time
print(f"\n" + "=" * 80)
print(f"✅ SYNCHRONISATION TERMINÉE en {elapsed:.1f}s")
print(f"=" * 80)
print(f"📊 Résultats:")
print(f"  Albums importés: {synced}")
print(f"  Erreurs: {errors}")
print(f"  Vitesse: {synced / max(elapsed, 1):.1f} albums/sec")
print(f"  Temps total: {elapsed:.1f}s (objectif: < 300s)")

if elapsed < 300:
    print(f"\n✅ OBJECTIF ATTEINT: < 5 minutes!")
else:
    print(f"\n⚠️ Trop long: {elapsed:.1f}s / 300s max")

db.close()
print("=" * 80)
