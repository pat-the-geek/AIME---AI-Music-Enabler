#!/usr/bin/env python3
"""Script de test pour l'API Discogs."""
import sys
import json
import discogs_client

# Charger les secrets
with open('config/secrets.json', 'r') as f:
    secrets = json.load(f)

discogs_config = secrets['discogs']
api_key = discogs_config['api_key']
username = discogs_config['username']

print(f"🔍 Test connexion Discogs")
print(f"Username: {username}")
print(f"API Key: {api_key[:10]}...")
print()

try:
    # Créer le client
    client = discogs_client.Client('MusicTrackerApp/4.0', user_token=api_key)
    print("✅ Client créé")
    
    # Tester l'identité
    print("\n🔍 Test identité utilisateur...")
    user = client.identity()
    print(f"✅ Utilisateur: {user.username}")
    print(f"   Nombre de releases: {user.num_collection}")
    
    # Tester les folders
    print("\n🔍 Test collection folders...")
    folders = user.collection_folders
    print(f"✅ Nombre de folders: {len(folders)}")
    
    for i, folder in enumerate(folders):
        print(f"   Folder {i}: {folder.name} - {folder.count} items")
    
    # Tester le premier folder (collection principale)
    if len(folders) > 0:
        print("\n🔍 Test récupération releases du folder principal...")
        main_folder = folders[0]
        print(f"   Folder: {main_folder.name}")
        print(f"   Count: {main_folder.count}")
        
        # Récupérer les releases
        releases = main_folder.releases
        print(f"✅ Releases object: {type(releases)}")
        
        # Essayer de parcourir les releases
        print("\n🔍 Premiers albums de la collection:")
        count = 0
        for release in releases:
            if count >= 5:  # Limiter à 5 pour le test
                break
            
            release_data = release.release
            print(f"\n   Album {count + 1}:")
            print(f"   - ID: {release_data.id}")
            print(f"   - Titre: {release_data.title}")
            print(f"   - Année: {release_data.year}")
            print(f"   - Artistes: {[a.name for a in release_data.artists]}")
            
            count += 1
        
        print(f"\n✅ {count} albums récupérés dans le test")
    
    print("\n✅ ✅ ✅ Test Discogs réussi!")
    
except Exception as e:
    print(f"\n❌ ERREUR: {type(e).__name__}")
    print(f"   Message: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
