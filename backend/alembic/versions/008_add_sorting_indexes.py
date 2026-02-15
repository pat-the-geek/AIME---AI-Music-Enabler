"""Add indexes for efficient sorting operations.

Revision ID: 008_add_sorting_indexes
Revises: 007_add_apple_music_url
Create Date: 2026-02-15 10:00:00.000000

This migration adds composite and single-column indexes to optimize sorting
by title, artist, year, and support when paginating through the album collection.

Indexes added:
- idx_albums_title_year: For sorting by title and year (composite)
- idx_albums_year_title: For sorting by year and title (composite)
- idx_albums_source_support: For filtering by source and sorting by support
- idx_artist_name: For sorting by artist name (reverse)
- idx_albums_created_title: For sorting by created_at and title
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_add_sorting_indexes'
down_revision = '007_add_apple_music_url'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add sorting indexes."""
    
    # Composite index for sorting by title and year
    op.create_index(
        'idx_albums_title_year',
        'albums',
        ['title', 'year'],
        if_not_exists=True
    )
    
    # Composite index for sorting by year and title
    op.create_index(
        'idx_albums_year_title',
        'albums',
        ['year', 'title'],
        if_not_exists=True
    )
    
    # Composite index for source and support filtering/sorting
    op.create_index(
        'idx_albums_source_support',
        'albums',
        ['source', 'support'],
        if_not_exists=True
    )
    
    # Index for artist name sorting
    op.create_index(
        'idx_artist_name_sort',
        'artists',
        ['name'],
        if_not_exists=True
    )
    
    # Composite index for sorting by created_at and title
    op.create_index(
        'idx_albums_created_title',
        'albums',
        ['created_at', 'title'],
        if_not_exists=True
    )
    
    # Index on album_artist table for efficient artist filtering
    op.create_index(
        'idx_album_artist_album_artist',
        'album_artist',
        ['album_id', 'artist_id'],
        if_not_exists=True
    )


def downgrade() -> None:
    """Remove sorting indexes."""
    
    op.drop_index('idx_album_artist_album_artist', table_name='album_artist', if_exists=True)
    op.drop_index('idx_albums_created_title', table_name='albums', if_exists=True)
    op.drop_index('idx_artist_name_sort', table_name='artists', if_exists=True)
    op.drop_index('idx_albums_source_support', table_name='albums', if_exists=True)
    op.drop_index('idx_albums_year_title', table_name='albums', if_exists=True)
    op.drop_index('idx_albums_title_year', table_name='albums', if_exists=True)
