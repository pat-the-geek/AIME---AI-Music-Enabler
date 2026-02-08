#!/usr/bin/env python3
"""Debug script to test metadata loading in get_album()"""

import sys
sys.path.insert(0, '.')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Album, Metadata
from app.database import Base
from app.services.collection.album_service import AlbumService

# Create in-memory DB for testing
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Create an album
album = Album(title='Test Album', source='manual')
session.add(album)
session.commit()

print(f"Created album with ID: {album.id}")

# Create metadata for the album
metadata = Metadata(album_id=album.id, ai_info='Test metadata')
session.add(metadata)
session.commit()

print(f"Created metadata: {metadata}")
print(f"Metadata album_id: {metadata.album_id}")

# Get the album using service
service = AlbumService()
retrieved_album = service.get_album(session, album.id)

print(f"\nRetrieved album: {retrieved_album}")
print(f"Album type: {type(retrieved_album)}")
print(f"Album ID: {retrieved_album.id if retrieved_album else None}")

if retrieved_album:
    print(f"Has album_metadata attr: {hasattr(retrieved_album, 'album_metadata')}")
    if hasattr(retrieved_album, 'album_metadata'):
        print(f"album_metadata value: {retrieved_album.album_metadata}")
        print(f"album_metadata is None: {retrieved_album.album_metadata is None}")
    
    # Also check the raw relationship
    session.refresh(retrieved_album)
    print(f"\nAfter refresh:")
    print(f"album_metadata value: {retrieved_album.album_metadata}")
