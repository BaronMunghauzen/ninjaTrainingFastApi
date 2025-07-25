"""add tumpnaul_id to the table

Revision ID: 6095bd8218d7
Revises: 2aef130fee19
Create Date: 2025-07-19 17:51:24.321872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6095bd8218d7'
down_revision: Union[str, Sequence[str], None] = '2aef130fee19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('exercise', sa.Column('video_preview_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'exercise', 'files', ['video_preview_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'exercise', type_='foreignkey')
    op.drop_column('exercise', 'video_preview_id')
    # ### end Alembic commands ###
