"""Créer les tables de collections."""
from app.database import Base, engine
from app.models import AlbumCollection, CollectionAlbum

def create_collection_tables():
    """Créer les tables pour les collections d'albums."""
    print("Création des tables de collections...")
    
    # Créer toutes les tables qui n'existent pas
    Base.metadata.create_all(bind=engine)
    
    print("✅ Tables créées avec succès!")
    
    # Vérifier
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if 'album_collections' in tables:
        print("✅ Table album_collections créée")
    if 'collection_albums' in tables:
        print("✅ Table collection_albums créée")
    
    print(f"\nToutes les tables: {', '.join(tables)}")

if __name__ == '__main__':
    create_collection_tables()
