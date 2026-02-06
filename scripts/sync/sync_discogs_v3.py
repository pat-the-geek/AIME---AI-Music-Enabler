#!/usr/bin/env python3
"""Synchronisation Discogs - Approche TRÈS simple."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Artist, Image, Metadata
from backend.app.services.discogs_service import DiscogsService
import json

print("=" * 80)
print("🔄 SYNCHRONISATION DISCOGS - SIMPLE ET ROBUSTE")
print("=" * 80)

# Charger les secrets
with open('./config/secrets.json') as f:
    secrets = json.load(f)

discogs_config = secrets.get('discogs', {})
service = DiscogsService(
    api_key=discogs_config.get('api_key'),
    username=discogs_config.get('username')
)

# Récupérer la collection  
print("\n📡 Récupération collection Discogs...")
try:
    albums_data = service.get_collection(limit=None)
    print(f"✅ {len(albums_data)} albums trouvés\n")
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

# Utiliser une seule session pour tout
db = SessionLocal()
synced = 0
errors = 0
tame_impala = []

print(f"📥 Import dans la BD...\n")

for idx, album_data in enumerate(albums_data, 1):
    try:
        # Vérifier doublon
        release_id = str(album_data['release_id'])
        if db.query(Album).filter_by(discogs_id=release_id).first():
            continue
        
        # Créer ou récupérer les artistes
        artist_objects = []
        for artist_name in album_data.get('artists', []):
            if not artist_name or not artist_name.strip():
                continue
            
            artist = db.query(Artist).filter_by(name=artist_name).first()
            if not artist:
                artist = Artist(name=artist_name)
                db.add(artist)
            artist_objects.append(artist)
        
        # Commit artistes
        db.commit()
        
        if not artist_objects:
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
        
        # CRÉER ALBUM SANS ARTISTES D'ABORD
        album = Album(
            title=album_data['title'],
            year=year,
            support=support,
            source='discogs',
            discogs_id=release_id,
            discogs_url=album_data.get('discogs_url')
        )
        db.add(album)
        db.flush()
        
        # AJOUTER LES ARTISTES APRÈS
        for artist in artist_objects:
            # Vérifier que la relation n'existe pas déjà
            if artist not in album.artists:
                album.artists.append(artist)
        
        # Image
        if album_data.get('cover_image'):
            image = Image(
                url=album_data['cover_image'],
                image_type='album',
                source='discogs',
                album_id=album.id
            )
            db.add(image)
        
        # Métadonnées
        metadata = Metadata(
            album_id=album.id,
            labels=','.join(album_data.get('labels', [])) if album_data.get('labels') else None
        )
        db.add(metadata)
        
        db.commit()
        synced += 1
        
        # Afficher Tame Impala
        if any('Tame Impala' in str(a) for a in album_data.get('artists', [])):
            tame_impala.append(f"{album.title} ({year})")
            print(f"🎵 Tame Impala: {album.title} ({year})")
        elif synced % 50 == 0:
            print(f"📀 {synced} albums...")
        
    except Exception as e:
        errors += 1
        db.rollback()
        if errors <= 5:
            print(f"⚠️ Album {idx}: {str(e)[:70]}")
        continue

# Résultats finaux
print(f"\n" + "=" * 80)
print(f"✅ SYNCHRONISATION TERMINÉE")
print(f"=" * 80)
print(f"📊 Résultats:")
print(f"  Albums importés: {synced}")
print(f"  Erreurs: {errors}")
print(f"  Total attendus: {len(albums_data)}")

# Vérifier Albums de Tame Impala
print(f"\n🎵 Albums Tame Impala: {len(tame_impala)}")
for album in tame_impala:
    print(f"  ✓ {album}")

db.close()
print(f"\n" + "=" * 80)
