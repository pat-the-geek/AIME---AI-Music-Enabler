#!/usr/bin/env python3
"""
Nettoyer les doublons de scrobbles dans listening_history.
Applique la règle des 10 minutes: même track à moins de 10 minutes d'écart = doublon.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

def cleanup_duplicates():
    """Supprimer les doublons selon la règle des 10 minutes."""
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
    
    # Trouver tous les doublons selon la règle des 10 minutes
    # Même track_id avec timestamp <= 600 secondes d'écart = doublon
    cursor.execute("""
        SELECT 
            lh1.id,
            lh1.track_id,
            t.title,
            lh1.timestamp,
            lh2.timestamp,
            (lh2.timestamp - lh1.timestamp) as diff
        FROM listening_history lh1
        JOIN listening_history lh2 ON lh1.track_id = lh2.track_id
        JOIN tracks t ON lh1.track_id = t.id
        WHERE lh2.timestamp > lh1.timestamp
          AND (lh2.timestamp - lh1.timestamp) <= 600
          AND NOT EXISTS (
              SELECT 1 FROM listening_history lh3
              WHERE lh3.track_id = lh1.track_id
              AND lh3.timestamp > lh1.timestamp
              AND lh3.timestamp < lh2.timestamp
          )
        ORDER BY lh1.track_id, lh1.timestamp
    """)
    
    duplicates = cursor.fetchall()
    print(f"\n🔍 Doublons trouvés (10 min rule): {len(duplicates)}")
    
    if not duplicates:
        print("✅ Aucun doublon détecté!")
        conn.close()
        return True
    
    # Afficher les premiers doublons
    print("\n📋 Premiers 20 doublons à supprimer:")
    print("-" * 80)
    
    ids_to_delete = []
    for entry_id, track_id, title, ts1, ts2, diff in duplicates[:20]:
        dt1 = datetime.fromtimestamp(ts1).strftime("%Y-%m-%d %H:%M:%S")
        dt2 = datetime.fromtimestamp(ts2).strftime("%Y-%m-%d %H:%M:%S")
        print(f"ID {entry_id}: {title}")
        print(f"  Entre {dt1} et {dt2} ({diff}s d'écart)")
        ids_to_delete.append(entry_id)
    
    # Grouper par track pour afficher un résumé
    print("\n" + "-" * 80)
    print(f"📊 Résumé par track:")
    print("-" * 80)
    
    by_track = {}
    for entry_id, track_id, title, _, _, diff in duplicates:
        if title not in by_track:
            by_track[title] = {"count": 0, "ids": []}
        by_track[title]["count"] += 1
        by_track[title]["ids"].append(entry_id)
    
    for title in sorted(by_track.keys())[:10]:
        count = by_track[title]["count"]
        print(f"  {title}: {count} doublons")
    
    if len(by_track) > 10:
        print(f"  ... et {len(by_track) - 10} autres tracks")
    
    print(f"\n🗑️  Total à supprimer: {len(duplicates)} entries")
    
    # Demander confirmation
    response = input("\n❓ Continuer avec la suppression? (y/n): ").strip().lower()
    if response != 'y':
        print("❌ Suppression annulée")
        conn.close()
        return False
    
    # Supprimer les doublons
    print("\n🧹 Suppression en cours...")
    for entry_id, _, _, _, _, _ in duplicates:
        cursor.execute("DELETE FROM listening_history WHERE id = ?", (entry_id,))
    
    conn.commit()
    
    # Vérifier le résultat
    cursor.execute("SELECT COUNT(*) FROM listening_history")
    total_after = cursor.fetchone()[0]
    deleted_count = total_before - total_after
    
    print(f"\n✅ Nettoyage terminé!")
    print(f"📊 Avant: {total_before} entries")
    print(f"📊 Après: {total_after} entries")
    print(f"🗑️  Supprimé: {deleted_count} doublons ({100*deleted_count/total_before:.1f}%)")
    
    conn.close()
    return True

if __name__ == "__main__":
    success = cleanup_duplicates()
    exit(0 if success else 1)
