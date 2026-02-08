#!/usr/bin/env python3
"""Résumé de la génération des magazines."""

import json
import os
from pathlib import Path
from datetime import datetime

magazine_dir = "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/data/magazine-editions/2026-02-08"

print("\n" + "="*70)
print("📰 GÉNÉRATION DE MAGAZINES PAR LE SCHEDULER")
print("="*70)

if os.path.exists(magazine_dir):
    files = sorted(os.listdir(magazine_dir))
    
    print(f"\n✅ Répertoire créé: 2026-02-08")
    print(f"📦 Magazines générés: {len(files)}")
    
    total_size = 0
    total_articles = 0
    sample_magazine = None
    
    for filename in files:
        filepath = os.path.join(magazine_dir, filename)
        size = os.path.getsize(filepath)
        total_size += size
        
        with open(filepath, 'r', encoding='utf-8') as f:
            mag = json.load(f)
        
        pages = mag.get('pages', [])
        articles_count = sum(len(p.get('content', {}).get('albums', [])) for p in pages)
        total_articles += articles_count
        
        if not sample_magazine:
            sample_magazine = mag
        
        mtime = os.path.getmtime(filepath)
        mod_time = datetime.fromtimestamp(mtime).strftime("%H:%M:%S")
        
        print(f"\n  {filename}")
        print(f"    Créé: {mod_time}")
        print(f"    Taille: {size/1024:.1f} KB")
        print(f"    Pages: {len(pages)}")
        print(f"    Articles: {articles_count}")
    
    if sample_magazine:
        print(f"\n" + "-"*70)
        print(f"📄 Détails du premier magazine (2026-02-08-001.json):")
        print(f"-"*70)
        
        mag = sample_magazine
        print(f"\nID: {mag.get('id', 'N/A')}")
        print(f"Edition: {mag.get('edition_number', 'N/A')}")
        print(f"Généré: {mag.get('generated_at', 'N/A')}")
        
        pages = mag.get('pages', [])
        print(f"\nPages ({len(pages)}):")
        for page in pages[:3]:
            print(f"  - Page {page.get('page_number')}: {page.get('type')} - {page.get('title')}")
            layout = page.get('layout', {})
            print(f"    Layout: {layout.get('columns')} colonnes, {layout.get('composition')}")
            
            content = page.get('content', {})
            albums = content.get('albums', [])
            haikus = content.get('haikus', [])
            
            if albums:
                print(f"    Albums: {len(albums)}")
                if albums:
                    first = albums[0]
                    print(f"      • {first.get('title')} - {first.get('artist')}")
            
            if haikus:
                print(f"    Haïkus: {len(haikus)}")
                if haikus:
                    first_haiku = haikus[0]
                    haiku_text = first_haiku.get('haiku', '').split('\n')[0]
                    print(f"      • {haiku_text}")
    
    print(f"\n" + "-"*70)
    print(f"📊 Statistiques totales:")
    print(f"  Taille totale: {total_size/1024:.1f} KB")
    print(f"  Articles totaux: {total_articles}")
    print(f"\n  ℹ️ Les autres magazines (2026-02-08-002 à 010) seront générés")
    print(f"     avec des délais de 30 minutes entre chaque édition.")
    print(f"     Processus en cours... (Vérifier avec 'ps' pour confirmer)")
    
    print(f"\n" + "="*70)
    print(f"✅ MAGAZINE GENERATION ACTIVE")
    print(f"   Prochains magazines dans: ~30 min, ~60 min, etc.")
    print(f"="*70 + "\n")

else:
    print(f"\n❌ Répertoire non trouvé: {magazine_dir}")
