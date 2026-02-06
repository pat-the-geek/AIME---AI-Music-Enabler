#!/usr/bin/env python3
"""ÉTAPE 3: Importe les données dans la base de données."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal, engine
from backend.app.models import Album, Artist, Image, Metadata
from sqlalchemy import text, inspect
import json
import time
from datetime import datetime

print("\n" + "=" * 80)
print("💾 ÉTAPE 3: IMPORT EN BASE DE DONNÉES")
print("=" * 80)

# Charger le fichier de l'étape 2
input_file = './discogs_data_step2.json'
print(f"\n📖 Chargement {input_file}...")

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"❌ Fichier {input_file} non trouvé!")
    print("   Exécute d'abord: python3 step1_fetch_discogs.py && python3 step2_enrich_data.py")
    exit(1)

albums_data = data['albums']
print(f"✅ {len(albums_data)} albums chargés\n")

# Connexion DB
db = SessionLocal()
start_time = time.time()

print("🗑️ Nettoyage de la BD (tables Discogs)...")
# Désactiver les contraintes FK
db.execute(text("PRAGMA foreign_keys=OFF"))
db.commit()

# Nettoyer simplement en supprimant tous les albums Discogs et en cascade
try:
    # Méthode simple : supprimer tous les albums Discogs (cascade automatique)
    db.execute(text("DELETE FROM albums WHERE source = 'discogs'"))
    db.commit()
except Exception:
    pass

db.execute(text("PRAGMA foreign_keys=ON"))
db.commit()
print("✅ Nettoyage effectué\n")

# Récupérer les artistes existants
print("📍 Préparation artistes...")
artist_cache = {}
for row in db.execute(text("SELECT id, name FROM artists")).fetchall():
    artist_cache[row[1]] = row[0]

print(f"  ✓ {len(artist_cache)} artistes en cache\n")

# Import par batch
print("📥 Import albums...")
batch_size = 50
synced = 0
errors = 0
tame_impala_found = []

# Récupérer les IDs existants pour éviter les doublons
existing_ids = set()
for row in db.execute(text("SELECT discogs_id FROM albums WHERE discogs_id IS NOT NULL")).fetchall():
    if row[0]:
        existing_ids.add(str(row[0]))

for batch_idx in range(0, len(albums_data), batch_size):
    batch = albums_data[batch_idx:batch_idx + batch_size]
    
    for album_data in batch:
        try:
            release_id = str(album_data['release_id'])
            
            # Passer les doublons
            if release_id in existing_ids:
                continue
            
            # Créer ou rechercher les artistes
            artists_for_album = []
            for artist_name in album_data.get('artists', []):
                if not artist_name or not artist_name.strip():
                    continue
                
                # Vérifier si l'artiste existe
                if artist_name not in artist_cache:
                    artist = Artist(name=artist_name)
                    db.add(artist)
                    db.flush()
                    artist_cache[artist_name] = artist.id
                
                artists_for_album.append(artist_cache[artist_name])
            
            if not artists_for_album:
                continue
            
            # Créer l'album
            album = Album(
                title=album_data['title'][:250],
                year=album_data.get('year'),
                support=album_data.get('support', 'Unknown'),
                source='discogs',
                discogs_id=release_id,
                discogs_url=(album_data.get('discogs_url') or '')[:500]
            )
            db.add(album)
            db.flush()
            
            # Ajouter les relations artistes
            for artist_id in artists_for_album:
                artist_obj = db.query(Artist).filter_by(id=artist_id).first()
                if artist_obj and artist_obj not in album.artists:
                    album.artists.append(artist_obj)
            
            # Ajouter l'image si elle existe
            if album_data.get('cover_image'):
                image = Image(
                    url=album_data['cover_image'][:1000],
                    image_type='album',
                    source='discogs',
                    album_id=album.id
                )
                db.add(image)
            
            # Ajouter les métadonnées
            labels = ','.join(album_data.get('labels', []))[:1000] if album_data.get('labels') else None
            metadata = Metadata(
                album_id=album.id,
                labels=labels
            )
            db.add(metadata)
            
            synced += 1
            existing_ids.add(release_id)
            
            # Vérifier Tame Impala
            if any('Tame Impala' in artist for artist in album_data.get('artists', [])):
                tame_impala_found.append(f"{album_data['title']} ({album_data.get('year', '?')})")
            
        except Exception as e:
            errors += 1
            db.rollback()
            db = SessionLocal()  # Nouvelle session
            if errors <= 3:
                print(f"  ⚠️ Erreur: {str(e)[:60]}")
            continue
    
    # Commit du batch
    try:
        db.commit()
        progress = min(batch_idx + batch_size, len(albums_data))
        percent = int((progress / len(albums_data)) * 100)
        bar_length = 30
        filled = int(bar_length * progress / len(albums_data))
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"  [{bar}] {progress}/{len(albums_data)} ({percent}%) - {synced} importés")
    except Exception as e:
        print(f"  ❌ Erreur commit: {str(e)[:60]}")
        db.rollback()
        db = SessionLocal()

elapsed = time.time() - start_time

# Résultats finaux
print(f"\n✅ Étape 3 complétée")
print("=" * 80)
print(f"📊 Résumé final:")
print(f"  Albums importés: {synced}")
print(f"  Erreurs: {errors}")
print(f"  Temps: {elapsed:.1f}s")
print(f"  Vitesse: {synced / max(elapsed, 1):.1f} albums/s")

if tame_impala_found:
    print(f"\n🎵 Tame Impala trouvés ({len(tame_impala_found)}):")
    for album in tame_impala_found[:10]:
        print(f"  ✓ {album}")

if elapsed < 300:
    print(f"\n⏱️ ✅ Import < 5 minutes")
else:
    print(f"\n⏱️ ⚠️ Import > 5 minutes")

print("=" * 80 + "\n")

db.close()
