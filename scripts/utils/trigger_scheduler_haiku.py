#!/usr/bin/env python3
"""
Script pour déclencher manuellement la génération de haiku par le scheduler
"""

import asyncio
import os
import sys
from pathlib import Path

# Ajouter le backend au chemin
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Configuration
os.environ.setdefault("ENV", "development")

async def trigger_haiku():
    """Déclenche la génération de haiku."""
    from app.services.scheduler_service import SchedulerService
    from app.config import get_config
    
    try:
        config = get_config()
        scheduler = SchedulerService(config)
        
        print("\n" + "="*80)
        print("🎋 DÉCLENCHEMENT MANUEL - GÉNÉRATION DE HAIKU")
        print("="*80 + "\n")
        
        # Appeler directement la méthode
        await scheduler._generate_random_haikus()
        
        print("\n" + "="*80)
        print("✅ GÉNÉRATION COMPLÉTÉE")
        print("="*80)
        print("\nVérifier le fichier généré dans: Scheduled Output/")
        print()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(trigger_haiku())
    sys.exit(exit_code)
