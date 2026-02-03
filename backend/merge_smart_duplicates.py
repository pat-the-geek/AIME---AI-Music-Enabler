#!/usr/bin/env python3
"""
Script de fusion intelligente des albums doublons.

Fusionne les albums avec le même titre mais artistes légèrement différents
en gardant les données d'historique d'écoute.
"""
import sys
import difflib
from sqlalchemy import and_
from app.database import SessionLocal
from app.models import Album, Artist, Track, ListeningHistory, Image, Metadata

def normalize_artist_name(name: str) -> str:
    """Normaliser les noms d'artistes pour les comparer."""
    # Enlever les majuscules, espaces, tirets et caractères spéciaux
    normalized = name.upper()
    # Enlever les numéros entre parenthèses (ex: "La Femme (4)" -> "LA FEMME")
    normalized = normalized.split('(')[0].strip()
    return normalized

def are_artists_similar(artists_a, artists_b) -> bool:
    """Vérifier si deux listes d'artistes sont similaires."""
    if not artists_a or not artists_b:
        return False
    
    # Normaliser
    norm_a = [normalize_artist_name(a.name) for a in artists_a]
    norm_b = [normalize_artist_name(a.name) for a in artists_b]
    
    # Si c'est un artiste unique, utiliser fuzzy matching
    if len(norm_a) == 1 and len(norm_b) == 1:
        ratio = difflib.SequenceMatcher(None, norm_a[0], norm_b[0]).ratio()
        return ratio > 0.85  # 85% de similarité
    
    # Sinon, vérifier si les ensembles sont identiques
    return set(norm_a) == set(norm_b)

print("🔍 Initialisation du script de fusion intelligente...", flush=True)

db = SessionLocal()

try:
    # Chercher les albums en doublon
    print("\n=== RECHERCHE DES ALBUMS DOUBLONS ===\n", flush=True)
    
    albums = db.query(Album).all()
    processed_ids = set()
    merged_count = 0
    
    for i, album_a in enumerate(albums):
        if album_a.id in processed_ids:
            continue
        
        for album_b in albums[i+1:]:
            if album_b.id in processed_ids:
                continue
            
            # Vérifier si les titres correspondent
            if album_a.title != album_b.title:
                continue
            
            # Vérifier si les artistes sont similaires
            if not are_artists_similar(album_a.artists, album_b.artists):
                continue
            
            # C'est un doublon ! Fusionner
            print(f"🎵 Doublon détecté: '{album_a.title}'", flush=True)
            print(f"   Album A - ID {album_a.id}: {album_a.source:8s} | artists={', '.join([a.name for a in album_a.artists])}", flush=True)
            print(f"   Album B - ID {album_b.id}: {album_b.source:8s} | artists={', '.join([a.name for a in album_b.artists])}", flush=True)
            
            # Choisir le meilleur album (celui avec le plus de données d'écoute)
            histories_a = sum(len(t.listening_history) for t in album_a.tracks)
            histories_b = sum(len(t.listening_history) for t in album_b.tracks)
            
            if histories_a >= histories_b:
                best_album = album_a
                dup_album = album_b
                best_has_more = histories_a > histories_b
            else:
                best_album = album_b
                dup_album = album_a
                best_has_more = True
            
            histories_best = sum(len(t.listening_history) for t in best_album.tracks)
            histories_dup = sum(len(t.listening_history) for t in dup_album.tracks)
            
            print(f"   ✓ Fusion vers l'album ID {best_album.id} ({histories_best} historiques)")
            
            # Copier les données manquantes
            if not best_album.spotify_url and dup_album.spotify_url:
                best_album.spotify_url = dup_album.spotify_url
            if not best_album.year and dup_album.year:
                best_album.year = dup_album.year
            if not best_album.genre and dup_album.genre:
                best_album.genre = dup_album.genre
            # Ne pas copier les discogs_id car c'est UNIQUE et peut causer des conflits
            # Les images discogs serviront de référence
            
            # Normaliser les artistes vers la version du meilleur album
            dup_album.artists = best_album.artists
            
            # Fusionner les images
            for image in dup_album.images:
                existing = db.query(Image).filter(
                    Image.album_id == best_album.id,
                    Image.image_type == image.image_type,
                    Image.source == image.source
                ).first()
                
                if not existing:
                    image.album_id = best_album.id
                    print(f"   ✓ Image déplacée: {image.source}", flush=True)
                else:
                    db.delete(image)
            
            # Fusionner les métadonnées
            if dup_album.album_metadata and not best_album.album_metadata:
                dup_album.album_metadata.album_id = best_album.id
            elif dup_album.album_metadata and best_album.album_metadata:
                if not best_album.album_metadata.ai_info and dup_album.album_metadata.ai_info:
                    best_album.album_metadata.ai_info = dup_album.album_metadata.ai_info
                db.delete(dup_album.album_metadata)
            
            # Fusionner les tracks
            for track_dup in dup_album.tracks:
                existing_track = db.query(Track).filter(
                    Track.album_id == best_album.id,
                    Track.title == track_dup.title
                ).first()
                
                if not existing_track:
                    track_dup.album_id = best_album.id
                    print(f"   ✓ Track déplacé: {track_dup.title}", flush=True)
                else:
                    # Fusionner les historiques d'écoute
                    for history in track_dup.listening_history:
                        existing_history = db.query(ListeningHistory).filter(
                            ListeningHistory.track_id == existing_track.id,
                            ListeningHistory.timestamp == history.timestamp,
                            ListeningHistory.source == history.source
                        ).first()
                        
                        if not existing_history:
                            history.track_id = existing_track.id
                        else:
                            db.delete(history)
                    
                    # Supprimer le track dupliqué
                    db.delete(track_dup)
            
            # Supprimer l'album dupliqué
            db.delete(dup_album)
            processed_ids.add(dup_album.id)
            merged_count += 1
            print()
    
    if merged_count > 0:
        db.commit()
        print(f"\n✅ Fusion complétée!", flush=True)
        print(f"   Albums fusionnés: {merged_count}", flush=True)
    else:
        print(f"\n✅ Aucun doublon détecté!", flush=True)
    
except Exception as e:
    print(f"\n❌ Erreur: {e}", flush=True)
    import traceback
    traceback.print_exc()
    db.rollback()
    sys.exit(1)
finally:
    db.close()
