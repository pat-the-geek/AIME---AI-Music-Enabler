#!/usr/bin/env python3
"""
Guide et exemples : Enrichissement automatique pour différentes sources

Cet exemple montre comment adapter auto_enrich_from_api.py pour:
1. OpenAI / Claude - Génération de descriptions par IA
2. Last.fm - Images et métadonnées d'artiste
3. Spotify - Images et métadonnées d'artiste
4. Hugging Face - Génération local ou API
"""

# ============================================================================
# EXEMPLE 1: OPENAI (GPT-3.5 / GPT-4)
# ============================================================================

def enrich_with_openai():
    """
    Génère des descriptions via OpenAI.
    
    Installation:
    pip install openai
    
    Configuration:
    1. Créer compte: https://platform.openai.com
    2. Obtenir clé API: https://platform.openai.com/account/api-keys
    3. Mettre clé dans variable env: export OPENAI_API_KEY="sk-..."
    """
    
    import os
    from openai import OpenAI
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate_album_description(title: str, artists: list, year: int = None) -> str:
        """Génère une description d'album via GPT."""
        
        artists_str = ", ".join(artists[:3])
        year_str = f" from {year}" if year else ""
        
        prompt = f"""
        Write a 100-word music review for the album:
        Title: {title}
        Artists: {artists_str}{year_str}
        
        Focus on: musical style, innovation, emotional impact
        Keep it concise and engaging.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    # Exemple d'usage
    desc = generate_album_description("Innerspeaker", ["Tame Impala"], 2010)
    print(f"Description générée:\n{desc}\n")
    
    return generate_album_description


# ============================================================================
# EXEMPLE 2: LASTFM
# ============================================================================

def enrich_with_lastfm():
    """
    Récupère images et infos d'artiste via Last.fm.
    
    Installation:
    pip install requests
    
    Configuration:
    1. S'inscrire: https://www.last.fm/join
    2. Créer app: https://www.last.fm/api/account/create
    3. Obtenir clé API
    """
    
    import requests
    from typing import Optional, Dict
    
    LASTFM_API_KEY = "YOUR_API_KEY"
    LASTFM_URL = "http://ws.audioscrobbler.com/2.0/"
    
    def get_artist_info(artist_name: str) -> Optional[Dict]:
        """Récupère infos complètes d'un artiste."""
        
        params = {
            'method': 'artist.getinfo',
            'artist': artist_name,
            'autocorrect': 1,
            'api_key': LASTFM_API_KEY,
            'format': 'json'
        }
        
        try:
            response = requests.get(LASTFM_URL, params=params, timeout=5)
            data = response.json()
            
            if 'artist' in data:
                artist = data['artist']
                return {
                    'name': artist.get('name'),
                    'url': artist.get('url'),
                    'image': artist.get('image', [])[-1].get('#text', None),  # La plus grande
                    'listeners': artist.get('stats', {}).get('listeners'),
                    'bio': artist.get('bio', {}).get('summary', '').strip(),
                }
        except Exception as e:
            print(f"Error fetching {artist_name}: {e}")
        
        return None
    
    # Exemple d'usage
    info = get_artist_info("Tame Impala")
    if info:
        print(f"Artiste: {info['name']}")
        print(f"Image: {info['image']}")
        print(f"Bio: {info['bio'][:200]}...\n")
    
    return get_artist_info


# ============================================================================
# EXEMPLE 3: SPOTIFY
# ============================================================================

