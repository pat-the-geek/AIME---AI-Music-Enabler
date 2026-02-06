#!/usr/bin/env python3
"""Génère les templates pour les descriptions Euria et images d'artiste."""
import sys
sys.path.insert(0, './backend')

import json
from pathlib import Path
from backend.app.database import SessionLocal
from backend.app.models import Album, Artist

print("\n" + "=" * 80)
print("📝 GÉNÉRATEUR DE TEMPLATES - DESCRIPTIONS EURIA + IMAGES ARTISTE")
print("=" * 80)

db = SessionLocal()

# ============================================================================
# 1. GÉNÉRER TEMPLATE DESCRIPTIONS EURIA
# ============================================================================
print("\n📝 Création du template descriptions Euria...")

# Récupérer tous les albums Discogs
discogs_albums = db.query(Album).filter_by(source='discogs').all()
print(f"   {len(discogs_albums)} albums Discogs trouvés")

# Créer le template
euria_template = {
    "description": "Format: titre de l'album -> description (max 2000 caractères)",
    "data": {}
}

for album in discogs_albums:
    euria_template["data"][album.title] = f"[Remplir la description pour: {album.title} ({album.year})]"

# Sauvegarder le template
euria_path = Path('./data/euria_descriptions.json')
euria_path.parent.mkdir(parents=True, exist_ok=True)

with open(euria_path, 'w', encoding='utf-8') as f:
    json.dump(euria_template, f, ensure_ascii=False, indent=2)

print(f"   ✅ Template créé: {euria_path}")
print(f"   📊 Contient {len(euria_template['data'])} entrées")

# ============================================================================
# 2. GÉNÉRER TEMPLATE IMAGES ARTISTE
# ============================================================================
print("\n🖼️  Création du template images artiste...")

# Récupérer tous les artistes
all_artists = db.query(Artist).all()
print(f"   {len(all_artists)} artistes trouvés")

# Créer le template
artist_img_template = {
    "description": "Format: nom de l'artiste -> URL de l'image (max 1000 caractères)",
    "data": {}
}

for artist in all_artists:
    artist_img_template["data"][artist.name] = "[URL de l'image de l'artiste]"

# Sauvegarder le template
artist_img_path = Path('./data/artist_images.json')
artist_img_path.parent.mkdir(parents=True, exist_ok=True)

with open(artist_img_path, 'w', encoding='utf-8') as f:
    json.dump(artist_img_template, f, ensure_ascii=False, indent=2)

print(f"   ✅ Template créé: {artist_img_path}")
print(f"   📊 Contient {len(artist_img_template['data'])} entrées")

# ============================================================================
# 3. RÉSUMÉ
# ============================================================================
print("\n" + "=" * 80)
print("✅ TEMPLATES CRÉÉS")
print("=" * 80)
print("""
📖 Prochaines étapes:
   1. Ouvrez ./data/euria_descriptions.json
   2. Remplissez les descriptions Euria pour chaque album
   3. Ouvrez ./data/artist_images.json
   4. Ajoutez les URLs des images pour chaque artiste
   5. Exécutez: python3 refresh_complete.py

💡 Formats:
   - Descriptions: texte libre, max 2000 caractères
   - Images artiste: URL complète commençant par http(s)://
   - Laisser blank pour ignorer une entrée
""".strip())

print("\n" + "=" * 80 + "\n")

db.close()
