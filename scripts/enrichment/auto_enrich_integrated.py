#!/usr/bin/env python3
"""
Auto-enrichment complet - Version intégrée avec configuration
Combine: Template généré + Last.fm (si configuré) + OpenAI (si configuré)
"""

import sys
sys.path.insert(0, './backend')

import json
import requests
import time
import os
from pathlib import Path
from typing import Optional, Dict
from backend.app.database import SessionLocal
from backend.app.models import Album, Artist

print("\n" + "=" * 90)
print("🤖 AUTO-ENRICHISSEMENT INTÉGRÉ - Multi-Source")
print("=" * 90)

# ============================================================================
# 1. CHARGER LA CONFIGURATION
# ============================================================================

config_file = Path('./config/enrichment_api_keys.json')

if config_file.exists():
    with open(config_file, 'r') as f:
        CONFIG = json.load(f)
    print("✓ Configuration API chargée")
else:
    CONFIG = {
        "lastfm": {"api_key": "", "enabled": False},
        "openai": {"api_key": "", "enabled": False},
        "huggingface": {"api_key": "", "enabled": False},
        "euria": {"api_url": "", "api_key": "", "enabled": False}
    }
    print("⚠️ Pas de configuration trouvée - Utilisant valeurs par défaut")

# ============================================================================
# 2. PROVIDERS - DESCRIPTIONS
# ============================================================================

