#!/usr/bin/env python3
"""Script d'initialisation de la base de données avec les modèles."""

import sys
import os

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, Base, engine
from app.models import Album, Artist, Track, ListeningHistory, Image, Metadata, Playlist, PlaylistTrack, album_artist

print("📝 Initialisation de la base de données...")
print(f"URL: {os.environ.get('DATABASE_URL', 'sqlite:///./backend/data/aime.db')}")

# Créer toutes les tables
init_db()

print("✅ Tables créées/vérifiées:")
print("  - albums")
print("  - artists")
print("  - album_artist")
print("  - tracks")
print("  - listening_history")
print("  - images")
print("  - metadata")
print("  - playlists")
print("  - playlist_tracks")

print("\n✅ Base de données initialisée avec succès!")
