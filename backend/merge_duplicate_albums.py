#!/usr/bin/env python3
"""
Script de fusion des albums doublons par titre et artistes.

Identifie les albums avec le même titre et les mêmes artistes,
puis les fusionne en gardant les meilleures données.
"""
import sys
from sqlalchemy import and_, func
from app.database import SessionLocal
from app.models import Album, Artist, Track, ListeningHistory, Image, Metadata

print("🔍 Initialisation du script de fusion...", flush=True)

db = SessionLocal()

try:
    # Trouver les albums doublons (même titre + mêmes artistes)
    print("\n=== RECHERCHE DES DOUBLONS ===\n", flush=True)
    
    # Grouper par titre et artistes
    album_groups = db.query(
        Album.title,
        func.group_concat(Album.id).label('album_ids'),
        func.count(Album.id).label('count')
    ).group_by(Album.title).having(func.count(Album.id) > 1).all()
    
    total_duplicates = 0
    total_merged = 0
    
    for group in album_groups:
        title = group[0]
        album_ids = list(map(int, group[1].split(',')))
        count = group[2]
        
        # Charger les albums complets
        albums = db.query(Album).filter(Album.id.in_(album_ids)).all()
        
        # Vérifier si ce sont vraiment les mêmes (mêmes artistes)
        album_artist_sets = []
        for album in albums:
            artist_ids = sorted([a.id for a in album.artists])
            album_artist_sets.append(set(artist_ids))
        
        # Si tous les albums ont les mêmes artistes, c'est un vrai doublon
        if all(artist_set == album_artist_sets[0] for artist_set in album_artist_sets):
            total_duplicates += count
            
            print(f"🎵 Album en doublon trouvé: '{title}'", flush=True)
            for album in albums:
                artist_names = ", ".join([a.name for a in album.artists])
                print(f"   - ID {album.id}: source='{album.source}', year={album.year}, "
                      f"artists='{artist_names}', images={len(album.images)}, "
                      f"tracks={len(album.tracks)}", flush=True)
            
            # Fusionner les albums
            # 1. Garder l'album avec le plus de données
            best_album = max(albums, key=lambda a: (
                bool(a.spotify_url),
                bool(a.year),
                len(a.images),
                len(a.tracks),
                1 if a.album_metadata else 0
            ))
            
            print(f"   ✓ Fusion vers l'album ID {best_album.id}", flush=True)
            
            # 2. Déplacer les données des autres albums vers le meilleur
            for album in albums:
                if album.id == best_album.id:
                    continue
                
                # Copier les données manquantes du meilleur album
                if not best_album.spotify_url and album.spotify_url:
                    best_album.spotify_url = album.spotify_url
                if not best_album.year and album.year:
                    best_album.year = album.year
                if not best_album.genre and album.genre:
                    best_album.genre = album.genre
                if not best_album.discogs_id and album.discogs_id:
                    best_album.discogs_id = album.discogs_id
                if not best_album.discogs_url and album.discogs_url:
                    best_album.discogs_url = album.discogs_url
                
                # Fusionner les images
                for image in album.images:
                    # Vérifier si une image similaire existe déjà
                    existing = db.query(Image).filter(
                        Image.album_id == best_album.id,
                        Image.image_type == image.image_type,
                        Image.source == image.source
                    ).first()
                    
                    if not existing:
                        image.album_id = best_album.id
                        print(f"   ✓ Image déplacée: {image.source}/{image.image_type}", flush=True)
                    else:
                        # Supprimer le doublon d'image
                        db.delete(image)
                
                # Fusionner les métadonnées
                if album.album_metadata and not best_album.album_metadata:
                    best_album.album_metadata = album.album_metadata
                    best_album.album_metadata.album_id = best_album.id
                    print(f"   ✓ Métadonnées déplacées", flush=True)
                elif album.album_metadata and best_album.album_metadata:
                    # Fusionner les infos IA
                    if not best_album.album_metadata.ai_info and album.album_metadata.ai_info:
                        best_album.album_metadata.ai_info = album.album_metadata.ai_info
                    db.delete(album.album_metadata)
                
                # Rediriger les tracks vers le meilleur album
                for track in album.tracks:
                    existing_track = db.query(Track).filter(
                        Track.album_id == best_album.id,
                        Track.title == track.title
                    ).first()
                    
                    if not existing_track:
                        track.album_id = best_album.id
                        print(f"   ✓ Track déplacé: {track.title}", flush=True)
                    else:
                        # Fusionner les historiques d'écoute
                        for history in track.listening_history:
                            # Vérifier si cet historique existe déjà
                            existing_history = db.query(ListeningHistory).filter(
                                ListeningHistory.track_id == existing_track.id,
                                ListeningHistory.timestamp == history.timestamp,
                                ListeningHistory.source == history.source
                            ).first()
                            
                            if not existing_history:
                                history.track_id = existing_track.id
                                print(f"   ✓ Historique déplacé: {history.date}", flush=True)
                            else:
                                # Doublon d'historique, supprimer
                                db.delete(history)
                        
                        # Supprimer le track dupliqué
                        db.delete(track)
                
                # Supprimer l'album dupliqué
                db.delete(album)
                total_merged += 1
                print(f"   ✓ Album ID {album.id} supprimé", flush=True)
            
            print()
    
    if total_duplicates > 0:
        db.commit()
        print(f"\n✅ Fusion complétée!", flush=True)
        print(f"   Doublons trouvés: {total_duplicates}", flush=True)
        print(f"   Albums supprimés: {total_merged}", flush=True)
    else:
        print(f"\n✅ Aucun doublon trouvé!", flush=True)
    
except Exception as e:
    print(f"\n❌ Erreur: {e}", flush=True)
    db.rollback()
    sys.exit(1)
finally:
    db.close()
