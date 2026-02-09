"""Add descending indexes for listening history queries.

Revision ID: 006_add_desc_indexes
Revises: 005_optimize_indexes
Create Date: 2026-02-09 15:00:00.000000

This migration adds descending indexes on listening_history.timestamp to optimize
the Journal display which sorts by most recent first (ORDER BY timestamp DESC).
Without these indexes, queries need to sort in-memory, causing slow pagination.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_add_desc_indexes'
down_revision = '005_optimize_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add descending indexes for listening history timestamp queries."""
    
    # ====================================
    # LISTENING HISTORY TABLE INDEXES
    # ====================================
    # Primary index: timestamp DESC for Journal sorting (most recent first)
    # This allows efficient ORDER BY timestamp DESC without in-memory sorting
    op.create_index(
        'idx_history_timestamp_desc',
        'listening_history',
        [sa.text('timestamp DESC')],
        if_not_exists=True
    )
    
    # Composite index: timestamp DESC with source for filtered queries
    # Optimizes: WHERE source = X ORDER BY timestamp DESC (common in analytics)
    op.create_index(
        'idx_history_timestamp_source_desc',
        'listening_history',
        [sa.text('timestamp DESC'), 'source'],
        if_not_exists=True
    )
    
    # Composite index: timestamp DESC with loved filter
    # Optimizes: WHERE loved = true/false ORDER BY timestamp DESC
    op.create_index(
        'idx_history_timestamp_loved_desc',
        'listening_history',
        [sa.text('timestamp DESC'), 'loved'],
        if_not_exists=True
    )


def downgrade() -> None:
    """Remove descending indexes."""
    
    op.drop_index('idx_history_timestamp_loved_desc', table_name='listening_history', if_exists=True)
    op.drop_index('idx_history_timestamp_source_desc', table_name='listening_history', if_exists=True)
    op.drop_index('idx_history_timestamp_desc', table_name='listening_history', if_exists=True)
