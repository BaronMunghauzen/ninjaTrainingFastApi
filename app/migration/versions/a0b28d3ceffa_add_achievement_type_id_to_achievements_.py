"""add_achievement_type_id_to_achievements_table

Revision ID: a0b28d3ceffa
Revises: d4fec2bd0095
Create Date: 2025-12-28 18:09:57.472809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0b28d3ceffa'
down_revision: Union[str, Sequence[str], None] = 'd4fec2bd0095'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляет колонку achievement_type_id в таблицу achievements"""
    # Получаем подключение для проверки существования колонки
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Проверяем существование таблицы achievements
    if 'achievements' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('achievements')]
        if 'achievement_type_id' not in columns:
            # Добавляем поле achievement_type_id в таблицу achievements
            op.add_column('achievements', sa.Column('achievement_type_id', sa.Integer(), nullable=True))
            
            # Создаем внешний ключ
            op.create_foreign_key(
                'fk_achievements_achievement_type_id', 
                'achievements', 
                'achievement_types', 
                ['achievement_type_id'], 
                ['id']
            )


def downgrade() -> None:
    """Удаляет колонку achievement_type_id из таблицы achievements"""
    # Получаем подключение для проверки существования колонки
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Проверяем существование таблицы achievements
    if 'achievements' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('achievements')]
        if 'achievement_type_id' in columns:
            # Удаляем внешний ключ
            op.drop_constraint('fk_achievements_achievement_type_id', 'achievements', type_='foreignkey')
            
            # Удаляем поле achievement_type_id
            op.drop_column('achievements', 'achievement_type_id')
