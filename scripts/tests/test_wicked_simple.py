#!/usr/bin/env python3
"""Test simple de recherche Wicked avec httpx direct"""

import httpx
import json

def get_spotify_token():
    """Obtenir le token Spotify"""
    with open('../config/secrets.json') as f:
        secrets = json.load(f)
    
    client_id = secrets['spotify']['client_id']
    client_secret = secrets['spotify']['client_secret']
    
    response = httpx.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        timeout=10
    )
    return response.json()["access_token"]

def search_album(artist, album):
    """Rechercher un album"""
    token = get_spotify_token()
    query = f"artist:{artist} album:{album}"
    
    print(f"\n🔍 Recherche: {query}")
    
    response = httpx.get(
        "https://api.spotify.com/v1/search",
        params={"q": query, "type": "album", "limit": 5},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    data = response.json()
    albums = data.get("albums", {}).get("items", [])
    
    print(f"\n📊 {len(albums)} résultat(s) trouvé(s)\n")
    
    for i, album in enumerate(albums, 1):
        print(f"{i}. {album['name']}")
        print(f"   Artistes: {', '.join([a['name'] for a in album['artists']])}")
        print(f"   URL: {album['external_urls']['spotify']}")
        print(f"   Année: {album['release_date'][:4]}")
        print()

def get_album_by_id(album_id):
    """Récupérer un album par son ID"""
    token = get_spotify_token()
    
    response = httpx.get(
        f"https://api.spotify.com/v1/albums/{album_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    data = response.json()
    print(f"\n📀 Album trouvé par ID:")
    print(f"   Nom: {data['name']}")
    print(f"   Artistes: {', '.join([a['name'] for a in data['artists']])}")
    print(f"   URL: {data['external_urls']['spotify']}")
    print(f"   Année: {data['release_date'][:4]}")

if __name__ == '__main__':
    print("="*80)
    print("TEST 1: Recherche avec titre complet")
    print("="*80)
    search_album("Various Artists", "Wicked: One Wonderful Night (Live) – The Soundtrack")
    
    print("="*80)
    print("TEST 2: Recherche avec tiret normal")
    print("="*80)
    search_album("Various Artists", "Wicked: One Wonderful Night (Live) - The Soundtrack")
    
    print("="*80)
    print("TEST 3: Recherche simplifiée")
    print("="*80)
    search_album("", "Wicked One Wonderful Night Live")
    
    print("="*80)
    print("TEST 4: Récupération par ID direct")
    print("="*80)
    get_album_by_id("39ixJY2rOByyed4OmCmAe2")
    print("\n" + "="*80)
