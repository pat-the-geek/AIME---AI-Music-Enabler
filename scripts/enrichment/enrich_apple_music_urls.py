#!/usr/bin/env python3
"""
🍎 ENRICHISSEMENT APPLE MUSIC URLs
Génère et met à jour les URLs Apple Music pour tous les albums via Euria API
"""

import sys
from pathlib import Path

# Ajouter le répertoire backend au sys.path
script_dir = Path(__file__).parent
root_dir = script_dir.parent.parent
backend_dir = root_dir / 'backend'
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(root_dir))

import json
import requests
import time
import os
from typing import Optional, Dict
from datetime import datetime
from urllib.parse import quote

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    env_path = root_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from app.database import SessionLocal
from app.models.album import Album

print("\n" + "=" * 90)
print("🍎 ENRICHISSEMENT APPLE MUSIC URLs - Génération via Euria API")
print("=" * 90)

# ============================================================================
# CONFIGURATION - Chargée depuis .env
# ============================================================================

EURIA_API_URL = os.getenv('URL', 'https://api.infomaniak.com/2/ai/106561/openai/v1/chat/completions')
EURIA_BEARER_TOKEN = os.getenv('bearer', '')

# ============================================================================
# PROVIDER: EURIA - GÉNÉRATION URLs APPLE MUSIC
# ============================================================================