def enrich_with_spotify():
    """
    Récupère images et métadonnées via Spotify.
    
    Installation:
    pip install spotipy
    
    Configuration:
    1. Créer app: https://developer.spotify.com/dashboard
    2. Obtenir Client ID et Secret
    3. Les mettre en variables env:
       export SPOTIFY_CLIENT_ID="..."
       export SPOTIFY_CLIENT_SECRET="..."
    """
    
    import os
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    client = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
    )
    
    def get_artist_image(artist_name: str) -> str:
        """Récupère l'image principale d'un artiste."""
        
        try:
            results = client.search(q=f"artist:{artist_name}", type="artist", limit=1)
            
            if results['artists']['items']:
                artist = results['artists']['items'][0]
                images = artist.get('images', [])
                
                if images:
                    # Récupérer l'image la plus grande (généralement la première)
                    return images[0]['url']
        except Exception as e:
            print(f"Error fetching Spotify image for {artist_name}: {e}")
        
        return None
    
    def get_album_info(album_name: str, artist_name: str) -> dict:
        """Récupère les infos complètes d'un album."""
        
        try:
            query = f"album:{album_name} artist:{artist_name}"
            results = client.search(q=query, type="album", limit=1)
            
            if results['albums']['items']:
                album = results['albums']['items'][0]
                return {
                    'name': album['name'],
                    'cover_url': album['images'][0]['url'] if album['images'] else None,
                    'release_date': album['release_date'],
                    'total_tracks': album['total_tracks'],
                    'artists': [a['name'] for a in album['artists']]
                }
        except Exception as e:
            print(f"Error fetching Spotify album: {e}")
        
        return None
    
    # Exemple d'usage (à décommenter)
    # image = get_artist_image("Tame Impala")
    # print(f"Image Spotify: {image}\n")
    
    return get_artist_image, get_album_info


# ============================================================================
# EXEMPLE 4: HUGGING FACE (LOCAL NLP)
# ============================================================================

def enrich_with_huggingface():
    """
    Génère des descriptions avec des modèles Hugging Face.
    Peut fonctionner localement ou via API.
    
    Installation:
    pip install transformers torch
    
    Ou via API:
    pip install requests
    """
    
    # Option 1: LOCAL (télécharge le modèle)
    def local_generation():
        from transformers import pipeline
        
        # Charger le modèle (première fois: ~500MB)
        generator = pipeline("text-generation", model="EleutherAI/gpt-neo-125m")
        
        def generate_description(album_title: str, artist_name: str) -> str:
            prompt = f"Album: {album_title} by {artist_name}\nDescription: This album"
            
            result = generator(
                prompt,
                max_length=100,
                num_return_sequences=1,
                temperature=0.8
            )
            
            return result[0]['generated_text'].replace(prompt, "").strip()
        
        return generate_description
    
    # Option 2: API (nécessite clé API)
    def api_generation():
        import requests
        import os
        
        HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
        API_URL = "https://api-inference.huggingface.co/models/gpt2"
        
        def generate_description(album_title: str, artist_name: str) -> str:
            prompt = f"Album: {album_title} by {artist_name}\n"
            
            headers = {"Authorization": f"Bearer {HF_API_KEY}"}
            response = requests.post(
                API_URL,
                headers=headers,
                json={"inputs": prompt}
            )
            
            if response.status_code == 200:
                return response.json()[0]['generated_text']
            
            return None
        
        return generate_description
    
    return local_generation, api_generation


# ============================================================================
# EXEMPLE 5: DISCOGS (MÉTADONNÉES ENRICHIES)
# ============================================================================

def enrich_with_discogs():
    """
    Récupère des métadonnées enrichies depuis Discogs API.
    (Déjà partiellement utilisé)
    
    Installation:
    pip install discogs-client
    """
    
    import discogs_client
    
    d = discogs_client.Client('MyApp/0.1', user_token='YOUR_TOKEN')
    
    def get_album_details(discogs_id: int) -> dict:
        """Récupère les détails complets d'un album Discogs."""
        
        try:
            release = d.release(discogs_id)
            
            return {
                'title': release.title,
                'year': release.year,
                'artists': [a.name for a in release.artists],
                'genres': release.genres,
                'styles': release.styles,
                'description': release.notes,
                'images': [img.uri for img in release.images],
            }
        except Exception as e:
            print(f"Error fetching Discogs release {discogs_id}: {e}")
        
        return None
    
    return get_album_details


# ============================================================================
# EXEMPLE 6: STRATÉGIE HYBRIDE (Recommandée)
# ============================================================================

