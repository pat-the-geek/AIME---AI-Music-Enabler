#!/usr/bin/env python3
"""Auto-enrichissement: Récupère descriptions + images depuis APIs."""
import sys
sys.path.insert(0, './backend')

import json
import requests
import time
from pathlib import Path
from typing import Optional, Dict
from backend.app.database import SessionLocal
from backend.app.models import Album, Artist

print("\n" + "=" * 90)
print("🤖 AUTO-ENRICHISSEMENT - DESCRIPTIONS + IMAGES ARTISTE")
print("=" * 90)

# ============================================================================
# CONFIGURATION - ADAPTER SELON VOS SOURCES
# ============================================================================

LASTFM_API_KEY = "YOUR_LASTFM_API_KEY"  # ← À remplir avec votre clé Last.fm
LASTFM_BASE_URL = "http://ws.audioscrobbler.com/2.0/"

# Template pour intégrer votre API de descriptions
# Options: OpenAI, Claude, Hugging Face, ou API Euria personnalisée
DESCRIPTION_SOURCE = "local_template"  # Options: "openai", "lastfm", "local_template"

# ============================================================================
# 1. RÉCUPÉRER IMAGES D'ARTISTE DEPUIS LASTFM
# ============================================================================

def get_lastfm_artist_image(artist_name: str) -> Optional[str]:
    """Récupère l'image d'artiste depuis Last.fm."""
    if not LASTFM_API_KEY or LASTFM_API_KEY == "YOUR_LASTFM_API_KEY":
        return None
    
    try:
        params = {
            'method': 'artist.getinfo',
            'artist': artist_name,
            'api_key': LASTFM_API_KEY,
            'format': 'json'
        }
        
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=5)
        data = response.json()
        
        if 'artist' in data and 'image' in data['artist']:
            images = data['artist']['image']
            # Chercher l'image la plus grande
            for img in reversed(images):
                if img.get('size') == 'extralarge' and img.get('#text'):
                    return img['#text']
        
        return None
        
    except Exception as e:
        if "--verbose" in sys.argv:
            print(f"  ⚠️  Erreur Last.fm pour {artist_name}: {e}")
        return None

# ============================================================================
# 2. GÉNÉRER DESCRIPTIONS (TEMPLATE LOCAL)
# ============================================================================

def generate_description_local(album: Album) -> Optional[str]:
    """Génère une description basée sur les infos locales (template)."""
    if not album or not album.title:
        return None
    
    # Template simple basé sur les données disponibles
    artists = ", ".join([a.name for a in album.artists[:3]])
    year = album.year if album.year else "Unknown"
    
    # Description template (à adapter selon vos besoins)
    description = f"{album.title} by {artists}" if artists else album.title
    if year and year != "Unknown":
        description += f" ({year})"
    
    return description

def generate_description_from_api(album: Album) -> Optional[str]:
    """
    Génère une description depuis une API externe.
    
    À implémenter avec votre source:
    - OpenAI API
    - Claude API
    - Hugging Face
    - API Euria personnalisée
    """
    # Exemple avec OpenAI (à adapter)
    # from openai import OpenAI
    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # 
    # prompt = f"Generate a 100-word description for album '{album.title}' by {', '.join([a.name for a in album.artists])}"
    # response = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # return response.choices[0].message.content
    
    return None

# ============================================================================
# 3. CHARGER/CRÉER LES FICHIERS JSON
# ============================================================================

def load_json_file(path: Path) -> Dict:
    """Charge ou crée un fichier JSON."""
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"description": "", "data": {}}

