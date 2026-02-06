#!/usr/bin/env python3
"""Helper pour enrichir les descriptions Euria depuis diverses sources."""
import sys
sys.path.insert(0, './backend')

import json
from pathlib import Path

print("\n" + "=" * 80)
print("🔧 HELPER ENRICHISSEMENT DESCRIPTIONS")
print("=" * 80)

# Chemins des fichiers
euria_path = Path('./data/euria_descriptions.json')
artist_img_path = Path('./data/artist_images.json')

# ============================================================================
# 1. CHARGER LE TEMPLATE EURIA
# ============================================================================
if euria_path.exists():
    with open(euria_path, 'r', encoding='utf-8') as f:
        euria_data = json.load(f)
    
    total = len(euria_data['data'])
    filled = len([v for v in euria_data['data'].values() if v and not v.startswith('[Remplir')])
    
    print(f"\n📝 Descriptions Euria:")
    print(f"   Total entrées: {total}")
    print(f"   Remplies: {filled}")
    print(f"   À remplir: {total - filled}")
    
    if filled > 0:
        print(f"   Exemples remplis:")
        for title, desc in list(euria_data['data'].items())[:3]:
            if desc and not desc.startswith('[Remplir'):
                print(f"   ✓ {title}: {desc[:60]}...")
else:
    print(f"\n⚠️  Fichier {euria_path} non trouvé")
    print(f"   Exécutez: python3 generate_enrichment_templates.py")

# ============================================================================
# 2. CHARGER LE TEMPLATE IMAGES ARTISTE
# ============================================================================
if artist_img_path.exists():
    with open(artist_img_path, 'r', encoding='utf-8') as f:
        artist_data = json.load(f)
    
    total = len(artist_data['data'])
    filled = len([v for v in artist_data['data'].values() if v and not v.startswith('[')])
    
    print(f"\n🖼️  Images Artiste:")
    print(f"   Total entrées: {total}")
    print(f"   Remplies: {filled}")
    print(f"   À remplir: {total - filled}")
    
    if filled > 0:
        print(f"   Exemples remplis:")
        count = 0
        for artist, url in artist_data['data'].items():
            if url and not url.startswith('['):
                print(f"   ✓ {artist}: {url[:60]}...")
                count += 1
                if count >= 3:
                    break
else:
    print(f"\n⚠️  Fichier {artist_img_path} non trouvé")
    print(f"   Exécutez: python3 generate_enrichment_templates.py")

# ============================================================================
# 3. INSTRUCTIONS
# ============================================================================
print("\n" + "=" * 80)
print("📖 INSTRUCTIONS D'UTILISATION:")
print("=" * 80)
print("""
Étape 1: Remplir les descriptions Euria
   - Ouvrez ./data/euria_descriptions.json
   - Pour chaque album, remplacez "[Remplir...]" par la description réelle
   - Format: texte libre, max 2000 caractères
   - Exemple:
     "The Dark Side of the Moon": "Pink Floyd masterpiece from 1973..."

Étape 2: Ajouter les images d'artiste (optionnel)
   - Ouvrez ./data/artist_images.json
   - Pour chaque artiste, remplacez ["[URL...]"] par l'URL réelle
   - Format: URL complète (http(s)://...)
   - Exemple:
     "Pink Floyd": "https://example.com/pink-floyd.jpg"

Étape 3: Exécuter le refresh complet
   - Lancez: python3 refresh_complete.py
   - Vérifiez les logs pour voir les descriptions appliquées

Étape 4: Vérification
   - Les descriptions devraient être dans le champ 'ai_description' des albums
   - Les images d'artiste devraient apparaître dans les relations Image
""".strip())

print("\n" + "=" * 80 + "\n")
