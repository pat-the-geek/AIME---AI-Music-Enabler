#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/data/musique.db')
c = conn.cursor()

# Chercher l'album ID 1360
c.execute('''
SELECT 
  a.id,
  a.title,
  a.year,
  a.spotify_url,
  a.discogs_url,
  GROUP_CONCAT(ar.name, ', ') as artists
FROM albums a
LEFT JOIN album_artist aa ON a.id = aa.album_id
LEFT JOIN artists ar ON aa.artist_id = ar.id
WHERE a.id = 1360
GROUP BY a.id
''')

album = c.fetchone()
if album:
    print("Album ID 1360 - Détails complets:")
    print(f"  Titre: {album[1]}")
    print(f"  Titre (repr): {repr(album[1])}")
    print(f"  Année: {album[2]}")
    print(f"  Spotify URL: {album[3]}")
    print(f"  Discogs URL: {album[4]}")
    print(f"  Artistes: {album[5]}")
    
    # Analyser les caractères du titre
    print(f"\n  Analyse caractère par caractère du titre:")
    for i, char in enumerate(album[1]):
        print(f"    Pos {i}: '{char}' (U+{ord(char):04X} {repr(char)})")

conn.close()
