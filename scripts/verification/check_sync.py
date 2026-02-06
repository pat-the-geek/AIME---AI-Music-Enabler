#!/usr/bin/env python3
"""Vérifier l'état de la synchronisation."""
import sqlite3

db_path = "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler/data/musique.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Total albums
cursor.execute("SELECT COUNT(*) FROM albums")
total = cursor.fetchone()[0]
print(f"✅ Total albums: {total}")

# Chercher l'album cyrillique
cursor.execute("SELECT id, title, year FROM albums WHERE title LIKE ?", ('%Приказна%',))
cyrillic = cursor.fetchall()

if cyrillic:
    print(f"\n✅ Album cyrillique TROUVÉ:")
    for album_id, title, year in cyrillic:
        print(f"   ID: {album_id}")
        print(f"   Titre: {title}")
        print(f"   Année: {year}")
        
        # Vérifier les artistes
        cursor.execute("""
            SELECT a.name 
            FROM artists a 
            JOIN album_artist aa ON a.id = aa.artist_id 
            WHERE aa.album_id = ?
        """, (album_id,))
        artists = cursor.fetchall()
        print(f"   Artistes: {', '.join([a[0] for a in artists])}")
else:
    print("\n❌ Album cyrillique NON trouvé dans la base")

# Vérifier encodage
cursor.execute("SELECT title FROM albums WHERE title LIKE '%р%' OR title LIKE '%и%' LIMIT 5")
utf8_albums = cursor.fetchall()
if utf8_albums:
    print(f"\n✅ Encodage UTF-8 supporté ({len(utf8_albums)} albums avec caractères spéciaux)")

conn.close()

print(f"\n📊 Synchronisation: {total}/235 albums importés ({total/235*100:.1f}%)")
if total >= 225:
    print("✅ Synchronisation quasi-complète!")
elif total < 50:
    print("⚠️  Relancer la synchronisation complète")
