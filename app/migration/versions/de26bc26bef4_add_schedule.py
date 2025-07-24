"""add schedule

Revision ID: de26bc26bef4
Revises: ee65bef79b49
Create Date: 2025-07-11 10:12:56.521106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de26bc26bef4'
down_revision: Union[str, Sequence[str], None] = 'ee65bef79b49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
