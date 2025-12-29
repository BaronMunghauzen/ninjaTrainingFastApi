"""add_achievement_type_id_to_achievements_table

Revision ID: a0b28d3ceffa
Revises: d4fec2bd0095
Create Date: 2025-12-28 18:09:57.472809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0b28d3ceffa'
down_revision: Union[str, Sequence[str], None] = 'd4fec2bd0095'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
