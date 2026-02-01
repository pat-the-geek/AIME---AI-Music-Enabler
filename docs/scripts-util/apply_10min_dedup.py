#!/usr/bin/env python3
"""
Apply 10-minute deduplication rule: same track within 600 seconds = keep first, delete second.
"""
import sqlite3

def main():
    db_path = "data/musique.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Finding duplicates within 10-minute window...")
    
    # Get all listening_history grouped by track_id, ordered by timestamp
    cursor.execute("""
        SELECT 
            lh.id,
            lh.track_id,
            t.title,
            lh.timestamp,
            LAG(lh.timestamp) OVER (PARTITION BY lh.track_id ORDER BY lh.timestamp) as prev_timestamp
        FROM listening_history lh
        JOIN tracks t ON lh.track_id = t.id
        ORDER BY lh.track_id, lh.timestamp
    """)
    
    all_entries = cursor.fetchall()
    
    duplicates_to_delete = []
    
    for entry_id, track_id, title, timestamp, prev_timestamp in all_entries:
        if prev_timestamp is not None:
            time_diff = timestamp - prev_timestamp
            if 0 <= time_diff <= 600:  # Within 10 minutes
                duplicates_to_delete.append((entry_id, track_id, title, time_diff))
    
    if not duplicates_to_delete:
        print("✅ No 10-minute duplicates found!")
        conn.close()
        return
    
    print(f"🔍 Found {len(duplicates_to_delete)} entries within 10 minutes of same track\n")
    
    # Group by track for display
    by_track = {}
    for entry_id, track_id, title, time_diff in duplicates_to_delete:
        if title not in by_track:
            by_track[title] = []
        by_track[title].append((entry_id, time_diff))
    
    for title in sorted(by_track.keys()):
        print(f"📌 {title}")
        for entry_id, time_diff in by_track[title]:
            print(f"   Delete ID {entry_id} ({time_diff}s after previous)")
    
    # Delete duplicates
    print(f"\n🧹 Deleting {len(duplicates_to_delete)} duplicate entries...")
    for entry_id, _, _, _ in duplicates_to_delete:
        cursor.execute("DELETE FROM listening_history WHERE id = ?", (entry_id,))
    
    conn.commit()
    print(f"✅ Deleted {len(duplicates_to_delete)} entries")
    
    # Verify final state
    cursor.execute("SELECT COUNT(*) FROM listening_history")
    history_count = cursor.fetchone()[0]
    print(f"\n📊 Final listening_history entries: {history_count}")
    
    conn.close()

if __name__ == "__main__":
    main()
