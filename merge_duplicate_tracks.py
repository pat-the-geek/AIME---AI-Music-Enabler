#!/usr/bin/env python3
"""
Merge duplicate tracks based on normalized title matching.
Handles: case differences, parentheses variations, extra spaces.
"""
import sqlite3
import re
from collections import defaultdict

def normalize_title(title: str) -> str:
    """Normalize track title for duplicate detection."""
    if not title:
        return ""
    # Convert to lowercase
    normalized = title.lower()
    # Remove extra spaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    # Normalize parentheses variations: (Album Version), (album version), [Album Version] -> all to "(album version)"
    normalized = re.sub(r'[\[\{]', '(', normalized)
    normalized = re.sub(r'[\]\}]', ')', normalized)
    # Remove trailing/leading spaces around parentheses
    normalized = re.sub(r'\s*\(\s*', ' (', normalized)
    normalized = re.sub(r'\s*\)\s*', ')', normalized)
    return normalized

def main():
    db_path = "data/musique.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📊 Starting track deduplication...")
    
    # Get all tracks grouped by album
    cursor.execute("""
        SELECT id, album_id, title 
        FROM tracks 
        ORDER BY album_id, title
    """)
    
    all_tracks = cursor.fetchall()
    print(f"📈 Total tracks: {len(all_tracks)}")
    
    # Group by (album_id, normalized_title)
    groups = defaultdict(list)
    for track_id, album_id, title in all_tracks:
        normalized = normalize_title(title)
        key = (album_id, normalized)
        groups[key].append((track_id, title))
    
    # Find duplicates
    duplicates = {key: tracks for key, tracks in groups.items() if len(tracks) > 1}
    print(f"🔍 Found {len(duplicates)} groups with duplicate titles")
    
    if not duplicates:
        print("✅ No duplicates found!")
        conn.close()
        return
    
    # Merge duplicates
    total_merged = 0
    deletions = []
    
    for (album_id, normalized_title), tracks in duplicates.items():
        # Sort by track_id to keep the first one
        tracks.sort(key=lambda x: x[0])
        keep_track_id = tracks[0][0]
        
        print(f"\n📌 Album ID {album_id}: '{normalized_title}'")
        print(f"   Keep: ID {keep_track_id} - {tracks[0][1]}")
        
        # Redirect listening_history entries from duplicates to keep_track_id
        for i, (track_id, title) in enumerate(tracks[1:], 1):
            print(f"   Delete: ID {track_id} - {title}")
            
            # Count entries to be moved
            cursor.execute(
                "SELECT COUNT(*) FROM listening_history WHERE track_id = ?",
                (track_id,)
            )
            count = cursor.fetchone()[0]
            print(f"      → Moving {count} listening_history entries")
            
            # Update listening_history
            cursor.execute(
                "UPDATE listening_history SET track_id = ? WHERE track_id = ?",
                (keep_track_id, track_id)
            )
            
            deletions.append(track_id)
            total_merged += 1
    
    # Delete orphaned tracks
    print(f"\n🧹 Deleting {len(deletions)} duplicate track records...")
    for track_id in deletions:
        cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    
    conn.commit()
    print(f"✅ Deleted {len(deletions)} duplicate tracks")
    print(f"✅ Merged {total_merged} duplicate track entries")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM tracks")
    track_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM listening_history")
    history_count = cursor.fetchone()[0]
    
    print(f"\n📊 Final state:")
    print(f"   Total tracks: {track_count}")
    print(f"   Total listening_history entries: {history_count}")
    
    # Check for remaining duplicates in same album
    cursor.execute("""
        SELECT album_id, COUNT(DISTINCT title) as unique_titles, COUNT(*) as total_tracks
        FROM tracks
        GROUP BY album_id
        HAVING COUNT(*) != COUNT(DISTINCT title)
    """)
    
    remaining = cursor.fetchall()
    if remaining:
        print(f"\n⚠️  Still {len(remaining)} albums with potential duplicates:")
        for album_id, unique, total in remaining:
            print(f"   Album {album_id}: {unique} unique titles, {total} total tracks")
    else:
        print(f"\n✅ No remaining duplicate titles in any album!")
    
    conn.close()

if __name__ == "__main__":
    main()
