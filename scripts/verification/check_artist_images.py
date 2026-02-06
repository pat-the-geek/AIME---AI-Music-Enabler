#!/usr/bin/env python3
"""Vérifier si les images d'artiste sont bien dans la base de données."""

import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('data/musique.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Prendre le premier album et vérifier s'il a des images d'artiste
cursor.execute("""
    SELECT a.id, a.title
    FROM albums a
    LIMIT 1
""")
album = cursor.fetchone()

if album:
    album_id = album[0]
    album_title = album[1]
    print(f"Album testé: {album_id} - {album_title}")
    
    # Récupérer les artistes de cet album
    cursor.execute("""
        SELECT a.id, a.name
        FROM artists a
        JOIN album_artist aa ON a.id = aa.artist_id
        WHERE aa.album_id = ?
    """, (album_id,))
    
    artists = cursor.fetchall()
    print(f"Artistes: {len(artists)}")
    
    for artist in artists:
        artist_id = artist[0]
        artist_name = artist[1]
        print(f"  - {artist_id}: {artist_name}")
        
        # Vérifier s'il y a des images d'artiste
        cursor.execute("""
            SELECT id, url, image_type, source
            FROM images
            WHERE artist_id = ? AND image_type = 'artist'
        """, (artist_id,))
        
        images = cursor.fetchall()
        print(f"    Images d'artiste: {len(images)}")
        for img in images:
            print(f"      - {img[2]} ({img[3]}): {img[1][:60]}...")

# Compter combien d'images d'artiste au total
cursor.execute("SELECT COUNT(*) as total FROM images WHERE image_type = 'artist'")
total = cursor.fetchone()[0]
print(f"\nTotal d'images d'artiste en base: {total}")

conn.close()
