#!/usr/bin/env python3
"""Script de test avec exemples de descriptions Euria et images artiste."""
import json
from pathlib import Path

print("\n" + "=" * 80)
print("📝 REMPLISSAGE DE TEST - Exemples Descriptions Euria + Images")
print("=" * 80)

# ============================================================================
# 1. CHARGER ET REMPLIR LES DESCRIPTIONS EURIA
# ============================================================================
euria_path = Path('./data/euria_descriptions.json')

if euria_path.exists():
    with open(euria_path, 'r', encoding='utf-8') as f:
        euria_data = json.load(f)
    
    # Ajouter quelques descriptions de test
    test_descriptions = {
        "Deadbeat": "Tame Impala's latest exploration into electronic and psychedelic soundscapes, released in 2025. A vibrant journey through modular synths and hypnotic rhythms.",
        "Innerspeaker": "Tame Impala's 2014 debut album, a psychedelic rock masterpiece featuring intricate guitar work and layered production. Kevin Parker's creative vision at its finest.",
        "The Slow Rush": "A genre-defying album from 2022 that blends electronic, pop, and psychedelic elements. Introspective lyrics paired with lush production.",
        "Currents": "2022 release showcasing Tame Impala's evolution towards more electronic and dance-oriented sounds while maintaining its psychedelic core.",
        "Lonerism": "2023 release that captures the essence of introspection and solitude through layered production and hypnotic melodies.",
    }
    
    updated = 0
    for title, description in test_descriptions.items():
        if title in euria_data['data']:
            euria_data['data'][title] = description
            updated += 1
            print(f"  ✓ {title}")
    
    # Sauvegarder les modifications
    with open(euria_path, 'w', encoding='utf-8') as f:
        json.dump(euria_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ {updated} descriptions Euria ajoutées")
else:
    print(f"⚠️  Fichier {euria_path} non trouvé")

# ============================================================================
# 2. CHARGER ET REMPLIR LES IMAGES ARTISTE
# ============================================================================
artist_img_path = Path('./data/artist_images.json')

if artist_img_path.exists():
    with open(artist_img_path, 'r', encoding='utf-8') as f:
        artist_data = json.load(f)
    
    # Ajouter quelques images test
    test_images = {
        "Tame Impala": "https://i.discogs.com/FnGF8pCrCzWPRfVKxLPVeOBH1z7eFoJH7Gvn4CqVtbY/rs:fit/g:sm/q:90/h:300/w:300/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9BLTE0NjMw/NzA2LTEzNzc2NTUx/MTMtNjkyNi5qcGVn.jpeg",
        "The Young Gods": "https://i.discogs.com/qazWV92JvAB7KqH6a_7_UQKl3N_OxUQ8mMkGUDyIqm0/rs:fit/g:sm/q:90/h:300/w:300/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9BLTI4MzQ4/MTE0LTE0NjY4NDQ4/MDEtMjAzOC5qcGVn.jpeg",
        "Pink Floyd": "https://i.discogs.com/lPkwc9RLQYY6GIvDw1m5vr-tFO5sFW3HvKdLm3mIvj8/rs:fit/g:sm/q:90/h:300/w:300/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9BLTI1OTMz/Ny0xMjQ3NDY5NzI3/LWpwZWc.jpeg",
        "The Rolling Stones": "https://i.discogs.com/j8DKQP-sE5ORFWRHmDZfKGtSPCLvXmBu9aQbZS89X3M/rs:fit/g:sm/q:90/h:300/w:300/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9BLTU2ODA4/NDEtMTIwMDA0MjE2/OS5qcGVn.jpeg",
    }
    
    updated = 0
    for artist, url in test_images.items():
        if artist in artist_data['data']:
            artist_data['data'][artist] = url
            updated += 1
            print(f"  ✓ {artist}")
    
    # Sauvegarder les modifications
    with open(artist_img_path, 'w', encoding='utf-8') as f:
        json.dump(artist_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ {updated} images artiste ajoutées")
else:
    print(f"⚠️  Fichier {artist_img_path} non trouvé")

print("\n" + "=" * 80)
print("📝 Exemples ajoutés:")
print("   - 5 descriptions Tame Impala")
print("   - 4 images d'artiste (Tame Impala, The Young Gods, Pink Floyd, Rolling Stones)")
print("\n💡 Exécutez maintenant: python3 refresh_complete.py")
print("=" * 80 + "\n")