def hybrid_enrichment_strategy():
    """
    Combine différentes sources pour un résultat optimal.
    
    Stratégie:
    1. Images: Spotify (meilleure qualité) → Fallback Last.fm
    2. Descriptions: OpenAI (si activé) → Fallback template local
    3. Métadonnées: Discogs (déjà imported) → Enrichir avec Last.fm
    """
    
    strategy = {
        'artist_images': {
            'primary': 'spotify',    # Spotify a les meilleures images
            'fallback': 'lastfm',
        },
        'descriptions': {
            'primary': 'openai',     # GPT génère les meilleures descriptions
            'fallback': 'template',  # Backend local si pas d'API
        },
        'album_metadata': {
            'primary': 'discogs',    # Déjà importé
            'enrichment': 'spotify', # Ajouter cover + release date
        },
        'rate_limits': {
            'openai': 3,         # 3 req/sec
            'spotify': 1,        # 1 req/sec
            'lastfm': 5,         # 5 req/sec
            'discogs': 1,        # 1 req/sec
        }
    }
    
    print("Stratégie hybride:")
    print(f"  Images artiste: {strategy['artist_images']}")
    print(f"  Descriptions: {strategy['descriptions']}")
    print(f"  Métadonnées: {strategy['album_metadata']}")
    
    return strategy


# ============================================================================
# MAIN - AFFICHER LES OPTIONS
# ============================================================================

if __name__ == "__main__":
    
    print("\n" + "=" * 90)
    print("📚 GUIDE ENRICHISSEMENT AUTOMATIQUE - OPTIONS ET EXEMPLES")
    print("=" * 90)
    
    print("\n1️⃣  OPENAI (GPT-3.5 / GPT-4)")
    print("─" * 90)
    print("   ✅ Génère les descriptions les plus naturelles")
    print("   ✅ Supporte personnalisation fine (tone, style, length)")
    print("   ❌ Coûte de l'argent (~ $0.001/description)")
    print("   ⏱️  ~1-2 sec par description")
    print("   👉 https://platform.openai.com/api/")
    
    print("\n2️⃣  LASTFM")
    print("─" * 90)
    print("   ✅ Images artiste de bonne qualité")
    print("   ✅ Gratuit et rapide")
    print("   ✅ Récupère aussi bio/listeners/tags")
    print("   ❌ Pas de génération de descriptions")
    print("   ⏱️  ~100ms par artiste")
    print("   👉 https://www.last.fm/api/")
    
    print("\n3️⃣  SPOTIFY")
    print("─" * 90)
    print("   ✅ Images de très haute qualité")
    print("   ✅ Récupère cover d'album de haute résolution")
    print("   ✅ Données de qualité professionnelle")
    print("   ❌ Nécessite couple Client ID/Secret")
    print("   ⏱️  ~200ms par requête")
    print("   👉 https://developer.spotify.com/")
    
    print("\n4️⃣  HUGGING FACE")
    print("─" * 90)
    print("   ✅ Peut fonctionner localement (offline)")
    print("   ✅ Gratuit si local, API gratuite si limité")
    print("   ❌ Qualité inférieure à OpenAI")
    print("   ⏱️  ~1-2 sec par description (selon modèle)")
    print("   👉 https://huggingface.co/")
    
    print("\n5️⃣  DISCOGS")
    print("─" * 90)
    print("   ✅ Déjà l'API source (complètement enrichie)")
    print("   ✅ Notes/descriptions existantes")
    print("   ✅ Gratuit et stable")
    print("   ❌ Descriptions pas toujours présentes")
    print("   👉 Déjà imlémenté !")
    
    print("\n" + "=" * 90)
    print("🎯 RECOMMANDATION")
    print("=" * 90)
    print("""
    Approche hybride (meilleur équilibre):
    
    1. Images artiste:
       └─ Spotify API (meilleure qualité)
          └─ Fallback: Last.fm
    
    2. Descriptions:
       └─ OpenAI (si budget)
          └─ Fallback: Template local
    
    3. Métadonnées:
       └─ Discogs (déjà importé)
          └─ Enrichir avec: Spotify release_date, cover
    
    Pour DÉMARRER rapidement sans API:
    └─ python3 auto_enrich_from_api.py (template local)
    
    Pour MEILLEUR résultat avec budget:
    └─ Configuration Last.fm (gratuit)
    └─ Configuration OpenAI ($)
    """)
    
    print("=" * 90)
    print("📖 PROCHAINES ÉTAPES")
    print("=" * 90)
    print("""
    1. python3 setup_automation.py
       → Configurer les clés API
    
    2. Personnaliser auto_enrich_from_api.py
       → Adapter avec votre source préférée
    
    3. python3 auto_enrich_from_api.py
       → Lancer l'enrichissement
    
    4. python3 refresh_complete.py
       → Appliquer au système
    
    5. python3 verify_enrichment.py
       → Valider le résultat
    """)
    print("=" * 90 + "\n")
