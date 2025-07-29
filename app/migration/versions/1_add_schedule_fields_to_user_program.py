"""add schedule_type, training_days, start_date to user_program

Revision ID: a1b2c3d4e5f6
Revises: f293eb050948
Create Date: 2024-07-11 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f293eb050948'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Проверяем существование колонок перед добавлением
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('user_program')]
    
    if 'schedule_type' not in existing_columns:
        op.add_column('user_program', sa.Column('schedule_type', sa.String(), nullable=True))
    
    if 'training_days' not in existing_columns:
        op.add_column('user_program', sa.Column('training_days', sa.String(), nullable=True))
    
    if 'start_date' not in existing_columns:
        op.add_column('user_program', sa.Column('start_date', sa.Date(), nullable=True))

def downgrade() -> None:
    op.drop_column('user_program', 'start_date')
    op.drop_column('user_program', 'training_days')
    op.drop_column('user_program', 'schedule_type') 