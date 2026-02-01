#!/usr/bin/env python3
"""Analyze and clean duplicate listening_history entries based on the 10-minute rule."""
import sqlite3
from pathlib import Path
from datetime import datetime

db_path = Path(__file__).parent / "data" / "musique.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("📊 Analyzing listening history for duplicates...")
print("=" * 70)

# Get all entries sorted by track_id and timestamp
cursor.execute("""
SELECT id, track_id, timestamp
FROM listening_history
ORDER BY track_id, timestamp ASC
""")

entries = cursor.fetchall()
print(f"Total entries: {len(entries)}\n")

# Find duplicates within 10 minutes
duplicates_to_delete = []
i = 0
while i < len(entries):
    id1, track_id1, ts1 = entries[i]
    j = i + 1
    
    # Find all consecutive entries with same track_id
    while j < len(entries):
        id2, track_id2, ts2 = entries[j]
        
        if track_id2 != track_id1:
            # Different track, stop looking
            break
        
        # Same track - check time difference
        time_diff = ts2 - ts1
        if time_diff <= 600:  # 600 seconds = 10 minutes
            # This is a duplicate
            duplicates_to_delete.append((id2, id1, track_id1, ts1, ts2, time_diff))
            # Move forward, keeping track of the last timestamp in sequence
            ts1 = ts2
            id1 = id2
        else:
            # More than 10 minutes - this is a legitimate new play
            i = j - 1
            break
        
        j += 1
    
    i += 1

print(f"🔍 Duplicates found (same track within 10 minutes): {len(duplicates_to_delete)}")

if duplicates_to_delete:
    print("\nFirst 30 duplicates to delete:")
    for dup_id, ref_id, track_id, ref_ts, dup_ts, diff_sec in duplicates_to_delete[:30]:
        ref_dt = datetime.fromtimestamp(ref_ts).strftime("%Y-%m-%d %H:%M:%S")
        dup_dt = datetime.fromtimestamp(dup_ts).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  Delete ID {dup_id} ({dup_dt}) | Keep ID {ref_id} ({ref_dt}) - {diff_sec}s apart (Track {track_id})")
    
    if len(duplicates_to_delete) > 30:
        print(f"  ... and {len(duplicates_to_delete) - 30} more\n")

    # Clean database
    print("\n🧹 Cleaning database...")
    ids_to_delete = [dup_id for dup_id, _, _, _, _, _ in duplicates_to_delete]
    
    placeholders = ','.join('?' * len(ids_to_delete))
    cursor.execute(f"DELETE FROM listening_history WHERE id IN ({placeholders})", ids_to_delete)
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM listening_history")
    final_count = cursor.fetchone()[0]
    print(f"✅ Deleted {len(duplicates_to_delete)} duplicates")
    print(f"✅ Final total entries: {final_count}")
else:
    print("✅ No duplicates found!")

conn.close()
