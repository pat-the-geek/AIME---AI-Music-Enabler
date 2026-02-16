#!/usr/bin/env python3
"""Script de nettoyage pour identifier et gérer les albums problématiques."""

import sqlite3
import sys
from pathlib import Path

def cleanup_check(db_path: str):
    """Vérifier et afficher les albums potentiellement problématiques."""
    
    if not Path(db_path).exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🧹 Vérification nettoyage de la collection...")
        print("=" * 60)
        
        # 1. Albums Discogs sans support valide
        print("\n🔍 Albums Discogs avec support potentiellement problématique...")
        cursor.execute("""
            SELECT id, title, support, discogs_id
            FROM albums 
            WHERE source = 'discogs' 
            AND support NOT IN ('Vinyle', 'Vinyl', 'CD', 'Digital', 'Cassette', 'Unknown')
            AND support IS NOT NULL
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"  Trouvé {len(results)} albums problématiques:")
            for album_id, title, support, discogs_id in results:
                print(f"    - ID {album_id}: '{title}' (support: '{support}')")
        else:
            print("  ✅ Aucun album problématique trouvé")
        
        # 2. Albums Discogs qui pourraient venir des écoutes
        print("\n🔍 Albums Discogs sans discogs_id (suspicious)...")
        cursor.execute("""
            SELECT id, title, support, created_at
            FROM albums 
            WHERE source = 'discogs' 
            AND discogs_id IS NULL
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"  ⚠️  Trouvé {len(results)} albums suspects:")
            for album_id, title, support, created_at in results:
                print(f"    - ID {album_id}: '{title}' (créé: {created_at})")
        else:
            print("  ✅ Tous les albums Discogs ont un discogs_id")
        
        # 3. Albums mélangés potentiels
        print("\n🔍 Albums qui pourraient être des doublons (même titre, sources différentes)...")
        cursor.execute("""
            SELECT title, COUNT(DISTINCT source) as source_count, 
                   GROUP_CONCAT(DISTINCT source) as sources,
                   GROUP_CONCAT(DISTINCT support) as supports
            FROM albums 
            GROUP BY title
            HAVING source_count > 1
            ORDER BY source_count DESC
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"  Trouvé {len(results)} albums en doublons (sources différentes):")
            for title, count, sources, supports in results:
                print(f"    - '{title}': sources={sources}, supports={supports}")
        else:
            print("  ✅ Pas de doublons détectés")
        
        # 4. Albums Last.fm très anciens (potentiellement erronés)
        print("\n🔍 Albums d'écoutes très anciens (> 1 an)...")
        cursor.execute("""
            SELECT id, title, support, source, created_at
            FROM albums 
            WHERE source = 'lastfm'
            AND datetime(created_at) < datetime('now', '-365 days')
            ORDER BY created_at ASC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"  Trouvé {len(results)} albums d'écoutes anciens:")
            for album_id, title, support, source, created_at in results:
                print(f"    - {source}: '{title}' (depuis {created_at})")
        else:
            print("  ℹ️  Aucun album d'écoute très ancien")
        
        # 5. Résumé général
        print("\n📊 Résumé général...")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN source = 'discogs' THEN 1 ELSE 0 END) as discogs,
                SUM(CASE WHEN source != 'discogs' THEN 1 ELSE 0 END) as listenings
            FROM albums
        """)
        
        total, discogs, listenings = cursor.fetchone()
        print(f"  - Total albums: {total}")
        print(f"  - Albums Discogs: {discogs}")
        print(f"  - Albums d'écoutes: {listenings}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Vérification complétée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def move_album_to_source(db_path: str, album_id: int, new_source: str, new_support: str = None):
    """Déplacer un album vers une autre source."""
    
    if new_source not in ['discogs', 'lastfm', 'spotify', 'manual']:
        print(f"❌ Source invalide: {new_source}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier que l'album existe
        cursor.execute("SELECT id, title, source FROM albums WHERE id = ?", (album_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ Album ID {album_id} non trouvé")
            return False
        
        current_source = result[2]
        print(f"📦 Déplacement album '{result[1]}':")
        print(f"  - De: {current_source} → À: {new_source}")
        
        # Mettre à jour
        if new_support:
            cursor.execute("""
                UPDATE albums 
                SET source = ?, support = ?
                WHERE id = ?
            """, (new_source, new_support, album_id))
            print(f"  - Support: {new_support}")
        else:
            cursor.execute("""
                UPDATE albums 
                SET source = ?
                WHERE id = ?
            """, (new_source, album_id))
        
        conn.commit()
        conn.close()
        
        print("✅ Album déplacé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python validate_correction.py <db_path> [check|move <album_id> <source> [support]]")
        print("\nExemples:")
        print("  python validate_correction.py ../data/db/musique.db check")
        print("  python validate_correction.py ../data/db/musique.db move 123 lastfm")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == "check":
        cleanup_check(db_path)
    elif len(sys.argv) > 2 and sys.argv[2] == "move":
        album_id = int(sys.argv[3])
        new_source = sys.argv[4]
        new_support = sys.argv[5] if len(sys.argv) > 5 else None
        move_album_to_source(db_path, album_id, new_source, new_support)
    else:
        cleanup_check(db_path)
