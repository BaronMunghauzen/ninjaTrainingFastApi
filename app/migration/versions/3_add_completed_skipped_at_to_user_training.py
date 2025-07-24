"""add completed_at, skipped_at to user_training

Revision ID: b2c3d4e5f6a7
Revises: 2_add_schedule_fields_to_program
Create Date: 2024-07-11 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = '2_add_schedule_fields_to_program'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('user_training', sa.Column('completed_at', sa.DateTime(), nullable=True))
    op.add_column('user_training', sa.Column('skipped_at', sa.DateTime(), nullable=True))

def downgrade() -> None:
    op.drop_column('user_training', 'skipped_at')
    op.drop_column('user_training', 'completed_at') 