"""Fix invalid supports for Discogs collection albums.

Revision ID: 002_fix_invalid_supports
Revises: 001_add_source_column
Create Date: 2026-01-31 12:05:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_fix_invalid_supports'
down_revision = '001_add_source_column'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix invalid supports for Discogs collection albums."""
    # Move albums with invalid support (not Vinyle, CD, Digital) from Discogs to their listening source
    # These are albums that came from listening history but were mistakenly added to collection
    
    # Albums with support="Roon" that were marked as discogs - move to roon source
    op.execute("""
        UPDATE albums 
        SET source = 'roon', support = 'Roon'
        WHERE source = 'discogs' AND support = 'Roon'
    """)
    
    # Albums with other invalid supports from Discogs - move to manual source
    # (we can't determine their real source, so mark as manual for manual review)
    op.execute("""
        UPDATE albums 
        SET source = 'manual'
        WHERE source = 'discogs' 
        AND support IS NOT NULL
        AND support NOT IN ('Vinyle', 'Vinyl', 'CD', 'Digital', 'Cassette')
    """)
    
    # Ensure Discogs albums have valid supports
    # If a Discogs album has an invalid support, clear it
    op.execute("""
        UPDATE albums 
        SET support = NULL
        WHERE source = 'discogs'
        AND support IS NOT NULL
        AND support NOT IN ('Vinyle', 'Vinyl', 'CD', 'Digital', 'Cassette')
    """)


def downgrade() -> None:
    """No downgrade needed."""
    pass
