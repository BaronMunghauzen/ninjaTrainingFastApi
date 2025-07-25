"""stage may be null in training

Revision ID: 3e33f2607c7a
Revises: 84dc237d2722
Create Date: 2025-07-24 00:06:41.244456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e33f2607c7a'
down_revision: Union[str, Sequence[str], None] = '84dc237d2722'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('training', 'stage',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('training', 'stage',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
