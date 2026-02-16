#!/usr/bin/env python3
"""Script de validation de la correction des sources d'albums."""

import sqlite3
from pathlib import Path
import sys

def validate_database(db_path: str):
    """Valider la correction effectuée."""
    
    if not Path(db_path).exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Validation de la correction Discogs...")
        print("=" * 60)
        
        # 1. Vérifier que la colonne source existe
        print("\n✅ Vérification structure...")
        cursor.execute("PRAGMA table_info(albums)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        if 'source' not in columns:
            print("❌ Colonne 'source' manquante!")
            return False
        else:
            print("✅ Colonne 'source' présente")
        
        # 2. Vérifier les albums Discogs
        print("\n📊 Albums Discogs...")
        cursor.execute("SELECT COUNT(*) FROM albums WHERE source = 'discogs'")
        discogs_count = cursor.fetchone()[0]
        print(f"  Total: {discogs_count}")
        
        cursor.execute("SELECT COUNT(*) FROM albums WHERE source = 'discogs' AND discogs_id IS NOT NULL")
        with_id = cursor.fetchone()[0]
        print(f"  Avec discogs_id: {with_id}")
        
        if with_id != discogs_count:
            print(f"  ⚠️ Attention: {discogs_count - with_id} albums Discogs sans ID")
        
        # 3. Vérifier les supports Discogs
        print("\n📀 Supports Discogs valides...")
        cursor.execute("""
            SELECT support, COUNT(*) as count
            FROM albums 
            WHERE source = 'discogs'
            GROUP BY support
            ORDER BY count DESC
        """)
        
        valid_supports = {'Vinyle', 'Vinyl', 'CD', 'Digital', 'Cassette', 'Unknown', None}
        all_valid = True
        
        for support, count in cursor.fetchall():
            status = "✅" if support in valid_supports else "❌"
            support_name = support or "(NULL)"
            print(f"  {status} {support_name}: {count}")
            if support not in valid_supports:
                all_valid = False
        
        if not all_valid:
            print("\n❌ Supports invalides trouvés pour les albums Discogs!")
            return False
        
        # 4. Vérifier les albums d'écoutes
        print("\n🎵 Albums d'écoutes...")
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM albums 
            WHERE source != 'discogs'
            GROUP BY source
            ORDER BY count DESC
        """)
        
        for source, count in cursor.fetchall():
            print(f"  - {source}: {count}")
        
        # 5. Vérifier la séparation
        print("\n🔀 Vérification de la séparation...")
        cursor.execute("SELECT COUNT(DISTINCT source) FROM albums")
        sources_count = cursor.fetchone()[0]
        print(f"  Nombre de sources différentes: {sources_count}")
        
        # 6. Albums sans source (contrôle)
        cursor.execute("SELECT COUNT(*) FROM albums WHERE source IS NULL")
        no_source = cursor.fetchone()[0]
        if no_source > 0:
            print(f"  ⚠️ {no_source} albums sans source!")
        else:
            print(f"  ✅ Tous les albums ont une source")
        
        # 7. Vérifier les relations
        print("\n🔗 Vérification des relations...")
        cursor.execute("""
            SELECT COUNT(DISTINCT a.id) 
            FROM albums a
            LEFT JOIN album_artist aa ON a.id = aa.album_id
            WHERE aa.album_id IS NULL
        """)
        orphans = cursor.fetchone()[0]
        if orphans > 0:
            print(f"  ⚠️ {orphans} albums sans artiste!")
        else:
            print(f"  ✅ Tous les albums ont au moins un artiste")
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM albums 
            WHERE source != 'discogs'
        """)
        listening_count = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Validation complétée avec succès!")
        print("\nRésumé:")
        print(f"  - Albums Discogs: {discogs_count} (séparés)")
        print(f"  - Albums d'écoutes: {listening_count} (séparés)")
        print(f"  - Supports Discogs: Tous valides")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la validation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "../data/db/musique.db"
    success = validate_database(db_path)
    sys.exit(0 if success else 1)
