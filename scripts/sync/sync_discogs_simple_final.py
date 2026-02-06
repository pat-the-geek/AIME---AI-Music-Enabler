#!/usr/bin/env python3
"""Synchronisation Discogs simple et fiable."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Artist, Image, Metadata
from backend.app.services.discogs_service import DiscogsService
import json

print("=" * 80)
print("🔄 SYNCHRONISATION DISCOGS FINALE")
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
print("\n📡 Récupération collection Discogs...")
try:
    albums_data = service.get_collection(limit=None)
    print(f"✅ {len(albums_data)} albums trouvés\n")
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

# Traiter et importer
synced = 0
errors = 0
tame_impala_list = []

print(f"📥 Import dans la BD...\n")

for idx, album_data in enumerate(albums_data, 1):
    db = SessionLocal()  # Nouvelle session par album
    try:
        # Vérifier doublon
        if db.query(Album).filter_by(discogs_id=str(album_data['release_id'])).first():
            db.close()
            continue
        
        # Créer artistes si nécessaire
        artists = []
        for artist_name in album_data.get('artists', []):
            if not artist_name or not artist_name.strip():
                continue
            artist = db.query(Artist).filter_by(name=artist_name).first()
            if not artist:
                artist = Artist(name=artist_name)
                db.add(artist)
            artists.append(artist)
        
        if not artists:
            db.close()
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
            discogs_id=str(album_data['release_id']),
            discogs_url=album_data.get('discogs_url')
        )
       
        # Associer artistes directement
        for artist in artists:
            album.artists.append(artist)
        
        db.add(album)
        db.flush()
        
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
            labels=','.join(album_data['labels']) if album_data.get('labels') else None
        )
        db.add(metadata)
        
        db.commit()
        synced += 1
        
        # Vérifier Tame Impala
        if any('Tame Impala' in str(a) for a in album_data.get('artists', [])):
            tame_impala_list.append(f"{album.title} ({year})")
            print(f"🎵 Tame Impala #{len(tame_impala_list)}: {album.title} ({year})")
        elif synced % 50 == 0:
            print(f"📀 {synced} albums synced...")
        
    except Exception as e:
        errors += 1
        if errors <= 5:  # Afficher que les 5 premières erreurs
            print(f"⚠️ Album {idx}: {str(e)[:80]}")
    finally:
        db.close()

# Afficher résultats
print(f"\n" + "=" * 80)
print(f"✅ SYNCHRONISATION TERMINÉE")
print(f"=" * 80)
print(f"📊 Résultats:")
print(f"  Albums importés: {synced}")
print(f"  Erreurs: {errors}")
print(f"  Total attendus: {len(albums_data)}")

# Vérifier en BD
db = SessionLocal()
db_count = db.query(Album).filter(Album.source == 'discogs').count()
print(f"\n📊 État BD:")
print(f"  Albums Discogs: {db_count}")

# Tame Impala
if tame_impala_list:
    print(f"\n🎵 Albums Tame Impala ({len(tame_impala_list)}):")
    for album in tame_impala_list:
        print(f"  ✓ {album}")
else:
    # Chercher en BD
    tame_albums = db.query(Album).join(Album.artists).filter(
        Artist.name.ilike('%Tame Impala%'), Album.source == 'discogs'
    ).all()
    if tame_albums:
        print(f"\n🎵 Albums Tame Impala en BD ({len(tame_albums)}):")
        for album in tame_albums:
            print(f"  ✓ {album.title} ({album.year})")
    else:
        print(f"\n🎵 Aucun album Tame Impala trouvé")

db.close()
print(f"\n" + "=" * 80)
