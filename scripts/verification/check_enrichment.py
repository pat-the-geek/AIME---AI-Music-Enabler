#!/usr/bin/env python3
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Artist, Image

db = SessionLocal()

print("=" * 80)
print("🔍 DIAGNOSTIC ENRICHISSEMENT EURIA")
print("=" * 80)

# Stats générales
total_albums = db.query(Album).count()
total_artists = db.query(Artist).count()
total_images = db.query(Image).count()

print(f"\n📊 STATS GÉNÉRALES:")
print(f"  Albums en BD: {total_albums}")
print(f"  Artistes en BD: {total_artists}")
print(f"  Images en BD: {total_images}")

# Vérifier descriptions Euria
albums_with_euria = db.query(Album).filter(Album.euria_description.isnot(None)).count()
print(f"\n✏️ DESCRIPTIONS EURIA:")
print(f"  Albums avec description: {albums_with_euria}/{total_albums}")

if albums_with_euria > 0:
    print(f"  ✅ {albums_with_euria} descriptions stockées")
else:
    print(f"  ❌ AUCUNE description stockée!")

# Exemples
print(f"\n📋 EXEMPLES D'ALBUMS (3 premiers):")
albums = db.query(Album).limit(3).all()
for i, album in enumerate(albums, 1):
    desc = album.euria_description[:80] if album.euria_description else "❌ VIDE"
    print(f"  {i}. {album.title}")
    print(f"     Description: {desc}...")

# Vérifier images artistes
artists_with_img = db.query(Artist).filter(Artist.image_url.isnot(None)).count()
print(f"\n🖼️ IMAGES D'ARTISTES:")
print(f"  Artistes avec image: {artists_with_img}/{total_artists}")

if artists_with_img > 0:
    print(f"  ✅ {artists_with_img} images téléchargées")
else:
    print(f"  ⚠️ Aucune image d'artiste stockée")

db.close()
print("\n" + "=" * 80)
