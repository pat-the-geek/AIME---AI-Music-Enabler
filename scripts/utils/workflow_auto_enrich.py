#!/usr/bin/env python3
"""
🚀 WORKFLOW COMPLET AUTO-ENRICHISSEMENT
Orchestration complète: Configuration → Enrichissement → Validation
"""

import subprocess
import sys
from pathlib import Path
import json

print("\n" + "=" * 90)
print("🚀 WORKFLOW AUTO-ENRICHISSEMENT - ORCHESTRATION COMPLÈTE")
print("=" * 90)

# ============================================================================
# ÉTAPE 0: VÉRIFIER LES DÉPENDANCES
# ============================================================================

print("\n[0/4] Vérification des dépendances...")
print("─" * 90)

required_packages = {
    'requests': 'HTTP client',
    'sqlalchemy': 'ORM database',
}

missing_packages = []
for package, description in required_packages.items():
    try:
        __import__(package)
        print(f"  ✓ {package:20} ({description})")
    except ImportError:
        print(f"  ✗ {package:20} ({description}) - à installer")
        missing_packages.append(package)

if missing_packages:
    print(f"\n⚠️  Packages manquants: {', '.join(missing_packages)}")
    print("   Installez avec: pip install " + " ".join(missing_packages))
    sys.exit(1)

# ============================================================================
# ÉTAPE 1: CONFIGURATION
# ============================================================================

print("\n[1/4] Configuration des sources API...")
print("─" * 90)

config_file = Path('./config/enrichment_api_keys.json')

if config_file.exists():
    print("✓ Configuration existante détectée")
else:
    print("\n⚠️  Aucune configuration trouvée")
    
    response = input("\nVoulez-vous configurer les sources API? (o/n) [o]: ").strip().lower()
    if response != 'n':
        print("\nLancement du setup...")
        result = subprocess.run([sys.executable, 'setup_automation.py'])
        if result.returncode != 0:
            print("❌ Setup échoué")
            sys.exit(1)
    else:
        print("⚠️  Continuant sans configuration (utilisant templates par défaut)")

# Afficher config actuelle
if config_file.exists():
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    enabled_sources = [s for s, c in config.items() if c.get("enabled")]
    print(f"\n📋 Sources activées: {len(enabled_sources)}")
    for source in enabled_sources:
        print(f"   • {source}")

# ============================================================================
# ÉTAPE 2: ENRICHISSEMENT
# ============================================================================

print("\n[2/4] Enrichissement automatique...")
print("─" * 90)

print("\nOptions:")
print("  a) Template local (pas d'API requis)")
print("  b) Avec Last.fm (images artiste)")
print("  c) Intégration complète multi-source")
print("  s) Passer cette étape (utiliser données existantes)")

choice = input("\nSélectionner [c]: ").strip().lower() or 'c'

if choice == 's':
    print("⏭️  Enrichissement skippé")
elif choice == 'a':
    print("\nLancement: Template local uniquement...")
    result = subprocess.run([sys.executable, 'auto_enrich_from_api.py', '--no-refresh'])
elif choice == 'b' or choice == 'c':
    print("\nLancement: Enrichissement intégré multi-source...")
    result = subprocess.run([sys.executable, 'auto_enrich_integrated.py', '--no-refresh'])
    
    if result.returncode != 0:
        print("❌ Enrichissement échoué")
        sys.exit(1)
else:
    print("⚠️  Choix invalide, continuant...")

# ============================================================================
# ÉTAPE 3: REFRESH & APPLICATION
# ============================================================================

print("\n[3/4] Application des données au système...")
print("─" * 90)

print("\nLancement: refresh_complete.py")
result = subprocess.run([sys.executable, 'refresh_complete.py'])

if result.returncode != 0:
    print("\n❌ Refresh échoué")
    sys.exit(1)

# ============================================================================
# ÉTAPE 4: VALIDATION
# ============================================================================

print("\n[4/4] Validation et rapport final...")
print("─" * 90)

print("\nLancement: Verification...")
result = subprocess.run([sys.executable, 'verify_enrichment.py'])

if result.returncode == 0:
    print("\n✅ Vérification réussie")
else:
    print("\n⚠️  Vérification échouée")

# ============================================================================
# RAPPORT FINAL
# ============================================================================

print("\n" + "=" * 90)
print("📊 RÉSUMÉ DU WORKFLOW")
print("=" * 90)

print("""
✨ AUTO-ENRICHISSEMENT COMPLÉTÉ AVEC SUCCÈS

Étapes:
  ✓ [1/4] Configuration API
  ✓ [2/4] Enrichissement automatique
  ✓ [3/4] Application des données
  ✓ [4/4] Validation

Prochaines étapes:
  □ Vérifier les résultats dans l'interface web (http://localhost:3000)
  □ Activer les APIs supplémentaires (Spotify, OpenAI) si souhaité
  □ Enrichir manuellement les descriptions non-remplies
  □ Exécuter le full sync: python3 run_complete_sync.py

Documentation:
  - Guide complet: enrichment_api_examples.py
  - Configuration API: config/enrichment_api_keys.json
  - Données enrichies: data/euria_descriptions.json, data/artist_images.json
""")

print("=" * 90 + "\n")
