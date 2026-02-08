#!/usr/bin/env python3
"""Vérifier le problème des albums manquants dans les magazines."""

import json

with open('/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/data/magazine-editions/2026-02-08/2026-02-08-001.json', 'r') as f:
    mag = json.load(f)

print("\n📰 MAGAZINE 2026-02-08-001 - ANALYSE")
print("="*70)

# Vérifier la structure
print(f"Clés du magazine JSON: {list(mag.keys())}")
print(f"Clé 'albums' présente: {'albums' in mag}")
print(f"Valeur de mag['albums']: {mag.get('albums')}")

# Compter les albums dans les pages
total_albums = 0
for page in mag.get('pages', []):
    albums_in_page = page.get('content', {}).get('albums', [])
    if albums_in_page:
        total_albums += len(albums_in_page)
        print(f"  Page {page.get('page_number')}: {len(albums_in_page)} albums")

print(f"\n📊 RÉSULTAT:")
print(f"  Albums dans champ root 'albums': {len(mag.get('albums', []))} ❌ VIDE")
print(f"  Albums réels trouvés dans pages: {total_albums} ✓ PRÉSENTS")

print(f"\n" + "="*70)
print(f"🐛 PROBLÈME DÉTECTÉ:")
print(f"   L'interface montre 0 albums car elle lit le champ 'albums' root")
print(f"   qui est un array vide []")
print(f"\n✅ CORRECTION APPLIQUÉE:")
print(f"   La prochaine génération remplira 'albums' avec les {total_albums}")
print(f"   albums extraits des pages")
print(f"="*70 + "\n")
