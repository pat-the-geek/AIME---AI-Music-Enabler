#!/usr/bin/env python3
"""
Chercher les albums potentiellement doublonnés avec artistes différents ou sources différentes.
"""
from sqlalchemy import func
from app.database import SessionLocal
from app.models import Album, Artist

db = SessionLocal()

# Chercher tous les albums avec le même titre mais des artistes différents
print("\n🔍 Recherche des albums avec même titre mais artistes différents...\n")

# Grouper par titre et compter les combinaisons
albums = db.query(Album).all()

title_groups = {}
for album in albums:
    title = album.title
    if title not in title_groups:
        title_groups[title] = []
    artist_names = sorted([a.name for a in album.artists])
    title_groups[title].append({
        'id': album.id,
        'source': album.source,
        'artists': artist_names,
        'year': album.year,
        'images': len(album.images),
        'tracks': len(album.tracks),
        'histories': sum(len(t.listening_history) for t in album.tracks)
    })

# Afficher les possibles doublons
found_any = False
for title, albums_list in sorted(title_groups.items()):
    if len(albums_list) > 1:
        # Vérifier si les artistes sont identiques
        first_artists = frozenset(albums_list[0]['artists'])
        all_same = all(frozenset(a['artists']) == first_artists for a in albums_list)
        
        if not all_same or len(set(a['source'] for a in albums_list)) > 1:
            found_any = True
            print(f"⚠️  '{title}':")
            for a in albums_list:
                artists_str = ', '.join(a['artists']) if a['artists'] else '(aucun artiste)'
                print(f"   ID {a['id']:4d}: source={a['source']:8s} | artists={artists_str:40s} | year={str(a['year']):4s} | img={a['images']} | tracks={a['tracks']} | histories={a['histories']}")
            print()

if not found_any:
    print("✅ Aucun doublon détecté après fusion!\n")

db.close()
