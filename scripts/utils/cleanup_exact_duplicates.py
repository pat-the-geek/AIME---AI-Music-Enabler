#!/usr/bin/env python3
"""
Nettoyer les doublons avec timestamp identique (même track, même timestamp).
Garder le premier, supprimer les suivants.
"""
import sqlite3
from pathlib import Path

def cleanup_exact_duplicates():
    """Supprimer les entries avec (track_id, timestamp) exactement identiques."""
    db_path = Path(__file__).parent.parent / "data" / "musique.db"
    
    if not db_path.exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    print(f"🔍 Connexion à {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Vérifier l'état initial
    cursor.execute("SELECT COUNT(*) FROM listening_history")
    total_before = cursor.fetchone()[0]
    print(f"📊 Total entries avant nettoyage: {total_before}")
    
    # Trouver les doublons avec timestamp identique
    cursor.execute("""
        SELECT track_id, timestamp, COUNT(*) as cnt
        FROM listening_history
        GROUP BY track_id, timestamp
        HAVING cnt > 1
    """)
    
    exact_dups = cursor.fetchall()
    print(f"\n🔍 Groupes avec doublons timestamp identique: {len(exact_dups)}")
    
    if not exact_dups:
        print("✅ Aucun doublon à supprimer!")
        conn.close()
        return True
    
    # Pour chaque groupe, garder le premier et supprimer les autres
    ids_to_delete = []
    
    for track_id, timestamp, count in exact_dups:
        # Récupérer tous les IDs pour ce (track_id, timestamp)
        cursor.execute("""
            SELECT id FROM listening_history
            WHERE track_id = ? AND timestamp = ?
            ORDER BY id ASC
        """, (track_id, timestamp))
        
        ids = [row[0] for row in cursor.fetchall()]
        
        # Garder le premier, supprimer les autres
        for entry_id in ids[1:]:
            ids_to_delete.append(entry_id)
    
    print(f"📋 Entries à supprimer: {len(ids_to_delete)}")
    
    if len(ids_to_delete) > 20:
        print(f"   Premiers 20: {ids_to_delete[:20]}")
    else:
        print(f"   {ids_to_delete}")
    
    # Demander confirmation
    response = input(f"\n❓ Supprimer {len(ids_to_delete)} entries? (y/n): ").strip().lower()
    if response != 'y':
        print("❌ Suppression annulée")
        conn.close()
        return False
    
    # Supprimer les doublons
    print("\n🧹 Suppression en cours...")
    for entry_id in ids_to_delete:
        cursor.execute("DELETE FROM listening_history WHERE id = ?", (entry_id,))
    
    conn.commit()
    
    # Vérifier le résultat
    cursor.execute("SELECT COUNT(*) FROM listening_history")
    total_after = cursor.fetchone()[0]
    deleted_count = total_before - total_after
    
    print(f"\n✅ Nettoyage terminé!")
    print(f"📊 Avant: {total_before} entries")
    print(f"📊 Après: {total_after} entries")
    print(f"🗑️  Supprimé: {deleted_count} entries ({100*deleted_count/total_before:.1f}%)")
    
    conn.close()
    return True

if __name__ == "__main__":
    success = cleanup_exact_duplicates()
    exit(0 if success else 1)
