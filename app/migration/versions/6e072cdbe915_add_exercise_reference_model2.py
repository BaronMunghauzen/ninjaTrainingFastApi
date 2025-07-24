"""add exercise_reference model2

Revision ID: 6e072cdbe915
Revises: aa876a34f6e3
Create Date: 2025-07-23 22:39:24.974015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e072cdbe915'
down_revision: Union[str, Sequence[str], None] = 'aa876a34f6e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
