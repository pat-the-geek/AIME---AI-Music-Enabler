"""Add Apple Music URL column to albums table.

Revision ID: 007_add_apple_music_url
Revises: 006_add_desc_indexes
Create Date: 2026-02-14 10:00:00.000000

This migration adds the apple_music_url column to the albums table to store
Apple Music links for each album, similar to spotify_url.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_apple_music_url'
down_revision = '006_add_desc_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add apple_music_url column to albums table."""
    
    # Add apple_music_url column to albums table
    # Same structure as spotify_url: String(500), nullable, no unique constraint
    op.add_column(
        'albums',
        sa.Column('apple_music_url', sa.String(500), nullable=True)
    )
    
    # Create index for quick lookups
    op.create_index(
        'idx_albums_apple_music_url',
        'albums',
        ['apple_music_url'],
        if_not_exists=True
    )


def downgrade() -> None:
    """Remove apple_music_url column and index."""
    
    # Drop index first
    op.drop_index('idx_albums_apple_music_url', table_name='albums', if_exists=True)
    
    # Drop column
    op.drop_column('albums', 'apple_music_url')