class DescriptionProvider:
    """Client abstrait pour descriptions."""
    
    @staticmethod
    def get_description(album: Album) -> Optional[str]:
        """
        Essaie les providers dans cet ordre:
        1. OpenAI (si configuré)
        2. Last.fm enrichement
        3. Template local
        """
        
        # Essayer OpenAI
        if CONFIG.get("openai", {}).get("enabled"):
            desc = DescriptionProvider._openai(album)
            if desc:
                return desc
        
        # Essayer template enrichi
        return DescriptionProvider._template(album)
    
    @staticmethod
    def _openai(album: Album) -> Optional[str]:
        """Génère via OpenAI API."""
        try:
            import openai
            openai.api_key = CONFIG["openai"]["api_key"]
            
            artists = ", ".join([a.name for a in album.artists[:2]])
            year = f" ({album.year})" if album.year else ""
            
            response = openai.ChatCompletion.create(
                model=CONFIG["openai"].get("model", "gpt-3.5-turbo"),
                messages=[{
                    "role": "user",
                    "content": f"Write a 100-word music review for '{album.title}' by {artists}{year}. Focus on musical style and emotional impact.",
                }],
                max_tokens=120,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            if "--verbose" in sys.argv:
                print(f"  ⚠️  OpenAI erreur: {e}")
            return None
    
    @staticmethod
    def _template(album: Album) -> str:
        """Génère description template locale."""
        if not album.title:
            return "Unknown album"
        
        artists = ", ".join([a.name for a in album.artists[:3]])
        year = f" ({album.year})" if album.year else ""
        
        return f"{album.title}" + (f" by {artists}" if artists else "") + year


# ============================================================================
# 3. PROVIDERS - IMAGES ARTISTE
# ============================================================================

class ImageProvider:
    """Client abstrait pour images artiste."""
    
    @staticmethod
    def get_image(artist_name: str) -> Optional[str]:
        """
        Essaie les providers dans cet ordre:
        1. Spotify (si configuré)
        2. Last.fm
        """
        
        # Essayer Spotify
        if CONFIG.get("spotify", {}).get("enabled"):
            img = ImageProvider._spotify(artist_name)
            if img:
                return img
        
        # Essayer Last.fm
        if CONFIG.get("lastfm", {}).get("enabled"):
            img = ImageProvider._lastfm(artist_name)
            if img:
                return img
        
        return None
    
    @staticmethod
    def _spotify(artist_name: str) -> Optional[str]:
        """Récupère image via Spotify."""
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
            
            creds = SpotifyClientCredentials(
                client_id=CONFIG["spotify"].get("client_id", ""),
                client_secret=CONFIG["spotify"].get("client_secret", "")
            )
            
            sp = spotipy.Spotify(auth_manager=creds)
            results = sp.search(q=f"artist:{artist_name}", type="artist", limit=1)
            
            if results['artists']['items']:
                images = results['artists']['items'][0].get('images', [])
                if images:
                    return images[0]['url']
        
        except Exception as e:
            if "--verbose" in sys.argv:
                print(f"  ⚠️  Spotify erreur pour {artist_name}: {e}")
            return None
    
    @staticmethod
    def _lastfm(artist_name: str) -> Optional[str]:
        """Récupère image via Last.fm."""
        try:
            api_key = CONFIG.get("lastfm", {}).get("api_key", "")
            if not api_key:
                return None
            
            params = {
                'method': 'artist.getinfo',
                'artist': artist_name,
                'api_key': api_key,
                'format': 'json'
            }
            
            response = requests.get(
                'http://ws.audioscrobbler.com/2.0/',
                params=params,
                timeout=5
            )
            
            data = response.json()
            if 'artist' in data:
                images = data['artist'].get('image', [])
                for img in reversed(images):
                    if img.get('size') == 'extralarge' and img.get('#text'):
                        return img['#text']
        
        except Exception as e:
            if "--verbose" in sys.argv:
                print(f"  ⚠️  Last.fm erreur pour {artist_name}: {e}")
            return None


# ============================================================================
# 4. ORCHESTRATION
# ============================================================================

def auto_enrich_complete():
    """Orchestration complète multi-source."""
    
    db = SessionLocal()
    
    # Fichiers JSON
    euria_path = Path('./data/euria_descriptions.json')
    artist_img_path = Path('./data/artist_images.json')
    
    # Charger ou créer
    euria_data = json.loads(euria_path.read_text()) if euria_path.exists() else {"data": {}}
    artist_data = json.loads(artist_img_path.read_text()) if artist_img_path.exists() else {"data": {}}
    
    albums = db.query(Album).filter_by(source='discogs').all()
    artists = db.query(Artist).all()
    
    # Stats initiales
    existing_descs = len([v for v in euria_data.get('data', {}).values() if v and not v.startswith('[')])
    existing_imgs = len([v for v in artist_data.get('data', {}).values() if v and not v.startswith('[')])
    
    print(f"\n📊 État actuel:")
    print(f"   {len(albums)} albums | {len(artists)} artistes")
    print(f"   Descriptions: {existing_descs}/{len(albums)}")
    print(f"   Images artiste: {existing_imgs}/{len(artists)}")
    
    # ========================================================================
    # ENRICHIR DESCRIPTIONS
    # ========================================================================
    print("\n📝 ENRICHISSEMENT DESCRIPTIONS:")
    print("─" * 90)
    
    sources_used = []
    descriptions_added = 0
    
    for idx, album in enumerate(albums, 1):
        # Vérifier si existe déjà
        if album.title in euria_data.get('data', {}):
            existing = euria_data['data'][album.title]
            if existing and not existing.startswith('['):
                continue
        
        # Générer
        desc = DescriptionProvider.get_description(album)
        if desc:
            euria_data['data'][album.title] = desc
            descriptions_added += 1
        
        # Progress
        if idx % 50 == 0 or idx == len(albums):
            pct = int((idx / len(albums)) * 100)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            print(f"  [{bar}] {idx}/{len(albums)} (+{descriptions_added})")
        
        time.sleep(0.05)  # Rate limiting
    
    if CONFIG.get("openai", {}).get("enabled") and descriptions_added > 0:
        sources_used.append("OpenAI")
    if descriptions_added > 0:
        sources_used.append("Template")
    
    print(f"\n✅ +{descriptions_added} descriptions")
    if sources_used:
        print(f"   Sources: {', '.join(sources_used)}")
    
    # ========================================================================
    # ENRICHIR IMAGES ARTISTE
    # ========================================================================
    print("\n🖼️  ENRICHISSEMENT IMAGES ARTISTE:")
    print("─" * 90)
    
    img_sources = []
    images_added = 0
    
    for idx, artist in enumerate(artists, 1):
        if artist.name in artist_data.get('data', {}):
            existing = artist_data['data'][artist.name]
            if existing and not existing.startswith('['):
                continue
        
        img_url = ImageProvider.get_image(artist.name)
        if img_url:
            artist_data['data'][artist.name] = img_url
            images_added += 1
        
        if idx % 100 == 0 or idx == len(artists):
            pct = int((idx / len(artists)) * 100)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            print(f"  [{bar}] {idx}/{len(artists)} (+{images_added})")
        
        time.sleep(0.2)  # Rate limiting Last.fm
    
    if CONFIG.get("spotify", {}).get("enabled"):
        img_sources.append("Spotify")
    if CONFIG.get("lastfm", {}).get("enabled"):
        img_sources.append("Last.fm")
    
    print(f"\n✅ +{images_added} images artiste")
    if img_sources:
        print(f"   Sources: {', '.join(img_sources)}")
    
    # ========================================================================
    # SAUVEGARDER
    # ========================================================================
    print("\n💾 SAUVEGARDE:")
    print("─" * 90)
    
    euria_path.parent.mkdir(parents=True, exist_ok=True)
    euria_path.write_text(json.dumps(euria_data, ensure_ascii=False, indent=2))
    print(f"✅ {euria_path.relative_to('.')}")
    print(f"   {len(euria_data.get('data', {}))} entrées")
    
    artist_img_path.parent.mkdir(parents=True, exist_ok=True)
    artist_img_path.write_text(json.dumps(artist_data, ensure_ascii=False, indent=2))
    print(f"✅ {artist_img_path.relative_to('.')}")
    print(f"   {len(artist_data.get('data', {}))} entrées")
    
    # ========================================================================
    # REFRESH OPTIONNEL
    # ========================================================================
    print("\n" + "=" * 90)
    
    if "--no-refresh" not in sys.argv:
        print("🔄 LANCEMENT REFRESH_COMPLETE...")
        import subprocess
        result = subprocess.run(['python3', 'refresh_complete.py'], cwd='.')
        
        if result.returncode == 0:
            print("✅ Refresh complété!")
        else:
            print(f"❌ Refresh échoué (code {result.returncode})")
    else:
        print("⏭️  Refresh skippé (--no-refresh)")
        print("   Lancez: python3 refresh_complete.py")
    
    print("\n" + "=" * 90)
    print("✨ AUTO-ENRICHISSEMENT COMPLÉTÉ")
    print("=" * 90 + "\n")
    
    db.close()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    
    print("\n⚙️  CONFIGURATION DÉTECTÉE:")
    print("─" * 90)
    
    for source, config in CONFIG.items():
        enabled = config.get("enabled", False)
        status = "✓" if enabled else "✗"
        print(f"   {status} {source.upper():15} {'(configuré)' if enabled else '(non configuré)'}")
    
    print("\n" + "─" * 90)
    print("💡 Pour configurer les sources:")
    print("   python3 setup_automation.py")
    
    print("\n" + "─" * 90)
    
    auto_enrich_complete()
