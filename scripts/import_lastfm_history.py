#!/usr/bin/env python3
"""Script d'import de l'historique Last.fm."""
import sys
import os

# Ajouter le chemin du backend au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import requests
import argparse
from datetime import datetime


def import_history(limit=1000, skip_existing=True, base_url="http://localhost:8000"):
    """Importer l'historique Last.fm."""
    print("🎵 Import de l'historique Last.fm")
    print(f"📊 Limite: {limit} tracks")
    print(f"⚙️  Skip existing: {skip_existing}")
    print("-" * 50)
    
    url = f"{base_url}/api/v1/services/lastfm/import-history"
    params = {
        "limit": limit,
        "skip_existing": skip_existing
    }
    
    print(f"🔄 Envoi de la requête...")
    start_time = datetime.now()
    
    try:
        response = requests.post(url, params=params, timeout=600)  # 10 min timeout
        response.raise_for_status()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        result = response.json()
        
        print("\n" + "=" * 50)
        print("✅ IMPORT TERMINÉ!")
        print("=" * 50)
        print(f"⏱️  Durée: {elapsed:.1f}s")
        print(f"📥 Tracks importés: {result.get('tracks_imported', 0)}")
        print(f"⏭️  Tracks ignorés: {result.get('tracks_skipped', 0)}")
        print(f"❌ Erreurs: {result.get('tracks_errors', 0)}")
        print(f"🎨 Albums enrichis: {result.get('albums_enriched', 0)}")
        print(f"📀 Total albums à enrichir: {result.get('total_albums_to_enrich', 0)}")
        print(f"📊 Total scrobbles Last.fm: {result.get('total_scrobbles', 0)}")
        print("=" * 50)
        
        if result.get('total_albums_to_enrich', 0) > result.get('albums_enriched', 0):
            remaining = result.get('total_albums_to_enrich', 0) - result.get('albums_enriched', 0)
            print(f"\n💡 Info: {remaining} albums restent à enrichir.")
            print("   Vous pouvez lancer scripts/enrich_albums.py pour continuer l'enrichissement.")
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: L'import prend trop de temps.")
        print("   Essayez avec une limite plus petite ou augmentez le timeout.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Détails: {e.response.text}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Importer l'historique d'écoute depuis Last.fm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Importer les 500 derniers tracks
  python scripts/import_lastfm_history.py 500
  
  # Importer 2000 tracks sans ignorer les doublons
  python scripts/import_lastfm_history.py 2000 --no-skip-existing
  
  # Importer avec URL custom
  python scripts/import_lastfm_history.py 1000 --url http://localhost:8080
        """
    )
    
    parser.add_argument(
        'limit',
        type=int,
        nargs='?',
        default=1000,
        help='Nombre maximum de tracks à importer (défaut: 1000)'
    )
    
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='Réimporter même les tracks déjà en base'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:8000',
        help='URL du backend API (défaut: http://localhost:8000)'
    )
    
    args = parser.parse_args()
    
    import_history(
        limit=args.limit,
        skip_existing=not args.no_skip_existing,
        base_url=args.url
    )


if __name__ == '__main__':
    main()
