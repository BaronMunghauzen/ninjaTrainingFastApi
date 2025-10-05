"""add_achievement_type_id_to_achievements

Revision ID: add_achievement_type_id
Revises: 3f32087843a6
Create Date: 2025-08-18 21:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_achievement_type_id'
down_revision: Union[str, Sequence[str], None] = '3f32087843a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Получаем подключение для проверки существования таблиц
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Проверяем существование таблицы achievement_types
    if 'achievement_types' not in inspector.get_table_names():
        # Создаем таблицу achievement_types
        op.create_table('achievement_types',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=False),
            sa.Column('category', sa.String(), nullable=False),
            sa.Column('subcategory', sa.String(), nullable=True),
            sa.Column('requirements', sa.String(), nullable=True),
            sa.Column('icon', sa.String(), nullable=True),
            sa.Column('points', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('uuid')
        )
    
    # Проверяем существование таблицы achievements
    if 'achievements' not in inspector.get_table_names():
        # Создаем таблицу achievements
        op.create_table('achievements',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(), nullable=False),
            sa.Column('user_training_id', sa.Integer(), nullable=True),
            sa.Column('user_program_id', sa.Integer(), nullable=True),
            sa.Column('program_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('uuid'),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.ForeignKeyConstraint(['user_training_id'], ['user_training.id'], ),
            sa.ForeignKeyConstraint(['user_program_id'], ['user_program.id'], ),
            sa.ForeignKeyConstraint(['program_id'], ['program.id'], )
        )
    
    # Проверяем существование колонки achievement_type_id в таблице achievements
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
    """Downgrade schema."""
    # Получаем подключение для проверки существования таблиц
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Проверяем существование таблицы achievements
    if 'achievements' in inspector.get_table_names():
        # Проверяем существование колонки achievement_type_id
        columns = [col['name'] for col in inspector.get_columns('achievements')]
        if 'achievement_type_id' in columns:
            # Удаляем внешний ключ
            op.drop_constraint('fk_achievements_achievement_type_id', 'achievements', type_='foreignkey')
            
            # Удаляем поле achievement_type_id
            op.drop_column('achievements', 'achievement_type_id')
        
        # Удаляем таблицу achievements только если она была создана этой миграцией
        # (это сложно определить, поэтому оставляем таблицу)
        # op.drop_table('achievements')
    
    # Удаляем таблицу achievement_types только если она была создана этой миграцией
    # (это сложно определить, поэтому оставляем таблицу)
    # if 'achievement_types' in inspector.get_table_names():
    #     op.drop_table('achievement_types')
