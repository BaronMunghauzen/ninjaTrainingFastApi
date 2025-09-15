"""fix_foreign_keys_user_measurements

Revision ID: d1d0db70a2a8
Revises: b053d472d7ab
Create Date: 2025-09-13 22:28:38.448683

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1d0db70a2a8'
down_revision: Union[str, Sequence[str], None] = 'b053d472d7ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Удаляем существующие внешние ключи
    op.drop_constraint('user_measurement_types_user_id_fkey', 'user_measurement_types', type_='foreignkey')
    op.drop_constraint('user_measurements_user_id_fkey', 'user_measurements', type_='foreignkey')
    op.drop_constraint('user_measurements_measurement_type_id_fkey', 'user_measurements', type_='foreignkey')
    
    # Создаем правильные внешние ключи
    op.create_foreign_key('user_measurement_types_user_id_fkey', 'user_measurement_types', 'user', ['user_id'], ['id'])
    op.create_foreign_key('user_measurements_user_id_fkey', 'user_measurements', 'user', ['user_id'], ['id'])
    op.create_foreign_key('user_measurements_measurement_type_id_fkey', 'user_measurements', 'user_measurement_types', ['measurement_type_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем исправленные внешние ключи
    op.drop_constraint('user_measurements_measurement_type_id_fkey', 'user_measurements', type_='foreignkey')
    op.drop_constraint('user_measurements_user_id_fkey', 'user_measurements', type_='foreignkey')
    op.drop_constraint('user_measurement_types_user_id_fkey', 'user_measurement_types', type_='foreignkey')
    
    # Восстанавливаем старые внешние ключи (если нужно)
    # op.create_foreign_key('user_measurement_types_user_id_fkey', 'user_measurement_types', 'users', ['user_id'], ['id'])
    # op.create_foreign_key('user_measurements_user_id_fkey', 'user_measurements', 'users', ['user_id'], ['id'])
    # op.create_foreign_key('user_measurements_measurement_type_id_fkey', 'user_measurements', 'user_measurement_types', ['measurement_type_id'], ['id'])
