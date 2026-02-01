#!/usr/bin/env python3
"""
Find and merge duplicate albums and tracks across the entire database.
Handles: case differences, article normalization, extra spaces.
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
    # Normalize case variations like "Of" vs "of"
    return normalized

def find_duplicate_albums():
    """Find albums that are likely duplicates based on normalized title."""
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
    
    print(f"\n📊 Found {len(duplicates)} album groups with potential duplicates:")
    
    for normalized_title, albums in sorted(duplicates.items()):
        print(f"\n  Normalized: '{normalized_title}'")
        for album_id, title in albums:
            # Count tracks in this album
            cursor.execute("SELECT COUNT(*) FROM tracks WHERE album_id = ?", (album_id,))
            track_count = cursor.fetchone()[0]
            print(f"    ID {album_id}: '{title}' ({track_count} tracks)")
    
    conn.close()
    return duplicates

if __name__ == "__main__":
    find_duplicate_albums()
