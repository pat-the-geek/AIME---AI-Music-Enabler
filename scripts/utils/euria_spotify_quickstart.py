#!/usr/bin/env python3
"""
🚀 EURIA + SPOTIFY ENRICHMENT - CONFIGURATION CHECK
Vérifie que les clés .env sont présentes et prêtes
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Charger .env
load_dotenv()

print("""
╔════════════════════════════════════════════════════════════════╗
║  🤖 ENRICHISSEMENT EURIA + SPOTIFY - VÉRIFICATION CONFIG       ║
╚════════════════════════════════════════════════════════════════╝
""")

# Vérifier que .env existe
env_path = Path('.env')
if not env_path.exists():
    print("❌ ERREUR: Fichier .env non trouvé!")
    print("   Le fichier .env doit être à la racine du projet")
    sys.exit(1)

print("✅ Fichier .env trouvé\n")

# Vérifier les clés Euria
print("🔹 Configuration Euria:")
euria_url = os.getenv('URL')
euria_bearer = os.getenv('bearer')

if euria_url:
    print(f"   ✅ URL: {euria_url[:60]}...")
else:
    print(f"   ❌ URL manquante dans .env")

if euria_bearer:
    print(f"   ✅ Bearer Token: {euria_bearer[:20]}...")
else:
    print(f"   ❌ Bearer Token manquant dans .env")

# Vérifier les clés Spotify
print("\n🎵 Configuration Spotify:")
spotify_id = os.getenv('SPOTIFY_CLIENT_ID')
spotify_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

if spotify_id:
    print(f"   ✅ Client ID: {spotify_id[:20]}...")
else:
    print(f"   ❌ Client ID manquant dans .env")

if spotify_secret:
    print(f"   ✅ Client Secret: {spotify_secret[:20]}...")
else:
    print(f"   ❌ Client Secret manquant dans .env")

# Résumé
print("\n" + "=" * 60)
all_configured = all([euria_url, euria_bearer, spotify_id, spotify_secret])

if all_configured:
    print("✅ CONFIGURATION COMPLÈTE - Prêt à enrichir!\n")
    
    while True:
        print("\n📋 OPTIONS:")
        print("   1. Afficher l'URL de configuration")
        print("   2. Lancer l'enrichissement automatiquement")
        print("   3. Test: Enrichir 5 albums seulement")
        print("   4. Quitter")
        
        choice = input("\nChoisir (1-4): ").strip()
        
        if choice == "1":
            print(f"\n🔗 URLs de configuration:")
            print(f"   • Euria: https://euria.ai/dashboard")
            print(f"   • Spotify: https://developer.spotify.com/dashboard\n")
        
        elif choice == "2":
            print("\n🚀 Lancement enrichissement complet...")
            print("   (Cela peut prendre 3-4 minutes)")
            os.system("python3 enrich_euria_spotify.py")
            break
        
        elif choice == "3":
            print("\n🧪 Test: 5 albums seulement...")
            sys.path.insert(0, './backend')
            from enrich_euria_spotify import enrich_albums_euria_spotify
            
            def show_progress(data):
                print(f"  {data['phase']}: {data['current']}/{data['total']} "
                      f"(+{data['descriptions_added']}D, +{data.get('images_added', 0)}I)")
            
            try:
                stats = enrich_albums_euria_spotify(limit=5, progress_callback=show_progress)
                print(f"\n✅ Test complété!")
                print(f"   📝 Descriptions: +{stats['descriptions_added']}")
                print(f"   🖼️  Images: +{stats['artist_images_added']}")
                print(f"   ⏱️  Temps: {stats['processing_time']:.1f}s\n")
            except Exception as e:
                print(f"❌ Erreur: {e}\n")
        
        elif choice == "4":
            print("\n👋 Au revoir!")
            break
        
        else:
            print("❌ Option invalide!")

else:
    print("❌ CONFIGURATION INCOMPLÈTE\n")
    
    if not euria_url:
        print("   Manquant: URL= (clé Euria/Infomaniak)")
    if not euria_bearer:
        print("   Manquant: bearer= (token Euria/Infomaniak)")
    if not spotify_id:
        print("   Manquant: SPOTIFY_CLIENT_ID")
    if not spotify_secret:
        print("   Manquant: SPOTIFY_CLIENT_SECRET")
    
    print("\n📝 Mettez à jour .env avec les clés manquantes")
    print("   Créer app Spotify: https://developer.spotify.com/dashboard\n")
    
    sys.exit(1)
