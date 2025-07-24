"""add exercise_reference model

Revision ID: aa876a34f6e3
Revises: 7b95baeff19a
Create Date: 2025-07-23 22:37:43.265536

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa876a34f6e3'
down_revision: Union[str, Sequence[str], None] = '7b95baeff19a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
