"""add schedule_type, training_days to program

Revision ID: 2_add_schedule_fields_to_program
Revises: a1b2c3d4e5f6
Create Date: 2024-07-11 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2_add_schedule_fields_to_program'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('program', sa.Column('schedule_type', sa.String(), nullable=True, server_default='weekly'))
    op.add_column('program', sa.Column('training_days', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('program', 'training_days')
    op.drop_column('program', 'schedule_type') 