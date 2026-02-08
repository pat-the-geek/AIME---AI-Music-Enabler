#!/usr/bin/env python3
"""Déclencher la génération de magazines par le scheduler et vérifier les fichiers."""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from app.database import SessionLocal
from app.services.scheduler_service import SchedulerService
from app.core.config import get_settings

async def trigger_magazine_generation():
    """Lance la tâche de génération de magazines du scheduler."""
    print("🚀 Démarrage de la génération de magazines du scheduler\n")
    
    # Charger la configuration
    settings = get_settings()
    config = settings.app_config
    
    # Initialiser le scheduler
    scheduler = SchedulerService(config)
    
    db = SessionLocal()
    
    try:
        # Déclencher la génération de magazines
        print("📰 Lancement génération des magazines...")
        await scheduler._generate_magazine_editions()
        print("✅ Génération de magazines terminée\n")
        
        # Afficher les fichiers créés
        print("\n" + "="*70)
        print("📂 Magazines générés:")
        print("="*70)
        
        # Vérifier le répertoire
        magazines_dir = os.path.join(os.path.dirname(__file__), '../data/magazine-editions')
        
        if os.path.exists(magazines_dir):
            files = sorted(os.listdir(magazines_dir), reverse=True)
            json_files = [f for f in files if f.endswith('.json')]
            
            print(f"\n📁 Répertoire: {magazines_dir}")
            print(f"📦 Total fichiers: {len(files)}")
            print(f"📰 Fichiers magazines (JSON): {len(json_files)}\n")
            
            # Afficher les 5 magazines les plus récents
            if json_files:
                print("🆕 5 Magazines les plus récents:")
                for f in json_files[:5]:
                    filepath = os.path.join(magazines_dir, f)
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Charger le magazine pour vérifier son contenu
                    try:
                        with open(filepath, 'r', encoding='utf-8') as jf:
                            mag_data = json.load(jf)
                        
                        album_count = len(mag_data.get('articles', []))
                        print(f"\n   ✅ {f}")
                        print(f"      Taille: {size/1024:.1f} KB")
                        print(f"      Modifié: {mod_time}")
                        print(f"      Articles/Albums: {album_count}")
                    except Exception as e:
                        print(f"   ⚠️  {f} - Erreur lecture: {e}")
            else:
                print("⚠️  Aucun magazine trouvé!")
        else:
            print(f"⚠️  Répertoire non trouvé: {magazines_dir}")
        
        print("\n" + "="*70)
        
        # Afficher un exemple de magazine
        if json_files:
            print("\n📄 Exemple de contenu (premier magazine):")
            print("="*70)
            
            sample_path = os.path.join(magazines_dir, json_files[0])
            with open(sample_path, 'r', encoding='utf-8') as f:
                mag = json.load(f)
            
            print(f"\nMagazine: {json_files[0]}")
            print(f"  Titre: {mag.get('title', 'N/A')}")
            print(f"  Edition: {mag.get('edition', 'N/A')}")
            print(f"  Date: {mag.get('date', 'N/A')}")
            print(f"  Articles: {len(mag.get('articles', []))}")
            
            # Afficher le premier article
            articles = mag.get('articles', [])
            if articles:
                first_article = articles[0]
                print(f"\n  Premier article:")
                print(f"    Titre: {first_article.get('title', 'N/A')[:60]}...")
                print(f"    Type: {first_article.get('type', 'N/A')}")
                if 'album' in first_article:
                    album = first_article['album']
                    print(f"    Album: {album.get('title', 'N/A')}")
                    print(f"    Artiste: {album.get('artist', 'N/A')}")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(trigger_magazine_generation())
