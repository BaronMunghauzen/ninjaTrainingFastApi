"""make_muscle_group_nullable_in_training

Revision ID: f8efc015059c
Revises: 5e8f808e2025
Create Date: 2026-01-14 22:02:08.116454

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8efc015059c'
down_revision: Union[str, Sequence[str], None] = '5e8f808e2025'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
