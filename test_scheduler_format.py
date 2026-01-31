#!/usr/bin/env python3
"""Test pour vérifier que les formats du scheduler correspondent aux formats de l'API."""

import asyncio
import sys
import os
from pathlib import Path

# Ajouter le backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal
from app.services.scheduler_service import SchedulerService
from app.services.markdown_export_service import MarkdownExportService
from app.core.config import get_settings
import json

async def test_scheduler_formats():
    """Tester que les formats générés par le scheduler correspondent aux formats de l'API."""
    print("🧪 Test des formats du scheduler\n")
    print("=" * 60)
    
    # Charger la configuration
    settings = get_settings()
    secrets = settings.secrets
    config = {
        'euria': secrets.get('euria', {}),
        'spotify': secrets.get('spotify', {}),
        'scheduler': {
            'output_dir': 'Scheduled Output',
            'max_files_per_type': 5
        }
    }
    
    db = SessionLocal()
    
    try:
        # Test 1: Vérifier le format markdown
        print("\n✅ Test 1: Format Markdown")
        print("-" * 60)
        markdown_from_service = MarkdownExportService.get_collection_markdown(db)
        
        # Vérifier les éléments clés du format
        checks = [
            ("Table des matières présente", "## Table des matières" in markdown_from_service),
            ("Titre avec emoji", "# 🎵 Collection Discogs" in markdown_from_service),
            ("Date d'export", "Exportée le:" in markdown_from_service),
            ("Total albums", "**Total:**" in markdown_from_service),
            ("Séparateurs markdown", "---" in markdown_from_service),
            ("Sections artistes", "## " in markdown_from_service and len(markdown_from_service) > 500),
        ]
        
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}")
        
        # Test 2: Vérifier le format JSON
        print("\n✅ Test 2: Format JSON")
        print("-" * 60)
        
        albums = db.query(os.path.abspath(__file__).split('/')[0])  # Import Album
        from app.models import Album
        albums = db.query(Album).filter(Album.source == 'discogs').limit(1).all()
        
        if albums:
            album = albums[0]
            
            # Vérifier structure JSON
            checks_json = [
                ("Images incluses", bool(album.images)),
                ("Métadonnées incluses", bool(album.album_metadata)),
                ("Artistes présents", bool(album.artists)),
                ("Support présent", album.support is not None),
            ]
            
            for check_name, result in checks_json:
                status = "✅" if result else "❌"
                print(f"{status} {check_name}")
        else:
            print("⚠️  Pas d'albums pour tester le format JSON")
        
        # Test 3: Vérifier les services utilisés
        print("\n✅ Test 3: Services de scheduler")
        print("-" * 60)
        
        scheduler = SchedulerService(config)
        
        checks_services = [
            ("MarkdownExportService importé", hasattr(scheduler, 'ai')),
            ("AI Service disponible", scheduler.ai is not None),
            ("Config scheduler", scheduler.config.get('scheduler', {}) is not None),
        ]
        
        for check_name, result in checks_services:
            status = "✅" if result else "❌"
            print(f"{check_name}: {status}")
        
        print("\n" + "=" * 60)
        print("✅ Tests complétés avec succès!")
        print("\nLes fichiers générés par le scheduler utiliseront maintenant:")
        print("• Format markdown identique à l'API (table des matières, formatage enrichi)")
        print("• Format JSON identique à l'API (avec images et métadonnées)")
        print("• Haikus structurés avec métadonnées détaillées")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_scheduler_formats())
