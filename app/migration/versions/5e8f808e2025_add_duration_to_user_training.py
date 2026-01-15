"""add_duration_to_user_training

Revision ID: 5e8f808e2025
Revises: 888f283b245f
Create Date: 2026-01-12 18:17:16.974594

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e8f808e2025'
down_revision: Union[str, Sequence[str], None] = '888f283b245f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Добавляем колонку duration в таблицу user_training
    op.add_column('user_training', sa.Column('duration', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем колонку duration из таблицы user_training
    op.drop_column('user_training', 'duration')
