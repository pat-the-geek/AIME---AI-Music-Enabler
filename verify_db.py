#!/usr/bin/env python3
"""
Verify database integrity and check for any remaining duplicates or issues.
"""
import sqlite3

def main():
    db_path = "data/musique.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Database Integrity Verification\n")
    
    # 1. Count statistics
    cursor.execute("SELECT COUNT(*) FROM albums")
    album_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tracks")
    track_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM listening_history")
    history_count = cursor.fetchone()[0]
    
    print(f"📊 Counts:")
    print(f"   Albums: {album_count}")
    print(f"   Tracks: {track_count}")
    print(f"   History entries: {history_count}")
    
    # 2. Check for orphaned tracks (tracks not in any history)
    cursor.execute("""
        SELECT COUNT(*)
        FROM tracks t
        WHERE NOT EXISTS (
            SELECT 1 FROM listening_history lh WHERE lh.track_id = t.id
        )
    """)
    orphaned_tracks = cursor.fetchone()[0]
    print(f"\n⚠️  Orphaned tracks (not in history): {orphaned_tracks}")
    
    # 3. Check for orphaned albums (albums with no tracks)
    cursor.execute("""
        SELECT COUNT(*)
        FROM albums a
        WHERE NOT EXISTS (
            SELECT 1 FROM tracks t WHERE t.album_id = a.id
        )
    """)
    orphaned_albums = cursor.fetchone()[0]
    print(f"⚠️  Orphaned albums (no tracks): {orphaned_albums}")
    
    # 4. Check for duplicate (track_id, timestamp) in history
    cursor.execute("""
        SELECT track_id, timestamp, COUNT(*) as cnt
        FROM listening_history
        GROUP BY track_id, timestamp
        HAVING cnt > 1
    """)
    duplicates = cursor.fetchall()
    print(f"\n🔍 Duplicate (track_id, timestamp) pairs: {len(duplicates)}")
    if duplicates:
        for track_id, timestamp, cnt in duplicates[:5]:
            cursor.execute("SELECT title FROM tracks WHERE id = ?", (track_id,))
            title = cursor.fetchone()[0]
            print(f"   Track {track_id} ({title}) has {cnt} entries at timestamp {timestamp}")
    
    # 5. Check for 10-minute duplicates (consecutive same track within 600s)
    cursor.execute("""
        SELECT lh1.id, lh1.track_id, lh1.timestamp, lh2.timestamp,
               (lh2.timestamp - lh1.timestamp) as diff
        FROM listening_history lh1
        JOIN listening_history lh2 ON lh1.track_id = lh2.track_id
        WHERE lh2.timestamp > lh1.timestamp
          AND (lh2.timestamp - lh1.timestamp) <= 600
          AND NOT EXISTS (
              SELECT 1 FROM listening_history lh3
              WHERE lh3.track_id = lh1.track_id
              AND lh3.timestamp > lh1.timestamp
              AND lh3.timestamp < lh2.timestamp
          )
    """)
    
    time_dups = cursor.fetchall()
    print(f"🔍 Consecutive same-track within 10 min: {len(time_dups)}")
    if time_dups:
        for id1, track_id, ts1, ts2, diff in time_dups[:5]:
            cursor.execute("SELECT title FROM tracks WHERE id = ?", (track_id,))
            title = cursor.fetchone()[0]
            print(f"   Track {track_id} ({title}): {diff}s apart")
    
    # 6. Check tracks with duplicate titles in same album
    cursor.execute("""
        SELECT a.id, t.title, COUNT(*) as cnt
        FROM tracks t
        JOIN albums a ON t.album_id = a.id
        GROUP BY a.id, t.title
        HAVING cnt > 1
    """)
    
    dup_titles = cursor.fetchall()
    print(f"\n🔍 Duplicate track titles in same album: {len(dup_titles)}")
    if dup_titles:
        for album_id, title, cnt in dup_titles[:5]:
            print(f"   Album {album_id}: '{title}' appears {cnt} times")
    
    # 7. Check albums with duplicate names
    cursor.execute("""
        SELECT title, COUNT(*) as cnt
        FROM albums
        GROUP BY LOWER(title)
        HAVING cnt > 1
    """)
    
    dup_albums = cursor.fetchall()
    print(f"🔍 Albums with similar names (case-insensitive): {len(dup_albums)}")
    if dup_albums:
        for title, cnt in dup_albums[:5]:
            print(f"   '{title}' appears {cnt} times")
    
    # 8. Summary
    print(f"\n✅ Database Status:")
    issues = orphaned_tracks + orphaned_albums + len(duplicates) + len(time_dups) + len(dup_titles) + len(dup_albums)
    if issues == 0:
        print(f"   ✓ No integrity issues found!")
    else:
        print(f"   ⚠️  {issues} potential issues detected")
    
    conn.close()

if __name__ == "__main__":
    main()