class AppleMusicProvider:
    """Client pour générer des URLs Apple Music via Euria."""
    
    @classmethod
    def generate_apple_music_url(cls, album: Album) -> Optional[str]:
        """
        Génère une URL Apple Music pour l'album.
        Essaie d'abord de trouver l'ID via Euria, sinon génère une URL de recherche.
        """
        if not EURIA_BEARER_TOKEN:
            return cls._generate_search_url(album)
        
        try:
            artists = ", ".join([a.name for a in album.artists[:3]])
            year = f" ({album.year})" if album.year else ""
            
            # Première approche: demander à l'API Euria de trouver l'URL
            payload = {
                "model": "mistral3",
                "messages": [
                    {
                        "role": "user",
                        "content": f"""Find the Apple Music URL for this album:
Title: {album.title}
Artist: {artists}{year}

If you can find the exact Apple Music URL, return it in this format:
https://music.apple.com/fr/album/[album-slug]/[id]

If you cannot find it, return ONLY the word "SEARCH" and nothing else.
Respond with ONLY the URL or the word SEARCH, no other text."""
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.3
            }
            
            response = requests.post(
                EURIA_API_URL,
                json=payload,
                headers={"Authorization": f"Bearer {EURIA_BEARER_TOKEN}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0].get('message', {}).get('content', '').strip()
                    
                    # Si l'API a trouvé une URL
                    if content and 'music.apple.com' in content:
                        # Extraire l'URL de la réponse
                        if content.startswith('http'):
                            return content.split()[0]  # Prendre juste l'URL
                    
            # Fallback: générer une URL de recherche
            return cls._generate_search_url(album)
            
        except Exception as e:
            if "--verbose" in sys.argv:
                print(f"  ⚠️  Euria erreur pour {album.title}: {e}")
            return cls._generate_search_url(album)
    
    @classmethod
    def _generate_search_url(cls, album: Album) -> str:
        """Génère une URL de recherche Apple Music (fallback)."""
        artists = ", ".join([a.name for a in album.artists[:3]])
        search_query = f"{album.title} {artists}".strip()
        encoded_query = quote(search_query)
        return f"https://music.apple.com/search?term={encoded_query}"


# ============================================================================
# ORCHESTRATION - ENRICHISSEMENT COMPLET
# ============================================================================

def enrich_apple_music_urls(limit: int = None, force_update: bool = False) -> Dict:
    """
    Enrichit les albums avec des URLs Apple Music.
    
    Args:
        limit: Nombre max d'albums (pour tests)
        force_update: Si True, met à jour même les albums qui ont déjà une URL
    
    Returns:
        Dict avec statistiques
    """
    
    db = SessionLocal()
    
    stats = {
        "total": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "processing_time": 0,
        "start_time": datetime.now()
    }
    
    try:
        print(f"\n⚙️  Configuration:")
        print(f"   EURIA Bearer Token: {'✅ Configuré' if EURIA_BEARER_TOKEN else '❌ Manquant'}")
        print(f"   Force Update: {'✅ Oui' if force_update else '❌ Non (skip albums avec URL existante)'}")
        
        # Récupérer les albums
        query = db.query(Album)
        
        # Si force_update est False, on ne prend que les albums sans URL Apple Music
        if not force_update:
            query = query.filter(
                (Album.apple_music_url == None) | (Album.apple_music_url == '')
            )
        
        if limit:
            query = query.limit(limit)
        
        albums = query.all()
        stats["total"] = len(albums)
        
        print(f"\n📊 Albums à traiter: {len(albums)}")
        print("─" * 90)
        
        # ====================================================================
        # ENRICHISSEMENT URLs APPLE MUSIC
        # ====================================================================
        print("\n🍎 GÉNÉRATION URLs APPLE MUSIC:")
        
        for idx, album in enumerate(albums, 1):
            try:
                # Vérifier si on doit skip (déjà une URL et pas force_update)
                if album.apple_music_url and not force_update:
                    stats["skipped"] += 1
                    continue
                
                # Générer l'URL Apple Music
                apple_url = AppleMusicProvider.generate_apple_music_url(album)
                
                if apple_url:
                    album.apple_music_url = apple_url
                    db.add(album)
                    stats["updated"] += 1
                    
                    if idx % 10 == 0:
                        db.commit()  # Commit par batch de 10
                    
                    # Afficher le statut
                    if idx % 5 == 0 or idx == len(albums):
                        artists = ", ".join([a.name for a in album.artists[:2]])
                        print(f"  [{idx}/{len(albums)}] ✅ {album.title} - {artists}")
                else:
                    stats["errors"] += 1
                
                # Progression
                if idx % 20 == 0 or idx == len(albums):
                    pct = int((idx / len(albums)) * 100)
                    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                    print(f"\n  [{bar}] {idx}/{len(albums)} (+{stats['updated']} URLs, {stats['errors']} erreurs)")
                
                # Rate limiting Euria
                time.sleep(0.5)
            
            except Exception as e:
                print(f"  ❌ Erreur album {album.title}: {e}")
                stats["errors"] += 1
        
        db.commit()  # Final commit
        
        stats["processing_time"] = (datetime.now() - stats["start_time"]).total_seconds()
        
        print(f"\n✅ +{stats['updated']} URLs Apple Music appliquées")
        
        # ====================================================================
        # RÉSUMÉ FINAL
        # ====================================================================
        print("\n" + "=" * 90)
        print("📊 RÉSUMÉ D'ENRICHISSEMENT")
        print("=" * 90)
        print(f"Total albums traités: {stats['total']}")
        print(f"URLs ajoutées: {stats['updated']}")
        print(f"Albums skippés: {stats['skipped']}")
        print(f"Erreurs: {stats['errors']}")
        print(f"Temps de traitement: {stats['processing_time']:.1f}s")
        print(f"Moyenne par album: {stats['processing_time']/max(stats['total'], 1):.1f}s")
        print("=" * 90)
        
    finally:
        db.close()
    
    return stats


# ============================================================================
# EXÉCUTION
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrichir les URLs Apple Music')
    parser.add_argument('--limit', type=int, help='Nombre max d\'albums à traiter')
    parser.add_argument('--force', action='store_true', help='Forcer la mise à jour même pour les albums avec URL existante')
    parser.add_argument('--verbose', action='store_true', help='Afficher les erreurs détaillées')
    
    args = parser.parse_args()
    
    if not EURIA_BEARER_TOKEN:
        print("\n⚠️  ATTENTION: Bearer token Euria non configuré dans .env")
        print("   Le script va générer uniquement des URLs de recherche (fallback)")
        print("   Pour obtenir des URLs directes, configurez le bearer token dans .env\n")
    
    try:
        stats = enrich_apple_music_urls(limit=args.limit, force_update=args.force)
        
        if stats["updated"] > 0:
            print(f"\n✅ Succès! {stats['updated']} albums enrichis avec URLs Apple Music")
        else:
            print("\n⚠️  Aucun album enrichi. Utilisez --force pour mettre à jour les URLs existantes")
    
    except KeyboardInterrupt:
        print("\n\n⛔ Arrêt manuel détecté")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
