#!/usr/bin/env python3
"""Diagnostic script to check The Young Gods artist image in database"""
import sys
sys.path.insert(0, '/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend')

from app.database import SessionLocal
from app.models import Artist, Image, Album, album_artist

db = SessionLocal()

print("\n" + "="*60)
print("🔍 DIAGNOSTIC: The Young Gods Artist Image")
print("="*60 + "\n")

# Find The Young Gods artist
artist = db.query(Artist).filter(Artist.name == 'The Young Gods').first()
if not artist:
    print("❌ Artist 'The Young Gods' not found!")
    db.close()
    sys.exit(1)

print(f"✅ Found artist: {artist.name}")
print(f"   ID: {artist.id}\n")

# Check for images of this artist
images = db.query(Image).filter(Image.artist_id == artist.id).all()
print(f"📸 Total images for this artist: {len(images)}\n")

for img in images:
    print(f"   - Type: {img.image_type}")
    print(f"     URL: {img.url[:80]}...")
    print(f"     Source: {img.source}\n")

# Try the specific query used in code
artist_image = db.query(Image).filter(
    Image.artist_id == artist.id,
    Image.image_type == 'artist'
).first()

if artist_image:
    print(f"✅ Found artist image with type='artist':")
    print(f"   URL: {artist_image.url[:80]}...")
else:
    print(f"❌ No image found with image_type='artist'")

# Check albums
albums = db.query(Album).join(album_artist).filter(
    album_artist.c.artist_id == artist.id
).all()

print(f"\n📀 Albums by this artist: {len(albums)}")
for album in albums:
    print(f"   - {album.title} (ID: {album.id})")

db.close()
print("\n" + "="*60)
