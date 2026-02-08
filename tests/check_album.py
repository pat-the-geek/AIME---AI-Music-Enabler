#!/usr/bin/env python3
"""Check if album exists in database"""
import sys
sys.path.insert(0, '/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler')

from backend.app.database import SessionLocal
from backend.app.models.album import Album
from backend.app.models.artist import Artist

db = SessionLocal()
try:
    # Chercher l'album exact
    albums = db.query(Album).filter(
        (Album.title.ilike('%Data Mirage%')) | 
        (Album.title.ilike('%Tangram%'))
    ).all()
    
    print(f"🔍 Albums trouvés: {len(albums)}")
    for album in albums:
        artist_names = ", ".join([a.name for a in album.artists])
        print(f"\n✅ {album.id}: {album.title}")
        print(f"   Artistes: {artist_names}")
        print(f"   Année: {album.year}")
        print(f"   Spotify ID: {album.spotify_id}")
        print(f"   Source: {album.source}")
        
    if not albums:
        print("\n❌ Aucun album trouvé avec 'Data Mirage' ou 'Tangram'")
        
        # Chercher les albums de The Young Gods
        print("\n🎨 Recherche des albums de The Young Gods...")
        young_gods = db.query(Artist).filter(Artist.name == "The Young Gods").first()
        if young_gods:
            print(f"   Artiste trouvé: {young_gods.name}")
            print(f"   Albums ({len(young_gods.albums)}):")
            for a in young_gods.albums[:15]:
                print(f"     - {a.title} ({a.year})")
        else:
            print("   ❌ Artist 'The Young Gods' not found")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
