"""Add service_states table for auto-restart.

Revision ID: 003_add_service_states
Revises: 002_fix_invalid_supports
Create Date: 2026-01-31 21:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = '003_add_service_states'
down_revision = '002_fix_invalid_supports'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create service_states table."""
    op.create_table(
        'service_states',
        sa.Column('service_name', sa.String(), nullable=False, primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create index on last_updated for potential queries
    op.create_index('idx_service_states_last_updated', 'service_states', ['last_updated'])


def downgrade() -> None:
    """Drop service_states table."""
    op.drop_index('idx_service_states_last_updated', table_name='service_states')
    op.drop_table('service_states')
