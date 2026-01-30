#!/usr/bin/env python3
"""Script de validation des corrections de synchronisation Discogs."""
import sys
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.models import Album, Artist, Metadata
from sqlalchemy import func

print("🔍 Validation des Corrections Sync Discogs\n")

db = SessionLocal()

# Test 1: Albums dans la base
total_albums = db.query(Album).count()
print(f"✅ Albums dans la base: {total_albums}")

# Test 2: Albums avec artistes
albums_with_artists = db.query(Album).join(Album.artists).count()
print(f"✅ Albums avec artistes: {albums_with_artists}")

# Test 3: Albums SANS artistes (problématiques)
albums_without_artists = db.query(Album).outerjoin(Album.artists).group_by(Album.id).having(func.count(Artist.id) == 0).count()
if albums_without_artists > 0:
    print(f"⚠️  Albums SANS artistes: {albums_without_artists}")
else:
    print(f"✅ Aucun album sans artiste")

# Test 4: Albums avec métadonnées
albums_with_metadata = db.query(Album).join(Album.album_metadata).count()
print(f"✅ Albums avec métadonnées: {albums_with_metadata}")

# Test 5: Albums SANS métadonnées (normal)
albums_without_metadata = total_albums - albums_with_metadata
print(f"ℹ️  Albums sans métadonnées: {albums_without_metadata}")

# Test 6: Albums avec images
albums_with_images = db.query(Album).join(Album.images).count()
print(f"✅ Albums avec images: {albums_with_images}")

# Test 7: Albums avec année NULL ou 0
albums_no_year = db.query(Album).filter((Album.year == None) | (Album.year == 0)).count()
if albums_no_year > 0:
    print(f"ℹ️  Albums sans année: {albums_no_year}")

# Test 8: Lister quelques albums pour vérifier
print(f"\n📀 Échantillon d'albums:")
albums = db.query(Album).limit(5).all()
for album in albums:
    artists_names = [a.name for a in album.artists] if album.artists else ["(aucun artiste)"]
    has_metadata = "✓" if album.album_metadata else "✗"
    has_images = "✓" if album.images else "✗"
    print(f"  • {album.title} ({album.year or 'N/A'})")
    print(f"    Artistes: {', '.join(artists_names)}")
    print(f"    Metadata: {has_metadata} | Images: {has_images} | Support: {album.support}")

# Test 9: Vérifier l'intégrité des relations
print(f"\n🔗 Vérification des relations:")
try:
    for album in db.query(Album).limit(10).all():
        _ = album.artists  # Force le chargement
        _ = album.images
        _ = album.album_metadata
    print("✅ Toutes les relations sont valides (10 premiers albums)")
except Exception as e:
    print(f"❌ Erreur dans les relations: {e}")

db.close()

print(f"\n🎯 Validation terminée!")
print(f"\n💡 Pour tester l'API:")
print(f"   curl 'http://localhost:8000/api/v1/collection/albums?page_size=5' | python3 -m json.tool")
