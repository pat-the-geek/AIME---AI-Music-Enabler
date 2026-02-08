#!/usr/bin/env python3
"""Déclencher les exports du scheduler pour vérifier les fichiers générés."""

import asyncio
import os
from pathlib import Path
from app.database import SessionLocal
from app.services.scheduler_service import SchedulerService
from app.core.config import get_settings

async def trigger_exports():
    """Lance les tâches d'export JSON et Markdown du scheduler."""
    print("🚀 Démarrage des exports du scheduler\n")
    
    # Charger la configuration
    settings = get_settings()
    config = settings.app_config
    
    # Initialiser le scheduler
    scheduler = SchedulerService(config)
    
    db = SessionLocal()
    
    try:
        # Déclencher l'export Markdown
        print("📝 Lancement export Markdown...")
        await scheduler._export_collection_markdown()
        print("✅ Export Markdown terminé\n")
        
        # Déclencher l'export JSON
        print("💾 Lancement export JSON...")
        await scheduler._export_collection_json()
        print("✅ Export JSON terminé\n")
        
        # Afficher les fichiers créés
        print("\n" + "="*60)
        print("📂 Fichiers générés:")
        print("="*60)
        
        # Déterminer le répertoire de sortie
        current_dir = os.path.abspath(__file__)
        for _ in range(2):
            current_dir = os.path.dirname(current_dir)
        project_root = current_dir
        output_dir = os.path.join(
            project_root, 
            config.get('scheduler', {}).get('output_dir', 'Scheduled Output')
        )
        
        if os.path.exists(output_dir):
            files = sorted(os.listdir(output_dir), reverse=True)
            
            # Afficher les fichiers récents
            print(f"\n📁 Répertoire: {output_dir}\n")
            
            markdown_files = [f for f in files if f.endswith('.md')]
            json_files = [f for f in files if f.endswith('.json')]
            
            if markdown_files:
                print("📝 Fichiers Markdown:")
                for f in markdown_files[:3]:
                    filepath = os.path.join(output_dir, f)
                    size = os.path.getsize(filepath)
                    print(f"   ✓ {f} ({size:,} bytes)")
            
            if json_files:
                print("\n💾 Fichiers JSON:")
                for f in json_files[:3]:
                    filepath = os.path.join(output_dir, f)
                    size = os.path.getsize(filepath)
                    print(f"   ✓ {f} ({size:,} bytes)")
            
            # Afficher les derniers fichiers créés
            if files:
                print("\n🆕 Fichiers les plus récents:")
                for f in files[:5]:
                    filepath = os.path.join(output_dir, f)
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    from datetime import datetime
                    mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"   {f}")
                    print(f"      Taille: {size:,} bytes | Modifié: {mod_time}")
        else:
            print(f"⚠️  Répertoire non trouvé: {output_dir}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(trigger_exports())
