"""add_indexes_for_performance

Revision ID: 430f140b71da
Revises: f961f7c58c7c
Create Date: 2025-07-20 11:38:12.086319

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '430f140b71da'
down_revision: Union[str, Sequence[str], None] = 'f961f7c58c7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Индексы для таблицы user_training для ускорения запросов
    op.create_index('ix_user_training_user_program_id', 'user_training', ['user_program_id'])
    op.create_index('ix_user_training_user_id', 'user_training', ['user_id'])
    op.create_index('ix_user_training_program_id', 'user_training', ['program_id'])
    op.create_index('ix_user_training_training_id', 'user_training', ['training_id'])
    op.create_index('ix_user_training_status', 'user_training', ['status'])
    op.create_index('ix_user_training_training_date', 'user_training', ['training_date'])
    op.create_index('ix_user_training_stage', 'user_training', ['stage'])
    
    # Составной индекс для частых запросов по user_program_id и status
    op.create_index('ix_user_training_user_program_status', 'user_training', ['user_program_id', 'status'])
    
    # Составной индекс для запросов по user_program_id и training_date
    op.create_index('ix_user_training_user_program_date', 'user_training', ['user_program_id', 'training_date'])


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем созданные индексы
    op.drop_index('ix_user_training_user_program_date', 'user_training')
    op.drop_index('ix_user_training_user_program_status', 'user_training')
    op.drop_index('ix_user_training_stage', 'user_training')
    op.drop_index('ix_user_training_training_date', 'user_training')
    op.drop_index('ix_user_training_status', 'user_training')
    op.drop_index('ix_user_training_training_id', 'user_training')
    op.drop_index('ix_user_training_program_id', 'user_training')
    op.drop_index('ix_user_training_user_id', 'user_training')
    op.drop_index('ix_user_training_user_program_id', 'user_training')
