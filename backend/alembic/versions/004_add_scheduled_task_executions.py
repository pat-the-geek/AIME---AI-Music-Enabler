"""Add scheduled_task_executions table for scheduler persistence.

Revision ID: 004_add_scheduled_task_executions
Revises: 003_add_service_states
Create Date: 2026-02-06 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_add_scheduled_task_executions'
down_revision = '003_add_service_states'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create scheduled_task_executions table."""
    op.create_table(
        'scheduled_task_executions',
        sa.Column('task_id', sa.String(), nullable=False, primary_key=True),
        sa.Column('task_name', sa.String(), nullable=False),
        sa.Column('last_executed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('next_run_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create indices for common queries
    op.create_index('idx_scheduled_task_executions_task_id', 'scheduled_task_executions', ['task_id'])
    op.create_index('idx_scheduled_task_executions_last_executed', 'scheduled_task_executions', ['last_executed'])
    op.create_index('idx_scheduled_task_executions_last_status', 'scheduled_task_executions', ['last_status'])


def downgrade() -> None:
    """Drop scheduled_task_executions table."""
    op.drop_index('idx_scheduled_task_executions_last_status', table_name='scheduled_task_executions')
    op.drop_index('idx_scheduled_task_executions_last_executed', table_name='scheduled_task_executions')
    op.drop_index('idx_scheduled_task_executions_task_id', table_name='scheduled_task_executions')
    op.drop_table('scheduled_task_executions')
