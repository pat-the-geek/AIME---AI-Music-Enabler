"""Add source column to albums table.

Revision ID: 001_add_source_column
Revises: 
Create Date: 2026-01-31 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_source_column'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add source column to albums table."""
    # Add new column with default value
    op.add_column('albums', sa.Column('source', sa.String(20), nullable=False, server_default='manual'))
    
    # Update existing albums:
    # - Albums with discogs_id are from Discogs
    # - Albums with support="Roon" are from Roon
    # - Others are assumed to be from various sources but no clear origin
    op.execute("""
        UPDATE albums 
        SET source = 'discogs' 
        WHERE discogs_id IS NOT NULL
    """)
    
    op.execute("""
        UPDATE albums 
        SET source = 'roon' 
        WHERE support = 'Roon'
    """)
    
    # Create index on source column for better query performance
    op.create_index('idx_albums_source', 'albums', ['source'])


def downgrade() -> None:
    """Remove source column from albums table."""
    op.drop_index('idx_albums_source', table_name='albums')
    op.drop_column('albums', 'source')
