#!/usr/bin/env python3
"""Check final database statistics after import."""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "musique.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print("📊 Database Statistics:")
print("=" * 50)
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"  {table[0]}: {count} rows")

# Check for duplicates
cursor.execute("""
SELECT track_id, timestamp, COUNT(*) as count
FROM listening_history
GROUP BY track_id, timestamp
HAVING count > 1
ORDER BY count DESC
LIMIT 5
""")
duplicates = cursor.fetchall()

print("\n🔍 Duplicate Check:")
print("=" * 50)
if duplicates:
    print(f"Found {len(duplicates)} entries with duplicates:")
    for track_id, timestamp, count in duplicates:
        print(f"  - Track ID {track_id} at {timestamp}: {count} occurrences")
else:
    print("✅ No duplicates found!")

# Summary
cursor.execute("SELECT COUNT(*) FROM listening_history")
total_entries = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(DISTINCT track_id) FROM listening_history")
unique_tracks = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(DISTINCT album_id) FROM track WHERE album_id IN (SELECT DISTINCT album_id FROM track JOIN listening_history ON track.id = listening_history.track_id)")
unique_albums = cursor.fetchone()[0]

print("\n📈 Summary:")
print("=" * 50)
print(f"  Total listening history entries: {total_entries}")
print(f"  Unique tracks in history: {unique_tracks}")
print(f"  Unique albums in history: {unique_albums}")

conn.close()
