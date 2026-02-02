#!/usr/bin/env python3
"""Pipeline d'amélioration automatique des données"""

import sys
import os
import subprocess
import time
from datetime import datetime

def run_script(script_name, description):
    """Exécuter un script et retourner le résultat"""
    print('\n' + '='*70)
    print('🔄 {}'.format(description))
    print('='*70)
    
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    try:
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.returncode != 0 and result.stderr:
            print('⚠️  Erreur: {}'.format(result.stderr[:200]))
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print('❌ Script dépassé (timeout 5min)')
        return False
    except Exception as e:
        print('❌ Erreur: {}'.format(str(e)))
        return False

def main():
    print('\n' + '╔' + '='*68 + '╗')
    print('║' + ' '*15 + 'PIPELINE D\'AMÉLIORATION DES DONNÉES' + ' '*19 + '║')
    print('╚' + '='*68 + '╝')
    print('\nDémarrage: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    steps = [
        ('audit_database.py', '1. Audit initial de la base'),
        ('fix_malformed_artists.py', '2. Correction des artistes mal formatés'),
        ('enrich_musicbrainz_images.py', '3. Enrichissement images (MusicBrainz)'),
        ('validate_data.py', '4. Validation des données'),
    ]
    
    results = {}
    
    for script, description in steps:
        success = run_script(script, description)
        results[description] = '✅' if success else '⚠️'
        time.sleep(1)
    
    # Résumé final
    print('\n' + '╔' + '='*68 + '╗')
    print('║' + ' '*25 + 'RÉSUMÉ FINAL' + ' '*31 + '║')
    print('╚' + '='*68 + '╝')
    
    print('\nRésultats:')
    for step, status in results.items():
        print('  {} {}'.format(status, step))
    
    print('\nTerminé: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print('\n' + '='*70)

if __name__ == '__main__':
    main()
