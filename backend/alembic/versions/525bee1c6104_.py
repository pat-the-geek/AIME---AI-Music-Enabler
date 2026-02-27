"""empty message

Revision ID: 525bee1c6104
Revises: 003_deprecated, 008_add_sorting_indexes
Create Date: 2026-02-27 07:40:05.822499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '525bee1c6104'
down_revision: Union[str, Sequence[str], None] = ('003_deprecated', '008_add_sorting_indexes')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
