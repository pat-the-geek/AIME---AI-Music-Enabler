#!/usr/bin/env python3
"""Script de migration pour ajouter la colonne source à la table albums."""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path: str):
    """Appliquer les migrations à la base de données."""
    
    if not Path(db_path).exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"📝 Début de la migration sur {db_path}...")
        
        # Vérifier si la table albums existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='albums'")
        if not cursor.fetchone():
            print("⚠️ Table 'albums' n'existe pas. Initialisation requise.")
            conn.close()
            return False
        
        # 1. Ajouter la colonne source si elle n'existe pas
        cursor.execute("PRAGMA table_info(albums)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'source' not in columns:
            print("✅ Ajout de la colonne 'source'...")
            cursor.execute("ALTER TABLE albums ADD COLUMN source TEXT DEFAULT 'manual' NOT NULL")
        else:
            print("ℹ️ Colonne 'source' existe déjà.")
        
        # 2. Créer l'index sur la colonne source
        print("✅ Création de l'index sur 'source'...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_albums_source ON albums(source)")
        
        # 3. Mettre à jour les albums existants
        print("✅ Mise à jour des sources existantes...")
        
        # Albums avec discogs_id -> discogs
        cursor.execute("""
            UPDATE albums 
            SET source = 'discogs' 
            WHERE discogs_id IS NOT NULL AND source = 'manual'
        """)
        discogs_count = cursor.rowcount
        print(f"  - {discogs_count} albums Discogs marqués")
        
        # Albums avec support="Roon" -> roon
        cursor.execute("""
            UPDATE albums 
            SET source = 'roon' 
            WHERE support = 'Roon' AND source = 'manual'
        """)
        roon_count = cursor.rowcount
        print(f"  - {roon_count} albums Roon marqués")
        
        # 4. Corriger les supports invalides pour les albums Discogs
        print("✅ Correction des supports invalides...")
        cursor.execute("""
            UPDATE albums 
            SET support = NULL
            WHERE source = 'discogs'
            AND support IS NOT NULL
            AND support NOT IN ('Vinyle', 'Vinyl', 'CD', 'Digital', 'Cassette', 'Unknown')
        """)
        fixed_count = cursor.rowcount
        print(f"  - {fixed_count} supports invalides corrigés")
        
        # 5. Afficher les résumés
        print("\n📊 Résumé après migration:")
        
        cursor.execute("SELECT source, COUNT(*) as count FROM albums GROUP BY source ORDER BY count DESC")
        print("Albums par source:")
        for source, count in cursor.fetchall():
            print(f"  - {source}: {count}")
        
        cursor.execute("""
            SELECT support, COUNT(*) as count 
            FROM albums 
            WHERE source = 'discogs' 
            GROUP BY support 
            ORDER BY count DESC
        """)
        print("Albums Discogs par support:")
        for support, count in cursor.fetchall():
            support_name = support or "(NULL)"
            print(f"  - {support_name}: {count}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Migration complétée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/aime.db"
    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
