#!/usr/bin/env python3
"""Test la correction du champ albums dans les magazines."""

import asyncio
import json
import pytest
from app.database import SessionLocal
from app.services.magazine_generator_service import MagazineGeneratorService
from app.core.config import get_settings

# Debug utility only; skip during automated runs
pytest.skip("Debug magazine fix helper", allow_module_level=True)

async def test_magazine_albums_fix():
    """Générer un magazine pour tester que le fix fonctionne."""
    db = SessionLocal()
    try:
        settings = get_settings()
        service = MagazineGeneratorService(db)
        
        print("🧪 Test du fix - Génération d'un magazine test...\n")
        magazine = await service.generate_magazine()
        
        print(f"✅ Magazine généré!")
        print(f"   Clés retournées: {list(magazine.keys())}")
        print(f"   'albums' présent: {'albums' in magazine}")
        album_count = len(magazine.get('albums', []))
        print(f"   Nombre d'albums: {album_count}")
        print(f"   Nombre de pages: {len(magazine.get('pages', []))}")
        
        if 'albums' in magazine and magazine['albums']:
            samples = magazine['albums'][:3]
            print(f"\n   Premiers albums:")
            for album in samples:
                print(f"      • {album.get('title', 'N/A')} - {album.get('artist', 'N/A')}")
        
        print("\n" + "="*70)
        if album_count > 0:
            print(f"✅ FIX CONFIRMED: Magazine contient {album_count} albums!")
            print(f"   Interface affichera maintenant le bon nombre d'albums")
        else:
            print(f"❌ FIX FAILED: Magazine n'a pas d'albums")
        print("="*70)
        
        return album_count > 0
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_magazine_albums_fix())
    exit(0 if success else 1)
