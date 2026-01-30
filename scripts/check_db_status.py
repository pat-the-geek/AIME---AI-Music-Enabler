#!/usr/bin/env python3
"""Vérifier l'état de la base de données pour l'enrichissement."""
import sqlite3

conn = sqlite3.connect('data/musique.db')
c = conn.cursor()

# Albums sans metadata
result = c.execute('SELECT COUNT(*) FROM albums a WHERE NOT EXISTS (SELECT 1 FROM metadata m WHERE m.album_id = a.id)').fetchone()
print(f'Albums sans metadata: {result[0]}')

# Albums avec metadata mais sans ai_info
result = c.execute('SELECT COUNT(*) FROM albums a JOIN metadata m ON a.id = m.album_id WHERE m.ai_info IS NULL').fetchone()
print(f'Albums avec metadata mais sans ai_info: {result[0]}')

# Albums sans spotify_url
result = c.execute('SELECT COUNT(*) FROM albums WHERE spotify_url IS NULL').fetchone()
print(f'Albums sans spotify_url: {result[0]}')

# Total albums
result = c.execute('SELECT COUNT(*) FROM albums').fetchone()
print(f'Total albums: {result[0]}')

# Albums avec ai_info
result = c.execute('SELECT COUNT(*) FROM metadata WHERE ai_info IS NOT NULL').fetchone()
print(f'Albums avec ai_info: {result[0]}')

# Exemple d'albums à enrichir
print('\n3 exemples d\'albums à enrichir:')
results = c.execute('''
    SELECT a.id, a.title, a.spotify_url IS NOT NULL as has_spotify, m.ai_info IS NOT NULL as has_ai
    FROM albums a 
    LEFT JOIN metadata m ON a.id = m.album_id 
    WHERE m.ai_info IS NULL OR m.id IS NULL OR a.spotify_url IS NULL
    LIMIT 3
''').fetchall()

for row in results:
    print(f'  ID {row[0]}: {row[1][:40]} - Spotify:{row[2]} AI:{row[3]}')

conn.close()
