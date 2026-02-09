"""Optimize database indexes for improved query performance.

Revision ID: 005_optimize_indexes
Revises: 004_add_scheduled_task_executions
Create Date: 2026-02-09 10:00:00.000000

This migration adds missing indexes to improve query performance across common patterns:
- Track lookup by album
- Listening history queries by date/timestamp/source
- Album lookups by external IDs
- Image queries by type
- Analytics queries with source and date
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_optimize_indexes'
down_revision = '004_add_scheduled_task_executions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add optimization indexes for improved performance."""
    
    # ============================
    # TRACKS TABLE INDEXES
    # ============================
    # Index for album_id lookups (foreign key join optimization)
    op.create_index(
        'idx_tracks_album_id',
        'tracks',
        ['album_id'],
        if_not_exists=True
    )
    
    # Composite index for finding tracks by album and title (search optimization)
    op.create_index(
        'idx_tracks_album_title',
        'tracks',
        ['album_id', 'title'],
        if_not_exists=True
    )
    
    # Index for Spotify ID lookups
    op.create_index(
        'idx_tracks_spotify_id',
        'tracks',
        ['spotify_id'],
        if_not_exists=True
    )
    
    # =================================
    # LISTENING HISTORY TABLE INDEXES
    # =================================
    # Composite index for track_id with timestamp (common join + sort pattern)
    op.create_index(
        'idx_history_track_timestamp',
        'listening_history',
        ['track_id', 'timestamp'],
        if_not_exists=True
    )
    
    # Composite index for timestamp + source queries (analytics)
    op.create_index(
        'idx_history_timestamp_source',
        'listening_history',
        ['timestamp', 'source'],
        if_not_exists=True
    )
    
    # Index for date-based analytics (grouping by date)
    op.create_index(
        'idx_history_date_source',
        'listening_history',
        ['date', 'source'],
        if_not_exists=True
    )
    
    # ===============================
    # ALBUM TABLE INDEXES
    # ===============================
    # Index for Discogs ID lookup (collection synchronization)
    op.create_index(
        'idx_albums_discogs_id',
        'albums',
        ['discogs_id'],
        if_not_exists=True
    )
    
    # Index for Spotify URL lookup
    op.create_index(
        'idx_albums_spotify_url',
        'albums',
        ['spotify_url'],
        if_not_exists=True
    )
    
    # Index for Discogs URL lookup
    op.create_index(
        'idx_albums_discogs_url',
        'albums',
        ['discogs_url'],
        if_not_exists=True
    )
    
    # Composite index for source + creation date (analytics, filtering by source)
    op.create_index(
        'idx_albums_source_created',
        'albums',
        ['source', 'created_at'],
        if_not_exists=True
    )
    
    # Composite index for title searching with source filtering
    op.create_index(
        'idx_albums_title_source',
        'albums',
        ['title', 'source'],
        if_not_exists=True
    )
    
    # Index for year-based queries
    op.create_index(
        'idx_albums_year',
        'albums',
        ['year'],
        if_not_exists=True
    )
    
    # ================================
    # IMAGE TABLE INDEXES
    # ================================
    # Composite indexes for artist image lookups by type
    op.create_index(
        'idx_images_artist_type',
        'images',
        ['artist_id', 'image_type'],
        if_not_exists=True
    )
    
    # Composite indexes for album image lookups by type
    op.create_index(
        'idx_images_album_type',
        'images',
        ['album_id', 'image_type'],
        if_not_exists=True
    )
    
    # Index for source-based image lookups
    op.create_index(
        'idx_images_source',
        'images',
        ['source'],
        if_not_exists=True
    )
    
    # ====================================
    # METADATA TABLE INDEXES
    # ====================================
    # Index for film year queries (if added)
    op.create_index(
        'idx_metadata_film_year',
        'metadata',
        ['film_year'],
        if_not_exists=True
    )
    
    # =======================================
    # ALBUM_ARTIST TABLE INDEXES (junction)
    # =======================================
    # Index for artist-based queries (find all albums by an artist)
    op.create_index(
        'idx_album_artist_artist_id',
        'album_artist',
        ['artist_id'],
        if_not_exists=True
    )
    
    # Index for album-based queries (find all artists in an album)
    op.create_index(
        'idx_album_artist_album_id',
        'album_artist',
        ['album_id'],
        if_not_exists=True
    )


def downgrade() -> None:
    """Remove optimization indexes."""
    
    # Remove album_artist indexes
    op.drop_index('idx_album_artist_album_id', table_name='album_artist', if_exists=True)
    op.drop_index('idx_album_artist_artist_id', table_name='album_artist', if_exists=True)
    
    # Remove metadata indexes
    op.drop_index('idx_metadata_film_year', table_name='metadata', if_exists=True)
    
    # Remove image indexes
    op.drop_index('idx_images_source', table_name='images', if_exists=True)
    op.drop_index('idx_images_album_type', table_name='images', if_exists=True)
    op.drop_index('idx_images_artist_type', table_name='images', if_exists=True)
    
    # Remove album indexes
    op.drop_index('idx_albums_year', table_name='albums', if_exists=True)
    op.drop_index('idx_albums_title_source', table_name='albums', if_exists=True)
    op.drop_index('idx_albums_source_created', table_name='albums', if_exists=True)
    op.drop_index('idx_albums_discogs_url', table_name='albums', if_exists=True)
    op.drop_index('idx_albums_spotify_url', table_name='albums', if_exists=True)
    op.drop_index('idx_albums_discogs_id', table_name='albums', if_exists=True)
    
    # Remove listening_history indexes
    op.drop_index('idx_history_date_source', table_name='listening_history', if_exists=True)
    op.drop_index('idx_history_timestamp_source', table_name='listening_history', if_exists=True)
    op.drop_index('idx_history_track_timestamp', table_name='listening_history', if_exists=True)
    
    # Remove tracks indexes
    op.drop_index('idx_tracks_spotify_id', table_name='tracks', if_exists=True)
    op.drop_index('idx_tracks_album_title', table_name='tracks', if_exists=True)
    op.drop_index('idx_tracks_album_id', table_name='tracks', if_exists=True)
