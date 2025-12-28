"""add_score_to_user

Revision ID: 2d5fecfbf157
Revises: 58c47d8a16f0
Create Date: 2025-12-26 19:55:26.101024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d5fecfbf157'
down_revision: Union[str, Sequence[str], None] = '58c47d8a16f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user', sa.Column('score', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user', 'score')
