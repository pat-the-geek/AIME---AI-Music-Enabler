#!/usr/bin/env python3
"""
🤖 ENRICHISSEMENT EURIA + SPOTIFY
Descriptions via Euria AI + Images via Spotify
À intégrer au backend API
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au sys.path pour que les imports backend marchent
# Marche aussi bien quand lancé directement que quand chargé avec importlib
script_dir = Path(__file__).parent
root_dir = script_dir  # Le script est au root de AIME
sys.path.insert(0, str(root_dir))

import json
import requests
import time
import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv non disponible, continuer sans charger .env
    pass

from backend.app.database import SessionLocal
from backend.app.models import Album, Artist, Image

print("\n" + "=" * 90)
print("🤖 ENRICHISSEMENT EURIA + SPOTIFY - DESCRIPTIONS IA + IMAGES HD")
print("=" * 90)

# ============================================================================
# CONFIGURATION - Chargée depuis .env
# ============================================================================

# Euria via Infomaniak avec modèle Mistral (utilise bearer token du .env)
EURIA_API_URL = os.getenv('URL', 'https://api.infomaniak.com/2/ai/106561/openai/v1/chat/completions')
EURIA_BEARER_TOKEN = os.getenv('bearer', '')

# Spotify
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')

def load_config():
    """Vérifie que les credentials sont disponibles."""
    if not EURIA_BEARER_TOKEN:
        print("❌ ERREUR: Variable 'bearer' manquante dans .env")
        return False
    
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("❌ ERREUR: Variables Spotify manquantes dans .env")
        return False
    
    return True

# ============================================================================
# PROVIDER: EURIA + MISTRAL - DESCRIPTIONS IA
# ============================================================================

class EuriaProvider:
    """Client Euria (Infomaniak) avec modèle Mistral pour descriptions IA."""
    
    @classmethod
    def generate_description(cls, album: Album) -> Optional[str]:
        """Génère une description via Euria/Infomaniak avec modèle Mistral."""
        if not EURIA_BEARER_TOKEN:
            return None
        
        try:
            artists = ", ".join([a.name for a in album.artists[:3]])
            year = f" ({album.year})" if album.year else ""
            
            payload = {
                "model": "mistral3",  # Modèle Mistral disponible sur Euria
                "messages": [
                    {
                        "role": "user",
                        "content": f"""Generate a detailed 150-word music review for the album:
Title: {album.title}
Artists: {artists}{year}

Focus on:
- Musical style and genre
- Emotional impact and atmosphere
- Production quality and sound design
- Standout tracks and instrumentation

