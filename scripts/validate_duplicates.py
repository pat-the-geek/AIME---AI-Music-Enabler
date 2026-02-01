#!/usr/bin/env python3
"""
Script de validation après nettoyage des doublons.
Vérifie que la règle des 10 minutes est respectée.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def validate_database():
    """Valider que la base de données n'a plus de doublons."""
    db_path = Path(__file__).parent.parent / "data" / "musique.db"
    
    if not db_path.exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    print(f"🔍 Validation de {db_path}")
    print("=" * 80)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 1. Nombre total d'entries
    cursor.execute("SELECT COUNT(*) FROM listening_history")
    total_entries = cursor.fetchone()[0]
    print(f"\n📊 Statistiques:")
    print(f"   Total entries: {total_entries}")
    
    # 2. Chercher les 10-minute duplicates
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
    print(f"   Doublons 10min: {len(duplicates)}")
    
    if duplicates:
        print(f"\n❌ PROBLÈME: Encore {len(duplicates)} doublons détectés!")
        print("\nExemples:")
        for entry_id, track_id, title, ts1, ts2, diff in duplicates[:5]:
            dt1 = datetime.fromtimestamp(ts1).strftime("%Y-%m-%d %H:%M:%S")
            dt2 = datetime.fromtimestamp(ts2).strftime("%Y-%m-%d %H:%M:%S")
            print(f"   ID {entry_id}: {title} ({diff}s apart)")
            print(f"     {dt1} → {dt2}")
        return False
    
    # 3. Chercher des entries avec timestamp exactement identique (même track, même timestamp)
    cursor.execute("""
        SELECT track_id, timestamp, COUNT(*) as cnt
        FROM listening_history
        GROUP BY track_id, timestamp
        HAVING cnt > 1
        ORDER BY cnt DESC
    """)
    
    exact_dups = cursor.fetchall()
    print(f"   Timestamp identiques: {len(exact_dups)}")
    
    if exact_dups:
        print(f"\n⚠️  ATTENTION: {len(exact_dups)} entries avec timestamp identiques")
        for track_id, timestamp, cnt in exact_dups[:5]:
            cursor.execute("SELECT title FROM tracks WHERE id = ?", (track_id,))
            track = cursor.fetchone()
            title = track[0] if track else "Unknown"
            dt = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            print(f"   Track {track_id} ({title}): {cnt} fois à {dt}")
    
    # 4. Distribution par source
    cursor.execute("""
        SELECT source, COUNT(*) as cnt
        FROM listening_history
        GROUP BY source
        ORDER BY cnt DESC
    """)
    
    sources = cursor.fetchall()
    print(f"\n📈 Distribution par source:")
    for source, count in sources:
        pct = 100 * count / total_entries
        print(f"   {source}: {count} ({pct:.1f}%)")
    
    # 5. Top tracks with most entries
    cursor.execute("""
        SELECT t.title, COUNT(*) as cnt
        FROM listening_history lh
        JOIN tracks t ON lh.track_id = t.id
        GROUP BY t.title
        ORDER BY cnt DESC
        LIMIT 5
    """)
    
    top_tracks = cursor.fetchall()
    print(f"\n🎵 Top 5 tracks les plus écoutés:")
    for title, count in top_tracks:
        print(f"   {title}: {count} fois")
    
    # 6. Vérifier la cohérence temporelle
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest
        FROM listening_history
    """)
    
    stats = cursor.fetchone()
    total, earliest, latest = stats
    if earliest:
        start_dt = datetime.fromtimestamp(earliest).strftime("%Y-%m-%d %H:%M:%S")
        end_dt = datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M:%S")
        days = (latest - earliest) / (24 * 3600)
        print(f"\n📅 Plage temporelle:")
        print(f"   Du: {start_dt}")
        print(f"   Au: {end_dt}")
        print(f"   Durée: {days:.1f} jours")
    
    print("\n" + "=" * 80)
    print("✅ VALIDATION RÉUSSIE!")
    print("   • Aucun doublon 10 minutes")
    print("   • Base de données valide")
    
    conn.close()
    return True

if __name__ == "__main__":
    success = validate_database()
    exit(0 if success else 1)
