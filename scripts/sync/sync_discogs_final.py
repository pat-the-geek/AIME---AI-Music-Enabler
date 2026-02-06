#!/usr/bin/env python3
"""Script de synchronisation Discogs complète - FINAL TEST."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Artist, Image, Metadata
from backend.app.services.discogs_service import DiscogsService
from backend.app.services.spotify_service import SpotifyService
from backend.app.services.ai_service import AIService
import json
import logging
import asyncio

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

print("=" * 80)
print("🔄 SYNCHRONISATION COMPLÈTE DISCOGS - NOUVELLE PAGINATION")
print("=" * 80)

# Charger les secrets
with open('./config/secrets.json', 'r') as f:
    secrets = json.load(f)

# Initialiser les services
discogs_config = secrets.get('discogs', {})
spotify_config = secrets.get('spotify', {})
ai_config = secrets.get('euria', {})

discogs_service = DiscogsService(
    api_key=discogs_config.get('api_key'),
    username=discogs_config.get('username')
)

spotify_service = SpotifyService(
    client_id=spotify_config.get('client_id'),
    client_secret=spotify_config.get('client_secret')
)

ai_service = AIService(
    url=ai_config.get('url'),
    bearer=ai_config.get('bearer')
)

# Connexion BD
db = SessionLocal()

print("\n📊 État initial:")
old_count = db.query(Album).filter(Album.source == 'discogs').count()
print(f"  Albums Discogs en BD: {old_count}")

# Nettoyer les anciens
if old_count > 0:
    print(f"\n🗑️ Suppression des {old_count} anciens albums Discogs...")
    db.query(Album).filter(Album.source == 'discogs').delete()
    db.commit()
    print(f"✅ Nettoyé")

# Récupérer la collection
print("\n📡 Récupération collection Discogs (nouvelle pagination)...")
try:
    albums_data = discogs_service.get_collection(limit=None)
    print(f"\n✅ {len(albums_data)} albums récupérés de Discogs\n")
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

# Traiter et importer les albums
synced = 0
errors = 0
tame_count = 0

print(f"📥 Import dans la BD ({len(albums_data)} albums)...\n")

for idx, album_data in enumerate(albums_data, 1):
    try:
        # Vérifier doublon
        if db.query(Album).filter_by(discogs_id=str(album_data['release_id'])).first():
            continue
        
        # Créer/récupérer artistes
        artists = []
        seen_ids = set()
        for artist_name in album_data['artists']:
            if not artist_name or not artist_name.strip():
                continue
            artist = db.query(Artist).filter_by(name=artist_name).first()
            if not artist:
                artist = Artist(name=artist_name)
                db.add(artist)
                db.flush()
            if artist.id not in seen_ids:
                artists.append(artist)
                seen_ids.add(artist.id)
        
        if not artists:
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
        album.artists = artists
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
        
        # Métadonnées - Vérifier qu'elle n'existe pas
        existing_meta = db.query(Metadata).filter_by(album_id=album.id).first()
        if not existing_meta:
            metadata = Metadata(
                album_id=album.id,
                labels=','.join(album_data['labels']) if album_data.get('labels') else None
            )
            db.add(metadata)
        
        synced += 1
        
        # Vérifier Tame Impala
        if any('Tame Impala' in str(a) for a in album_data.get('artists', [])):
            tame_count += 1
            print(f"🎵 {synced}. TAME IMPALA: {album.title} ({year})")
        elif idx % 50 == 0:
            print(f"📀 Traitement: {synced} albums synced")
        
        # Commit par batch
        if synced % 25 == 0:
            db.commit()
        
    except Exception as e:
        errors += 1
        logger.warning(f"⚠️ Erreur album {idx}: {e}")
        db.rollback()
        continue

# Final commit
db.commit()

print(f"\n" + "=" * 80)
print(f"✅ SYNCHRONISATION TERMINÉE")
print(f"=" * 80)
print(f"📊 Résumé:")
print(f"  Albums synced: {synced}")
print(f"  Erreurs: {errors}")
print(f"  Tame Impala trouvés: {tame_count}")

# Vérifier en BD
db_count = db.query(Album).filter(Album.source == 'discogs').count()
print(f"\n📊 État final:")
print(f"  Albums Discogs en BD: {db_count}")

# Détails Tame Impala en BD
print(f"\n🎵 Albums Tame Impala en BD:")
tame_albums = db.query(Album).join(Album.artists).filter(
    Artist.name.ilike('%Tame Impala%')
).all()
for album in tame_albums:
    print(f"  • {album.title} ({album.year}) - source: {album.source} - discogs_id: {album.discogs_id}")

db.close()
print(f"\n" + "=" * 80)
