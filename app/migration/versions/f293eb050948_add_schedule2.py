"""add schedule2

Revision ID: f293eb050948
Revises: de26bc26bef4
Create Date: 2025-07-11 22:39:43.252329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f293eb050948'
down_revision: Union[str, Sequence[str], None] = 'de26bc26bef4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user_program', sa.Column('schedule_type', sa.String(), nullable=True))
    op.add_column('user_program', sa.Column('training_days', sa.String(), nullable=True))
    op.add_column('user_program', sa.Column('start_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user_program', 'start_date')
    op.drop_column('user_program', 'training_days')
    op.drop_column('user_program', 'schedule_type')
