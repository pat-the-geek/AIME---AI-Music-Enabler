#!/usr/bin/env python3
"""Script pour ajouter la colonne apple_music_url à la table albums."""
import sqlite3
import sys
import os
from pathlib import Path

# Chercher le chemin correct de la BD
project_root = Path(__file__).parent.parent
db_path = project_root / "data" / "db" / "musique.db"

# Essai du chemin alternatif
if not db_path.exists():
    db_path = Path(__file__).parent / "data" / "db" / "musique.db"

print(f"📍 Chemin de la BD: {db_path}")
print(f"✅ BD existe: {db_path.exists()}")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(albums)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "apple_music_url" in columns:
        print("✅ La colonne apple_music_url existe déjà!")
    else:
        print("📝 Ajout de la colonne apple_music_url...")
        cursor.execute("ALTER TABLE albums ADD COLUMN apple_music_url VARCHAR(500) NULL")
        print("✅ Colonne apple_music_url ajoutée avec succès!")
        
        # Créer l'index
        try:
            cursor.execute("CREATE INDEX idx_albums_apple_music_url ON albums(apple_music_url)")
            print("✅ Index créé avec succès!")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print("ℹ️  Index existe déjà")
            else:
                raise
    
    conn.commit()
    conn.close()
    print("\n✅ Migration appliquée avec succès!")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
