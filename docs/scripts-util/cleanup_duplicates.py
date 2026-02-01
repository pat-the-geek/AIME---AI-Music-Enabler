#!/usr/bin/env python3
"""Clean up duplicate listening_history entries."""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "musique.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("🧹 Cleaning duplicate listening_history entries...")

# Get duplicates
cursor.execute("""
SELECT track_id, timestamp, COUNT(*) as count
FROM listening_history
GROUP BY track_id, timestamp
HAVING count > 1
ORDER BY count DESC
""")
duplicates = cursor.fetchall()

print(f"Found {len(duplicates)} groups with duplicates")

# For each duplicate group, keep only the first one
total_deleted = 0
for track_id, timestamp, count in duplicates:
    # Get all IDs with this track_id and timestamp
    cursor.execute("""
    SELECT id FROM listening_history
    WHERE track_id = ? AND timestamp = ?
    ORDER BY id
    LIMIT -1 OFFSET 1
    """, (track_id, timestamp))
    
    ids_to_delete = [row[0] for row in cursor.fetchall()]
    
    if ids_to_delete:
        placeholders = ','.join('?' * len(ids_to_delete))
        cursor.execute(f"DELETE FROM listening_history WHERE id IN ({placeholders})", ids_to_delete)
        total_deleted += len(ids_to_delete)
        print(f"  - Deleted {len(ids_to_delete)} duplicates for track {track_id} at {timestamp}")

conn.commit()

# Verify
cursor.execute("""
SELECT COUNT(*)
FROM listening_history
GROUP BY track_id, timestamp
HAVING COUNT(*) > 1
""")
remaining_duplicates = len(cursor.fetchall())

cursor.execute("SELECT COUNT(*) FROM listening_history")
final_count = cursor.fetchone()[0]

print(f"\n✅ Cleaned {total_deleted} duplicate entries")
print(f"✅ Remaining duplicate groups: {remaining_duplicates}")
print(f"✅ Final total entries: {final_count}")

conn.close()
