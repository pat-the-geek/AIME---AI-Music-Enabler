#!/usr/bin/env python3
"""Script pour corriger les problèmes d'import Last.fm identifiés."""
import sys
import os

# Ajouter le chemin du backend au PYTHONPATH
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app.models import Album, Artist, ListeningHistory, Track, Image
from collections import defaultdict
import logging
from sqlalchemy import and_, func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def merge_albums_with_same_title():
    """Fusionner les albums portant le même titre mais avec artistes différents."""
    db = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print("🔀 FUSION - Albums avec même titre")
        print("=" * 60)
        
        # Trouver les albums avec même titre
        album_titles = db.query(Album.title, func.count(Album.id)).group_by(
            Album.title
        ).having(func.count(Album.id) > 1).all()
        
        print(f"\n📊 Albums trouvés avec doublons de titre: {len(album_titles)}")
        
        merged_count = 0
        for title, count in album_titles:
            albums = db.query(Album).filter_by(title=title).all()
            
            print(f"\n  📀 {title} ({count} versions):")
            
            # Garder le premier, fusionner les autres
            primary_album = albums[0]
            print(f"     → Version primaire (ID={primary_album.id})")
            
            for album in albums[1:]:
                print(f"     → Fusion album ID={album.id}")
                
                # Fusionner les artistes
                for artist in album.artists:
                    if artist not in primary_album.artists:
                        primary_album.artists.append(artist)
                        print(f"        + Artiste: {artist.name}")
                
                # Fusionner les images
                for img in album.images:
                    # Vérifier que l'image n'existe pas déjà
                    existing = db.query(Album).filter_by(id=primary_album.id).first().images
                    if not any(e.url == img.url for e in existing):
                        img.album_id = primary_album.id
                        print(f"        + Image: {img.source}")
                
                # Fusionner les tracks
                for track in album.tracks:
                    # Vérifier si le track existe déjà dans l'album primaire
                    existing = db.query(Track).filter_by(
                        album_id=primary_album.id,
                        title=track.title
                    ).first()
                    
                    if not existing:
                        track.album_id = primary_album.id
                        print(f"        + Track: {track.title}")
                    else:
                        # Fusionner l'historique d'écoute
                        for history in track.listening_history:
                            history.track_id = existing.id
                        db.delete(track)
                
                # Supprimer l'album dupliqué
                db.delete(album)
                merged_count += 1
            
            db.commit()
        
        print(f"\n✅ {merged_count} albums fusionnés!")
        
    except Exception as e:
        logger.error(f"❌ Erreur fusion albums: {e}")
        db.rollback()
    finally:
        db.close()


def remove_duplicate_listening_history():
    """Supprimer les doublons dans l'historique d'écoute."""
    db = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print("🧹 SUPPRESSION - Doublons d'historique")
        print("=" * 60)
        
        # Trouver les scrobbles dupliqués
        duplicates = db.query(
            ListeningHistory.track_id,
            ListeningHistory.timestamp,
            func.count(ListeningHistory.id)
        ).group_by(
            ListeningHistory.track_id,
            ListeningHistory.timestamp
        ).having(
            func.count(ListeningHistory.id) > 1
        ).all()
        
        print(f"\n📊 Doublons trouvés: {len(duplicates)}")
        
        removed_count = 0
        for track_id, timestamp, count in duplicates:
            # Récupérer toutes les entrées dupliquées
            entries = db.query(ListeningHistory).filter(
                and_(
                    ListeningHistory.track_id == track_id,
                    ListeningHistory.timestamp == timestamp
                )
            ).all()
            
            # Garder la première, supprimer les autres
            for entry in entries[1:]:
                track = db.query(Track).filter_by(id=track_id).first()
                if track:
                    print(f"  🗑️  Suppression: {track.title} @ {timestamp}")
                db.delete(entry)
                removed_count += 1
            
            db.commit()
        
        print(f"\n✅ {removed_count} doublons supprimés!")
        
    except Exception as e:
        logger.error(f"❌ Erreur suppression doublons: {e}")
        db.rollback()
    finally:
        db.close()


def ensure_album_artists_consistency():
    """S'assurer que chaque album a au moins un artiste."""
    db = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print("🎤 CORRECTION - Consistance Artistes")
        print("=" * 60)
        
        albums_without_artist = db.query(Album).filter(~Album.artists.any()).all()
        
        print(f"\n📊 Albums sans artiste: {len(albums_without_artist)}")
        
        fixed_count = 0
        for album in albums_without_artist:
            # Récupérer un artiste depuis les tracks
            track = db.query(Track).filter_by(album_id=album.id).first()
            if track:
                # Chercher un artiste du même album (via d'autres tracks)
                artist = db.query(Artist).join(Album.artists).filter(
                    Album.id == album.id
                ).first()
                
                if artist:
                    album.artists.append(artist)
                    print(f"  ✅ Artiste ajouté à {album.title}: {artist.name}")
                    fixed_count += 1
            
            db.commit()
        
        print(f"\n✅ {fixed_count} albums corrigés!")
        
    except Exception as e:
        logger.error(f"❌ Erreur correction artistes: {e}")
        db.rollback()
    finally:
        db.close()


def validate_image_urls():
    """Valider et corriger les URLs d'image."""
    db = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print("🖼️  VALIDATION - URLs d'Image")
        print("=" * 60)
        
        bad_images = db.query(Image).filter(
            ~Image.url.like('http://%') & ~Image.url.like('https://%')
        ).all()
        
        print(f"\n📊 Images avec URLs invalides: {len(bad_images)}")
        
        removed_count = 0
        for img in bad_images:
            print(f"  🗑️  Suppression: {img.source} - {img.url[:50]}...")
            db.delete(img)
            removed_count += 1
        
        db.commit()
        print(f"\n✅ {removed_count} images invalides supprimées!")
        
    except Exception as e:
        logger.error(f"❌ Erreur validation images: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Exécuter toutes les corrections."""
    print("\n")
    print("🔧 CORRECTION - Problèmes Import Last.fm")
    print("=" * 60)
    
    try:
        merge_albums_with_same_title()
        remove_duplicate_listening_history()
        ensure_album_artists_consistency()
        validate_image_urls()
        
        print("\n" + "=" * 60)
        print("✅ CORRECTIONS TERMINÉES")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
