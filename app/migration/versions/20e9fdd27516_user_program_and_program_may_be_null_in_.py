"""user_program and program may be null in tables

Revision ID: 20e9fdd27516
Revises: 430f140b71da
Create Date: 2025-07-22 21:31:39.331278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20e9fdd27516'
down_revision: Union[str, Sequence[str], None] = '430f140b71da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
