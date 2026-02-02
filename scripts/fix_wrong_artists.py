#!/usr/bin/env python3
"""Corriger les artistes et images erronés."""
import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app.models import Album, Artist, Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_more_songs_album():
    """Corriger l'album 'More Songs About Buildings and Food'."""
    db = SessionLocal()
    
    try:
        print("\n🔧 CORRECTION: More Songs About Buildings and Food")
        print("=" * 60)
        
        # Trouver l'album
        album = db.query(Album).filter_by(
            title="More Songs About Buildings and Food"
        ).first()
        
        if not album:
            print("❌ Album non trouvé")
            return
        
        print(f"\n📀 Album trouvé (ID: {album.id})")
        print(f"   Artistes actuels: {[a.name for a in album.artists]}")
        
        # Supprimer Supertramp de cet album
        supertramp = db.query(Artist).filter_by(name="Supertramp").first()
        if supertramp and supertramp in album.artists:
            album.artists.remove(supertramp)
            print(f"   ✅ Supertramp retiré")
        
        # S'assurer que Talking Heads est le seul artiste
        talking_heads = db.query(Artist).filter_by(name="Talking Heads").first()
        if not talking_heads:
            talking_heads = Artist(name="Talking Heads")
            db.add(talking_heads)
            db.flush()
            print(f"   ✅ Talking Heads créé")
        
        if talking_heads not in album.artists:
            album.artists.append(talking_heads)
            print(f"   ✅ Talking Heads ajouté")
        
        # Nettoyer les images incorrectes (Supertramp)
        print(f"\n🖼️  Images actuelles: {len(album.images)}")
        for img in list(album.images):
            print(f"   - {img.source}: {img.url[:60]}...")
            # Si l'URL contient "f82d2bd1097e3e60a6a0" (Supertramp), la supprimer
            if "f82d2bd1097e3e60a6a0" in img.url:
                print(f"     ❌ Image Supertramp détectée, suppression...")
                db.delete(img)
        
        db.commit()
        
        print(f"\n✅ Correction terminée!")
        print(f"   Artistes finaux: {[a.name for a in album.artists]}")
        print(f"   Images restantes: {len(album.images)}")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        db.rollback()
    finally:
        db.close()


def check_suspicious_albums():
    """Vérifier s'il y a d'autres albums suspects."""
    db = SessionLocal()
    
    try:
        print("\n\n🔍 RECHERCHE D'AUTRES ALBUMS SUSPECTS")
        print("=" * 60)
        
        # Chercher les albums avec Supertramp
        supertramp = db.query(Artist).filter_by(name="Supertramp").first()
        if supertramp:
            print(f"\n📊 Albums de Supertramp:")
            for album in supertramp.albums:
                other_artists = [a.name for a in album.artists if a.name != "Supertramp"]
                if other_artists:
                    print(f"   ⚠️  {album.title}")
                    print(f"      Autres artistes: {other_artists}")
                else:
                    print(f"   ✅ {album.title}")
        
        # Chercher les albums avec Talking Heads
        talking_heads = db.query(Artist).filter_by(name="Talking Heads").first()
        if talking_heads:
            print(f"\n📊 Albums de Talking Heads:")
            for album in talking_heads.albums:
                other_artists = [a.name for a in album.artists if a.name != "Talking Heads"]
                if other_artists:
                    print(f"   ⚠️  {album.title}")
                    print(f"      Autres artistes: {other_artists}")
                else:
                    print(f"   ✅ {album.title}")
        
    finally:
        db.close()


if __name__ == '__main__':
    fix_more_songs_album()
    check_suspicious_albums()
    
    print("\n\n💡 Recommandation:")
    print("   Si des images sont manquantes, lancez:")
    print("   python scripts/import_lastfm_history.py 10 --no-skip-existing")
    print("   pour ré-enrichir les albums")
