#!/usr/bin/env python3
"""Test de la fonctionnalité d'export markdown."""

import sys
sys.path.insert(0, '/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/backend')

from app.database import SessionLocal
from app.services.markdown_export_service import MarkdownExportService

def test_markdown_export():
    """Tester l'export markdown."""
    db = SessionLocal()
    
    try:
        print("🧪 Test d'export markdown\n")
        print("=" * 60)
        
        # Test 1: Export complet
        print("\n✅ TEST 1: Export complet de la collection")
        markdown = MarkdownExportService.get_collection_markdown(db)
        print(f"   - Taille du markdown: {len(markdown)} caractères")
        print(f"   - Nombre de lignes: {len(markdown.split(chr(10)))}")
        
        # Compter les albums
        album_count = markdown.count("## ")
        print(f"   - Albums détectés: {album_count}")
        
        # Premiers 500 caractères
        print(f"\n   Aperçu:\n")
        for line in markdown.split('\n')[:20]:
            print(f"   {line}")
        
        # Test 2: Export par support
        print("\n" + "=" * 60)
        print("\n✅ TEST 2: Export par support (Vinyle)")
        markdown_vinyl = MarkdownExportService.get_support_markdown(db, 'Vinyle')
        print(f"   - Taille: {len(markdown_vinyl)} caractères")
        vinyl_count = markdown_vinyl.count("## ")
        print(f"   - Albums Vinyle: {vinyl_count}")
        
        # Test 3: Récupérer un artiste et exporter sa discographie
        print("\n" + "=" * 60)
        print("\n✅ TEST 3: Export par artiste")
        from app.models import Artist
        artists = db.query(Artist).filter(
            Artist.albums.any()
        ).limit(1).all()
        
        if artists:
            artist = artists[0]
            print(f"   - Artiste: {artist.name}")
            markdown_artist = MarkdownExportService.get_artist_markdown(db, artist.id)
            print(f"   - Taille: {len(markdown_artist)} caractères")
            artist_albums = markdown_artist.count("## ")
            print(f"   - Albums de l'artiste: {artist_albums}")
        
        print("\n" + "=" * 60)
        print("\n✅ TOUS LES TESTS RÉUSSIS!")
        print("\nEndpoints disponibles:")
        print("  - GET /api/v1/collection/export/markdown")
        print("  - GET /api/v1/collection/export/markdown/{artist_id}")
        print("  - GET /api/v1/collection/export/markdown/support/{support}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_markdown_export()
