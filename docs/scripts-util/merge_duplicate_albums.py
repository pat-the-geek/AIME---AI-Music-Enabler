#!/usr/bin/env python3
"""
Merge duplicate albums and redirect all tracks to keep the album with most tracks.
"""
import sqlite3
import re
from collections import defaultdict

def normalize_album_title(title: str) -> str:
    """Normalize album title for duplicate detection."""
    if not title:
        return ""
    normalized = title.lower()
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def main():
    db_path = "data/musique.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Analyzing albums for duplicates...")
    
    cursor.execute("SELECT id, title FROM albums ORDER BY title")
    all_albums = cursor.fetchall()
    
    # Group by normalized title
    groups = defaultdict(list)
    for album_id, title in all_albums:
        normalized = normalize_album_title(title)
        groups[normalized].append((album_id, title))
    
    duplicates = {key: albums for key, albums in groups.items() if len(albums) > 1}
    
    print(f"📊 Found {len(duplicates)} album groups with duplicates\n")
    
    total_albums_merged = 0
    total_tracks_merged = 0
    album_deletions = []
    
    for normalized_title, albums in sorted(duplicates.items()):
        # Count tracks for each album
        albums_with_counts = []
        for album_id, title in albums:
            cursor.execute("SELECT COUNT(*) FROM tracks WHERE album_id = ?", (album_id,))
            count = cursor.fetchone()[0]
            albums_with_counts.append((album_id, title, count))
        
        # Sort by track count (descending) to keep the one with most tracks
        albums_with_counts.sort(key=lambda x: x[2], reverse=True)
        keep_album_id, keep_title, keep_count = albums_with_counts[0]
        
        if len(albums_with_counts) > 1:
            print(f"📌 '{normalized_title}'")
            print(f"   ✓ Keep: ID {keep_album_id} - '{keep_title}' ({keep_count} tracks)")
            
            # Redirect all other albums' tracks to the main album
            for album_id, title, count in albums_with_counts[1:]:
                print(f"   → Merge: ID {album_id} - '{title}' ({count} tracks)")
                
                # Update tracks
                cursor.execute(
                    "UPDATE tracks SET album_id = ? WHERE album_id = ?",
                    (keep_album_id, album_id)
                )
                
                album_deletions.append(album_id)
                total_tracks_merged += count
                total_albums_merged += 1
    
    # Delete empty albums
    print(f"\n🧹 Deleting {len(album_deletions)} duplicate album records...")
    for album_id in album_deletions:
        cursor.execute("DELETE FROM albums WHERE id = ?", (album_id,))
    
    conn.commit()
    
    print(f"✅ Merged {total_albums_merged} duplicate albums")
    print(f"✅ Redirected {total_tracks_merged} tracks to consolidated albums")
    
    # Verify final state
    cursor.execute("SELECT COUNT(*) FROM albums")
    album_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tracks")
    track_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM listening_history")
    history_count = cursor.fetchone()[0]
    
    print(f"\n📊 Final state:")
    print(f"   Albums: {album_count}")
    print(f"   Tracks: {track_count}")
    print(f"   History entries: {history_count}")
    
    conn.close()

if __name__ == "__main__":
    main()
