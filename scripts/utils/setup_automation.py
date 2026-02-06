#!/usr/bin/env python3
"""Setup automation: Configure les clés API et teste les connexions."""
import json
from pathlib import Path

print("\n" + "=" * 90)
print("🔧 SETUP AUTOMATION - Configuration des Sources d'Enrichissement")
print("=" * 90)

config_file = Path('./config/enrichment_api_keys.json')

# Charger ou créer le fichier de config
if config_file.exists():
    with open(config_file, 'r') as f:
        config = json.load(f)
    print("\n✓ Fichier de config existant trouvé")
else:
    config = {
        "lastfm": {
            "api_key": "",
            "enabled": False,
            "description": "Récupération images d'artiste"
        },
        "openai": {
            "api_key": "",
            "model": "gpt-3.5-turbo",
            "enabled": False,
            "description": "Génération descriptions via ChatGPT"
        },
        "huggingface": {
            "api_key": "",
            "model": "gpt2",
            "enabled": False,
            "description": "Génération descriptions via Hugging Face"
        },
        "euria": {
            "api_url": "",
            "api_key": "",
            "enabled": False,
            "description": "API Euria personnalisée (si disponible)"
        }
    }
    print("\n✓ Nouveau fichier de config créé")

# ============================================================================
# MENU CONFIGURATION
# ============================================================================

print("\n📋 SOURCES DISPONIBLES:")
print("─" * 90)

for idx, (source, details) in enumerate(config.items(), 1):
    status = "✓ ACTIVÉE" if details.get("enabled") else "✗ désactivée"
    key_status = "✓ Configurée" if details.get("api_key") else "✗ Non configurée"
    print(f"  {idx}. {source.upper():15} - {details['description']}")
    print(f"     Statut: {status:10} | Clé: {key_status}")

print("\n" + "─" * 90)
print("\n🔐 CONFIGURATION DES CLÉS API (laisser vide pour skipper):")
print("─" * 90)

# Last.fm
print("\n1️⃣  Last.fm - Images d'artiste")
print("   Obtenir une clé gratuite: https://www.last.fm/api/account/create")
lastfm_key = input("   Clé API Last.fm (laisser vide si pas de compte): ").strip()
if lastfm_key:
    config["lastfm"]["api_key"] = lastfm_key
    config["lastfm"]["enabled"] = True
    print("   ✅ Configuré")

# OpenAI
print("\n2️⃣  OpenAI - Descriptions via ChatGPT")
print("   Obtenir une clé: https://platform.openai.com/account/api-keys")
openai_key = input("   Clé API OpenAI (laisser vide si pas de compte): ").strip()
if openai_key:
    config["openai"]["api_key"] = openai_key
    config["openai"]["enabled"] = True
    print("   ✅ Configuré")

# Hugging Face
print("\n3️⃣  Hugging Face - Génération locale")
print("   Obtenir une clé: https://huggingface.co/settings/tokens")
hf_key = input("   Clé API Hugging Face (laisser vide pour skipper): ").strip()
if hf_key:
    config["huggingface"]["api_key"] = hf_key
    config["huggingface"]["enabled"] = True
    print("   ✅ Configuré")

# Euria
print("\n4️⃣  API Euria Personnalisée - (si disponible)")
euria_url = input("   URL API Euria (laisser vide si pas disponible): ").strip()
if euria_url:
    euria_key = input("   Clé API Euria: ").strip()
    config["euria"]["api_url"] = euria_url
    config["euria"]["api_key"] = euria_key
    config["euria"]["enabled"] = True
    print("   ✅ Configuré")

# ============================================================================
# SAUVEGARDER ET TESTER
# ============================================================================

config_file.parent.mkdir(parents=True, exist_ok=True)
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("\n" + "─" * 90)
print("✅ Configuration sauvegardée\n")

print("📊 RÉSUMÉ:")
print("─" * 90)
enabled_sources = [s for s, d in config.items() if d.get("enabled")]
print(f"   Sources activées: {len(enabled_sources)}")
for source in enabled_sources:
    print(f"   • {source.upper()}")

print("\n" + "=" * 90)
print("🚀 ÉTAPES SUIVANTES:")
print("─" * 90)
print("   1. python3 auto_enrich_from_api.py")
print("      → Lance l'enrichissement automatique")
print("")
print("   2. python3 refresh_complete.py")
print("      → Applique les données au système")
print("")
print("   3. python3 verify_enrichment.py")
print("      → Valide le résultat")
print("=" * 90 + "\n")
