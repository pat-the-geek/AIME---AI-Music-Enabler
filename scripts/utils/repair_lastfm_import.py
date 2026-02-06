#!/usr/bin/env python3
"""Script de réparation complète du dernier import Last.fm."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import subprocess
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_script(script_path, description):
    """Exécuter un script Python."""
    print(f"\n{'='*60}")
    print(f"▶️  {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            ['python3', script_path],
            capture_output=False,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erreur lors de {description}: {e}")
        return False


def main():
    """Exécuter la réparation complète."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + "  🔧 RÉPARATION COMPLÈTE - Import Last.fm".ljust(59) + "║")
    print("║" + f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(59) + "║")
    print("╚" + "=" * 58 + "╝")
    
    print("""
Ce script va:
1. 📊 Diagnostiquer les problèmes actuels
2. 🔧 Corriger les données existantes
3. ✅ Valider les corrections
""")
    
    # Étape 1: Diagnostic
    print("\n" + "▓" * 60)
    print("ÉTAPE 1: DIAGNOSTIC INITIAL")
    print("▓" * 60)
    
    if not run_script(
        os.path.join(base_path, 'check_import_quality.py'),
        "Diagnostic - État actuel"
    ):
        print("\n⚠️  Diagnostic échoué, mais on continue...")
    
    # Étape 2: Corrections
    print("\n" + "▓" * 60)
    print("ÉTAPE 2: APPLICATION DES CORRECTIONS")
    print("▓" * 60)
    
    if not run_script(
        os.path.join(base_path, 'fix_lastfm_import_issues.py'),
        "Correction - Nettoyage et fusion"
    ):
        print("\n❌ Corrections échouées!")
        return False
    
    # Étape 3: Validation
    print("\n" + "▓" * 60)
    print("ÉTAPE 3: VALIDATION FINALE")
    print("▓" * 60)
    
    if not run_script(
        os.path.join(base_path, 'check_import_quality.py'),
        "Validation - État après corrections"
    ):
        print("\n⚠️  Validation échouée")
    
    # Résumé
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + "  ✅ RÉPARATION COMPLÈTE TERMINÉE".ljust(59) + "║")
    print("╚" + "=" * 58 + "╝")
    
    print("""
🎯 Prochaines étapes:

1. Vérifier les résultats dans l'interface web
   → Analytics → Advanced Analytics (total d'écoutes)
   → Collection → Albums (vignettes affichées?)
   → Journal (artistes corrects?)

2. Si tout est OK:
   python scripts/import_lastfm_history.py 500
   (pour importer les 500 derniers scrobbles)

3. Attendre l'enrichissement (5-10 minutes)
   → Images d'album
   → Descriptions IA

📚 Voir docs/LASTFM-IMPORT-FIXES.md pour plus de détails.
""")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
