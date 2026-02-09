"""Table de liaison Album-Artist (Many-to-Many)."""
from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base

album_artist = Table(
    'album_artist',
    Base.metadata,
    Column('album_id', Integer, ForeignKey('albums.id', ondelete='CASCADE'), primary_key=True),
    Column('artist_id', Integer, ForeignKey('artists.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now(), nullable=False),
    Index('idx_album_artist_album_id', 'album_id'),
    Index('idx_album_artist_artist_id', 'artist_id'),
)
