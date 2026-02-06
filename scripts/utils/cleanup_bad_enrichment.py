#!/usr/bin/env python3
"""Nettoie les descriptions template erronées et réapplique les bonnes."""
import sys
sys.path.insert(0, './backend')

from backend.app.database import SessionLocal
from backend.app.models import Album, Image

db = SessionLocal()

print("\n" + "=" * 80)
print("🧹 NETTOYAGE DES DESCRIPTIONS TEMPLATE ERRONÉES")
print("=" * 80)

# Chercher et supprimer les descriptions template
bad_desc_count = 0
albums_with_bad_desc = db.query(Album).filter(
    Album.ai_description.isnot(None),
    Album.ai_description.like('[Remplir%')
).all()

print(f"\n📝 Suppression des descriptions template...")
print(f"   Trouvées: {len(albums_with_bad_desc)}")

for album in albums_with_bad_desc:
    album.ai_description = None
    bad_desc_count += 1

db.commit()
print(f"   ✅ Supprimées: {bad_desc_count}")

# Supprimer aussi les images d'artiste invalides si nécessaire
invalid_images = db.query(Image).filter(
    Image.image_type == 'artist',
    Image.source == 'discogs',
    Image.url.like('[%')  # URLs commençant par [  
).all()

if invalid_images:
    print(f"\n🖼️  Suppression des URLs d'image invalides...")
    print(f"   Trouvées: {len(invalid_images)}")
    for img in invalid_images:
        db.delete(img)
    db.commit()
    print(f"   ✅ Supprimées: {len(invalid_images)}")

print("\n" + "=" * 80)
print("✅ Nettoyage complet!")
print("=" * 80 + "\n")

db.close()