def save_json_file(path: Path, data: Dict):
    """Sauvegarde un fichier JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================================
# 4. ORCHESTRATION - AUTO-ENRICHISSEMENT
# ============================================================================

def auto_enrich():
    """Orchestration complète de l'enrichissement automatique."""
    
    db = SessionLocal()
    
    # Charger les fichiers JSON
    euria_path = Path('./data/euria_descriptions.json')
    artist_img_path = Path('./data/artist_images.json')
    
    euria_data = load_json_file(euria_path)
    artist_data = load_json_file(artist_img_path)
    
    # Récupérer tous les albums Discogs
    discogs_albums = db.query(Album).filter_by(source='discogs').all()
    
    print(f"\n📊 Albums à traiter: {len(discogs_albums)}")
    print(f"   Descriptions remplies: {len([v for v in euria_data['data'].values() if v and not v.startswith('[Remplir')])}")
    print(f"   Images artiste remplies: {len([v for v in artist_data['data'].values() if v and not v.startswith('[')])}")
    
    # ========================================================================
    # ÉTAPE 1: ENRICHIR LES DESCRIPTIONS
    # ========================================================================
    print("\n📝 ENRICHISSEMENT DESCRIPTIONS:")
    print("─" * 90)
    
    descriptions_added = 0
    for idx, album in enumerate(discogs_albums, 1):
        # Vérifier si la description existe déjà
        if album.title in euria_data['data']:
            existing = euria_data['data'][album.title]
            if existing and not existing.startswith('[Remplir'):
                continue  # Déjà remplie
        
        # Générer une nouvelle description
        if DESCRIPTION_SOURCE == "local_template":
            desc = generate_description_local(album)
        else:
            desc = generate_description_from_api(album)
        
        if desc:
            euria_data['data'][album.title] = desc
            descriptions_added += 1
        
        # Progress bar
        if idx % 50 == 0:
            bar_pct = int((idx / len(discogs_albums)) * 100)
            bar = "█" * int(bar_pct / 5) + "░" * (20 - int(bar_pct / 5))
            print(f"  [{bar}] {idx}/{len(discogs_albums)} (+{descriptions_added} descriptions)")
        
        # Rate limiting si API externe
        if DESCRIPTION_SOURCE != "local_template":
            time.sleep(0.1)
    
    print(f"\n✅ Descriptions ajoutées: {descriptions_added}")
    
    # ========================================================================
    # ÉTAPE 2: ENRICHIR LES IMAGES D'ARTISTE
    # ========================================================================
    print("\n🖼️  ENRICHISSEMENT IMAGES ARTISTE:")
    print("─" * 90)
    
    images_added = 0
    all_artists = db.query(Artist).all()
    
    for idx, artist in enumerate(all_artists, 1):
        # Vérifier si l'image existe déjà
        if artist.name in artist_data['data']:
            existing = artist_data['data'][artist.name]
            if existing and not existing.startswith('['):
                continue  # Déjà remplie
        
        # Récupérer l'image depuis Last.fm
        image_url = get_lastfm_artist_image(artist.name)
        
        if image_url:
            artist_data['data'][artist.name] = image_url
            images_added += 1
        
        # Progress bar
        if idx % 100 == 0:
            bar_pct = int((idx / len(all_artists)) * 100)
            bar = "█" * int(bar_pct / 5) + "░" * (20 - int(bar_pct / 5))
            print(f"  [{bar}] {idx}/{len(all_artists)} (+{images_added} images)")
        
        # Rate limiting Last.fm (5 requêtes/sec)
        time.sleep(0.2)
    
    print(f"\n✅ Images artiste ajoutées: {images_added}")
    
    # ========================================================================
    # ÉTAPE 3: SAUVEGARDER LES DONNÉES
    # ========================================================================
    print("\n💾 SAUVEGARDE:")
    print("─" * 90)
    
    save_json_file(euria_path, euria_data)
    print(f"✅ {euria_path} sauvegardé ({len(euria_data['data'])} entrées)")
    
    save_json_file(artist_img_path, artist_data)
    print(f"✅ {artist_img_path} sauvegardé ({len(artist_data['data'])} entrées)")
    
    # ========================================================================
    # ÉTAPE 4: LANCER LE REFRESH_COMPLETE (OPTIONNEL)
    # ========================================================================
    print("\n" + "=" * 90)
    
    if "--no-refresh" not in sys.argv:
        print("🔄 LANCEMENT DU REFRESH_COMPLETE...")
        print("─" * 90)
        
        import subprocess
        result = subprocess.run(['python3', 'refresh_complete.py'], cwd='.')
        
        if result.returncode == 0:
            print("\n✅ Refresh complété avec succès!")
        else:
            print(f"\n❌ Refresh échoué (code {result.returncode})")
    else:
        print("⏭️  Refresh skippé (--no-refresh)")
        print("   Lancez manuellement: python3 refresh_complete.py")
    
    print("\n" + "=" * 90)
    print("✨ AUTO-ENRICHISSEMENT COMPLÉTÉ")
    print("=" * 90 + "\n")
    
    db.close()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n💡 CONFIGURATION:")
    print(f"   Descriptions source: {DESCRIPTION_SOURCE}")
    print(f"   Last.fm API: {'✓ Configurée' if LASTFM_API_KEY != 'YOUR_LASTFM_API_KEY' else '✗ À configurer'}")
    
    if LASTFM_API_KEY == "YOUR_LASTFM_API_KEY":
        print("\n⚠️  IMPORTANT: Configurer la clé Last.fm API")
        print("   1. Créer un compte Last.fm: https://www.last.fm/join")
        print("   2. Obtenir une clé API: https://www.last.fm/api/account/create")
        print("   3. Remplacer 'YOUR_LASTFM_API_KEY' dans ce script")
        print("\n   Ou lancer sans: python3 auto_enrich_from_api.py --no-lastfm")
    
    auto_enrich()
