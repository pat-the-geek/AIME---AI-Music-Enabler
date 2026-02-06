#!/usr/bin/env python3
"""Script pour vérifier la qualité de l'import Last.fm."""
import sys
import os

# Ajouter le chemin du backend au PYTHONPATH
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app.models import Album, Artist, ListeningHistory, Image, Track
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_artist_quality():
    """Vérifier la qualité des artistes d'album."""
    db = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print("🎯 VÉRIFICATION - Artistes d'Albums")
        print("=" * 60)
        
        # Chercher les albums avec plusieurs artistes
        albums_with_multiple = []
        albums_with_single = []
        
        albums = db.query(Album).all()
        for album in albums[:100]:  # Vérifier les premiers 100
            if len(album.artists) > 1:
                albums_with_multiple.append((album.title, [a.name for a in album.artists]))
            elif len(album.artists) == 1:
                albums_with_single.append((album.title, album.artists[0].name))
        
        print(f"\n📊 Statistiques:")
        print(f"  - Albums avec plusieurs artistes: {len(albums_with_multiple)}")
        print(f"  - Albums avec 1 artiste: {len(albums_with_single)}")
        
        if albums_with_multiple:
            print(f"\n✅ Albums collaboratifs (bon signe!):")
            for title, artists in albums_with_multiple[:10]:
                print(f"   - {title}: {', '.join(artists)}")
        
    finally:
        db.close()


def check_duplicates():
    """Vérifier les doublons de scrobbles."""
    db = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print("🔍 VÉRIFICATION - Doublons de Scrobbles")
        print("=" * 60)
        
        # Chercher les scrobbles dupliqués
        duplicates = defaultdict(list)
        
        history = db.query(ListeningHistory).all()
        track_timestamps = defaultdict(list)
        
        for entry in history:
            key = (entry.track_id, entry.timestamp)
            track_timestamps[key].append(entry)
        
        # Trouver les doublons
        for key, entries in track_timestamps.items():
            if len(entries) > 1:
                track_id, timestamp = key
                track = db.query(Track).filter_by(id=track_id).first()
                if track:
                    duplicates[track.title].append((timestamp, len(entries)))
        
        print(f"\n📊 Résultats:")
        print(f"  - Total scrobbles: {len(history)}")
        print(f"  - Scrobbles uniques (track_id, timestamp): {len(track_timestamps)}")
        print(f"  - Combinaisons dupliquées: {len(duplicates)}")
        
        if duplicates:
            print(f"\n❌ Exemple de doublons:")
            for title, entries in list(duplicates.items())[:5]:
                print(f"   - {title}: {len(entries)} entrées")
        else:
            print(f"\n✅ Pas de doublons (track_id, timestamp) détectés!")
        
    finally:
        db.close()


def check_album_images():
    """Vérifier les images d'album."""
    db = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print("🖼️  VÉRIFICATION - Images d'Album")
        print("=" * 60)
        
        albums = db.query(Album).all()
        
        albums_with_images = 0
        albums_without_images = 0
        image_count_by_source = defaultdict(int)
        
        for album in albums:
            if album.images:
                albums_with_images += 1
                for img in album.images:
                    image_count_by_source[img.source] += 1
            else:
                albums_without_images += 1
        
        print(f"\n📊 Résultats:")
        print(f"  - Albums avec images: {albums_with_images}")
        print(f"  - Albums SANS images: {albums_without_images}")
        
        if image_count_by_source:
            print(f"\n📸 Images par source:")
            for source, count in sorted(image_count_by_source.items(), key=lambda x: -x[1]):
                print(f"   - {source}: {count} images")
        else:
            print(f"\n⚠️  Aucune image trouvée dans la base!")
        
        # Vérifier les URLs invalides
        bad_urls = 0
        for album in albums:
            for img in album.images:
                if not img.url or not img.url.startswith(('http://', 'https://')):
                    bad_urls += 1
        
        if bad_urls:
            print(f"\n⚠️  {bad_urls} URLs d'image invalides trouvées!")
        else:
            print(f"\n✅ Toutes les URLs d'image sont valides")
        
    finally:
        db.close()


def check_recent_imports():
    """Vérifier les imports récents."""
    db = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print("📥 VÉRIFICATION - Imports Récents")
        print("=" * 60)
        
        # Récupérer les 10 derniers scrobbles importés
        recent = db.query(ListeningHistory).filter_by(source='lastfm').order_by(
            ListeningHistory.timestamp.desc()
        ).limit(10).all()
        
        print(f"\n📋 Les 10 derniers scrobbles importés:")
        for i, entry in enumerate(recent, 1):
            track = entry.track
            album = track.album
            artists = ', '.join([a.name for a in album.artists])
            print(f"\n  {i}. {track.title}")
            print(f"     Album: {album.title}")
            print(f"     Artistes: {artists}")
            print(f"     Date: {entry.date}")
            print(f"     Images: {len(album.images)}")
        
    finally:
        db.close()


def main():
    """Exécuter tous les checks."""
    from datetime import datetime
    print("\n")
    print("🔧 DIAGNOSTIC - Qualité Import Last.fm")
    print("📅", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        check_artist_quality()
        check_duplicates()
        check_album_images()
        check_recent_imports()
        
        print("\n" + "=" * 60)
        print("✅ DIAGNOSTIC TERMINÉ")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
