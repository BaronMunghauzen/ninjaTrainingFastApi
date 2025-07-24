"""add user fields and enums

Revision ID: ee65bef79b49
Revises: 0e82396ee96a
Create Date: 2025-07-10 17:00:41.823721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee65bef79b49'
down_revision: Union[str, Sequence[str], None] = '0e82396ee96a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
