#!/usr/bin/env python3
"""ÉTAPE 2: Enrichit les données du JSON."""
import json
import time
from datetime import datetime

print("\n" + "=" * 80)
print("🔧 ÉTAPE 2: ENRICHISSEMENT DES DONNÉES")
print("=" * 80)

# Charger le fichier de l'étape 1
input_file = './discogs_data_step1.json'
print(f"\n📖 Chargement {input_file}...")

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"❌ Fichier {input_file} non trouvé!")
    print("   Exécute d'abord: python3 step1_fetch_discogs.py")
    exit(1)

albums = data['albums']
print(f"✅ {len(albums)} albums chargés\n")

# Enrichir les données
print("⚙️ Enrichissement des données... ")
start_time = time.time()

for idx, album in enumerate(albums, 1):
    # Afficher progression tous les 50 albums
    if idx % 50 == 0:
        print(f"  ✓ {idx}/{len(albums)} albums enrichis")
    
    # Déterminer le support
    support = "Unknown"
    if album.get('formats'):
        fmt = album['formats'][0]
        if 'Vinyl' in fmt or 'LP' in fmt:
            support = "Vinyle"
        elif 'CD' in fmt:
            support = "CD"
        elif 'Digital' in fmt:
            support = "Digital"
        elif '33' in fmt or '45' in fmt or '78' in fmt:
            support = "Vinyle"
    
    album['support'] = support
    album['enriched'] = True
    
    # Nettoyer les artistes (supprimer doublons/espaces)
    artists = []
    for artist in album.get('artists', []):
        artist_cleaned = artist.strip() if isinstance(artist, str) else str(artist)
        if artist_cleaned and artist_cleaned not in artists:
            artists.append(artist_cleaned)
    album['artists'] = artists

elapsed = time.time() - start_time

# Mettre à jour les métadonnées
data['metadata']['steps_completed'].append('enrich')
data['metadata']['enriched_at'] = datetime.now().isoformat()
data['metadata']['enrichment_time'] = elapsed

# Statistiques d'enrichissement
tame_impala_count = sum(1 for a in albums if any('Tame Impala' in artist for artist in a.get('artists', [])))
support_stats = {}
for album in albums:
    support = album.get('support', 'Unknown')
    support_stats[support] = support_stats.get(support, 0) + 1

# Sauvegarder
output_file = './discogs_data_step2.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n✅ Étape 2 complétée")
print("=" * 80)
print(f"📊 Résumé:")
print(f"  Albums: {len(albums)}")
print(f"  Temps: {elapsed:.1f}s")
print(f"  Support détecté:")
for support, count in sorted(support_stats.items()):
    print(f"    • {support}: {count}")
print(f"  Tame Impala trouvés: {tame_impala_count}")
print(f"  Fichier: {output_file}")
print("=" * 80 + "\n")
