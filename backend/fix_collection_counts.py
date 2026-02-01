"""Réparer les collections créées avant la correction du bug."""
from app.database import SessionLocal
from app.models import AlbumCollection, CollectionAlbum
from app.services.album_collection_service import AlbumCollectionService
from sqlalchemy import func

def fix_collection_counts():
    """Corriger les album_count pour toutes les collections."""
    db = SessionLocal()
    service = AlbumCollectionService(db)
    
    collections = db.query(AlbumCollection).all()
    print(f"Réparation de {len(collections)} collections...")
    
    for collection in collections:
        # Compter les albums réels
        real_count = db.query(func.count(CollectionAlbum.album_id)).filter(
            CollectionAlbum.collection_id == collection.id
        ).scalar() or 0
        
        # Mettre à jour si différent
        if collection.album_count != real_count:
            old_count = collection.album_count
            collection.album_count = real_count
            db.commit()
            print(f"  {collection.name}: {old_count} → {real_count}")
        else:
            print(f"  {collection.name}: {collection.album_count} ✓")
    
    print("\n✅ Réparation terminée!")
    db.close()

if __name__ == '__main__':
    fix_collection_counts()