Write in an engaging, professional tone suitable for a music database.
Keep it informative and clear."""
                    }
                ],
                "max_tokens": 250,
                "temperature": 0.7
            }
            
            response = requests.post(
                EURIA_API_URL,
                json=payload,
                headers={"Authorization": f"Bearer {EURIA_BEARER_TOKEN}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extraction du texte depuis OpenAI format response
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0].get('message', {}).get('content', '').strip()
                    return content if content else None
        
        except Exception as e:
            if "--verbose" in sys.argv:
                print(f"  ⚠️  Euria erreur pour {album.title}: {e}")
            return None


# ============================================================================
# PROVIDER: SPOTIFY - IMAGES HAUTE RÉSOLUTION
# ============================================================================

class SpotifyProvider:
    """Client Spotify pour images artiste haute résolution."""
    
    _access_token = None
    _token_expires = None
    
    @classmethod
    def _get_token(cls) -> Optional[str]:
        """Obtient un token d'accès Spotify."""
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            return None
        
        # Vérifier si token valide
        if cls._access_token and cls._token_expires and time.time() < cls._token_expires:
            return cls._access_token
        
        try:
            import base64
            
            auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
            auth_bytes = auth_str.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
            
            response = requests.post(
                "https://accounts.spotify.com/api/token",
                headers={"Authorization": f"Basic {auth_b64}"},
                data={"grant_type": "client_credentials"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                cls._access_token = data.get('access_token')
                cls._token_expires = time.time() + (data.get('expires_in', 3600) - 60)
                return cls._access_token
        
        except Exception as e:
            print(f"  ⚠️  Erreur Spotify token: {e}")
            return None
    
    @classmethod
    def get_artist_image(cls, artist_name: str) -> Optional[str]:
        """Récupère l'image artiste de meilleure résolution."""
        token = cls._get_token()
        if not token:
            return None
        
        try:
            response = requests.get(
                "https://api.spotify.com/v1/search",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "q": f"artist:{artist_name}",
                    "type": "artist",
                    "limit": 1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                artists = data.get('artists', {}).get('items', [])
                
                if artists:
                    images = artists[0].get('images', [])
                    if images:
                        # Retourner la première image (meilleure résolution)
                        return images[0]['url']
        
        except Exception as e:
            if "--verbose" in sys.argv:
                print(f"  ⚠️  Spotify erreur pour {artist_name}: {e}")
            return None
    
    @classmethod
    def get_album_image(cls, album_name: str, artist_name: str) -> Optional[str]:
        """Récupère la cover d'album de meilleure résolution."""
        token = cls._get_token()
        if not token:
            return None
        
        try:
            query = f'album:"{album_name}" artist:"{artist_name}"'
            response = requests.get(
                "https://api.spotify.com/v1/search",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "q": query,
                    "type": "album",
                    "limit": 1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                albums = data.get('albums', {}).get('items', [])
                
                if albums:
                    images = albums[0].get('images', [])
                    if images:
                        return images[0]['url']
        
        except Exception as e:
            if "--verbose" in sys.argv:
                print(f"  ⚠️  Spotify erreur album {album_name}: {e}")
            return None


# ============================================================================
# ORCHESTRATION - ENRICHISSEMENT COMPLET
# ============================================================================

def enrich_albums_euria_spotify(limit: int = None, progress_callback=None) -> Dict:
    """
    Enrichit les albums avec:
    - Descriptions via Euria IA
    - Images artiste via Spotify
    
    Args:
        limit: Nombre max d'albums (pour tests)
        progress_callback: Fonction pour rapporter la progression
    
    Returns:
        Dict avec statistiques
    """
    
    db = SessionLocal()
    
    stats = {
        "total": 0,
        "descriptions_added": 0,
        "artist_images_added": 0,
        "errors": 0,
        "processing_time": 0,
        "start_time": datetime.now()
    }
    
    try:
        # Charger les fichiers JSON pour cache
        euria_path = Path('./data/euria_descriptions.json')
        artist_img_path = Path('./data/artist_images.json')
        
        euria_cache = {}
        if euria_path.exists():
            data = json.loads(euria_path.read_text())
            euria_cache = data.get('data', {})
        
        artist_cache = {}
        if artist_img_path.exists():
            data = json.loads(artist_img_path.read_text())
            artist_cache = data.get('data', {})
        
        # Récupérer les albums
        query = db.query(Album).filter_by(source='discogs')
        if limit:
            query = query.limit(limit)
        
        albums = query.all()
        stats["total"] = len(albums)
        
        print(f"\n📊 Enrichissement de {len(albums)} albums")
        print(f"   Sources: Euria/Mistral (descriptions) + Spotify (images)")
        print("─" * 90)
        
        # ====================================================================
        # ÉTAPE 1: ENRICHIR LES DESCRIPTIONS AVEC EURIA + MISTRAL
        # ====================================================================
        print("\n📝 PHASE 1 - ENRICHISSEMENT DESCRIPTIONS (Euria/Mistral IA):")
        
        for idx, album in enumerate(albums, 1):
            try:
                # Vérifier cache
                desc = None
                if album.title in euria_cache:
                    desc = euria_cache[album.title]
                    if desc and not desc.startswith('['):
                        continue  # Déjà remplie, skip
                
                # Générer via Euria + Mistral
                if not desc or desc.startswith('['):
                    new_desc = EuriaProvider.generate_description(album)
                    if new_desc:
                        desc = new_desc
                        euria_cache[album.title] = desc
                        stats["descriptions_added"] += 1
                
                # Appliquer à la BD
                if desc and not desc.startswith('['):
                    album.ai_description = desc[:2000]  # Limiter à 2000 chars
                    db.add(album)
                    
                    if idx % 10 == 0:
                        db.commit()  # Commit par batch
                
                # Progression
                if idx % 20 == 0 or idx == len(albums):
                    pct = int((idx / len(albums)) * 100)
                    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                    msg = f"  [{bar}] {idx}/{len(albums)} (+{stats['descriptions_added']} descriptions)"
                    print(msg)
                    
                    if progress_callback:
                        progress_callback({
                            "phase": "descriptions",
                            "current": idx,
                            "total": len(albums),
                            "added": stats["descriptions_added"]
                        })
                
                # Rate limiting Euria
                time.sleep(0.5)
            
            except Exception as e:
                print(f"  ❌ Erreur album {album.title}: {e}")
                stats["errors"] += 1
        
        db.commit()  # Final commit
        print(f"\n✅ +{stats['descriptions_added']} descriptions Euria/Mistral appliquées")
        
        # ====================================================================
        # ÉTAPE 2: ENRICHIR LES IMAGES ARTISTE AVEC SPOTIFY
        # ====================================================================
        print("\n🖼️  PHASE 2 - ENRICHISSEMENT IMAGES ARTISTE (Spotify):")
        
        artists = db.query(Artist).all()
        
        for idx, artist in enumerate(artists, 1):
            try:
                # Vérifier cache
                img_url = None
                if artist.name in artist_cache:
                    img_url = artist_cache[artist.name]
                    if img_url and not img_url.startswith('['):
                        continue  # Déjà remplie, skip
                
                # Récupérer via Spotify
                if not img_url or img_url.startswith('['):
                    new_url = SpotifyProvider.get_artist_image(artist.name)
                    if new_url:
                        img_url = new_url
                        artist_cache[artist.name] = img_url
                        
                        # Ajouter/mettre à jour image en BD
                        existing = db.query(Image).filter_by(
                            artist_id=artist.id,
                            image_type='artist',
                            source='spotify'
                        ).first()
                        
                        if existing:
                            existing.url = img_url
                        else:
                            db.add(Image(
                                artist_id=artist.id,
                                image_type='artist',
                                source='spotify',
                                url=img_url
                            ))
                        
                        stats["artist_images_added"] += 1
                
                if idx % 20 == 0:
                    db.commit()  # Commit par batch
                
                # Progression
                if idx % 50 == 0 or idx == len(artists):
                    pct = int((idx / len(artists)) * 100)
                    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                    msg = f"  [{bar}] {idx}/{len(artists)} (+{stats['artist_images_added']} images)"
                    print(msg)
                    
                    if progress_callback:
                        progress_callback({
                            "phase": "artist_images",
                            "current": idx,
                            "total": len(artists),
                            "added": stats["artist_images_added"]
                        })
                
                # Rate limiting Spotify
                time.sleep(0.2)
            
            except Exception as e:
                print(f"  ❌ Erreur artiste {artist.name}: {e}")
                stats["errors"] += 1
        
        db.commit()  # Final commit
        print(f"\n✅ +{stats['artist_images_added']} images artiste Spotify appliquées")
        
        # ====================================================================
        # ÉTAPE 3: SAUVEGARDER CACHES JSON
        # ====================================================================
        print("\n💾 SAUVEGARDE CACHES:")
        
        euria_path.parent.mkdir(parents=True, exist_ok=True)
        euria_path.write_text(json.dumps(
            {"data": euria_cache},
            ensure_ascii=False,
            indent=2
        ))
        print(f"✅ {euria_path.relative_to('.')} ({len(euria_cache)} entrées)")
        
        artist_img_path.parent.mkdir(parents=True, exist_ok=True)
        artist_img_path.write_text(json.dumps(
            {"data": artist_cache},
            ensure_ascii=False,
            indent=2
        ))
        print(f"✅ {artist_img_path.relative_to('.')} ({len(artist_cache)} entrées)")
        
        # Temps d'exécution
        stats["processing_time"] = (datetime.now() - stats["start_time"]).total_seconds()
        
    finally:
        db.close()
    
    return stats


# ============================================================================
# MAIN / CLI
# ============================================================================

if __name__ == "__main__":
    
    print("\n⚙️  VÉRIFICATION CONFIGURATION:")
    print("─" * 90)
    
    has_config = load_config()
    
    if EURIA_BEARER_TOKEN:
        print("✓ Euria API: Configurée (modèle Mistral)")
    else:
        print("✗ Euria API: À configurer")
        print("  → Obtenir les credentials: Infomaniak dashboard")
        print("  → Ajouter à: .env (bearer=... et URL=...)")
    
    if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
        print("✓ Spotify API: Configurée")
    else:
        print("✗ Spotify API: À configurer")
        print("  → Créer une app: https://developer.spotify.com/dashboard")
        print("  → Ajouter à: .env (SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET)")
    
    if not has_config:
        print("\n⚠️  Configuration incomplète!")
        print("   Veuillez configurer les API dans .env")
        print("   Ou utiliser: python3 setup_automation.py")
        sys.exit(1)
    
    print("\n" + "─" * 90)
    
    # Lancer l'enrichissement
    stats = enrich_albums_euria_spotify()
    
    print("\n" + "=" * 90)
    print("📊 RÉSUMÉ:")
    print("=" * 90)
    print(f"  ✅ Albums traités: {stats['total']}")
    print(f"  📝 Descriptions Euria: +{stats['descriptions_added']}")
    print(f"  🖼️  Images Spotify: +{stats['artist_images_added']}")
    print(f"  ❌ Erreurs: {stats['errors']}")
    print(f"  ⏱️  Temps: {stats['processing_time']:.1f}s")
    print("=" * 90 + "\n")
