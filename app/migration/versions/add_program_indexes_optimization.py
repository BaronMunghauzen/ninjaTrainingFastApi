"""add_program_indexes_optimization

Revision ID: add_program_indexes_opt
Revises: 58c47d8a16f0
Create Date: 2026-01-15 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_program_indexes_opt'
down_revision: Union[str, Sequence[str], None] = 'f8efc015059c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Индексы для ускорения JOIN'ов и фильтрации
    # PostgreSQL не создает индексы автоматически для Foreign Keys
    
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # === ИНДЕКСЫ ДЛЯ ТАБЛИЦЫ PROGRAM ===
    existing_indexes_program = [idx['name'] for idx in inspector.get_indexes('program')]
    
    if 'ix_program_category_id' not in existing_indexes_program:
        op.create_index('ix_program_category_id', 'program', ['category_id'], unique=False)
    
    if 'ix_program_user_id' not in existing_indexes_program:
        op.create_index('ix_program_user_id', 'program', ['user_id'], unique=False)
    
    if 'ix_program_image_id' not in existing_indexes_program:
        op.create_index('ix_program_image_id', 'program', ['image_id'], unique=False)
    
    if 'ix_program_type_actual' not in existing_indexes_program:
        op.create_index('ix_program_type_actual', 'program', ['program_type', 'actual'], unique=False)
    
    # === ИНДЕКСЫ ДЛЯ ТАБЛИЦЫ TRAINING ===
    existing_indexes_training = [idx['name'] for idx in inspector.get_indexes('training')]
    
    if 'ix_training_program_id' not in existing_indexes_training:
        op.create_index('ix_training_program_id', 'training', ['program_id'], unique=False)
    
    if 'ix_training_user_id' not in existing_indexes_training:
        op.create_index('ix_training_user_id', 'training', ['user_id'], unique=False)
    
    if 'ix_training_image_id' not in existing_indexes_training:
        op.create_index('ix_training_image_id', 'training', ['image_id'], unique=False)
    
    if 'ix_training_type_actual' not in existing_indexes_training:
        op.create_index('ix_training_type_actual', 'training', ['training_type', 'actual'], unique=False)
    
    # === ИНДЕКСЫ ДЛЯ ТАБЛИЦЫ EXERCISE ===
    existing_indexes_exercise = [idx['name'] for idx in inspector.get_indexes('exercise')]
    
    if 'ix_exercise_user_id' not in existing_indexes_exercise:
        op.create_index('ix_exercise_user_id', 'exercise', ['user_id'], unique=False)
    
    if 'ix_exercise_image_id' not in existing_indexes_exercise:
        op.create_index('ix_exercise_image_id', 'exercise', ['image_id'], unique=False)
    
    if 'ix_exercise_video_id' not in existing_indexes_exercise:
        op.create_index('ix_exercise_video_id', 'exercise', ['video_id'], unique=False)
    
    if 'ix_exercise_video_preview_id' not in existing_indexes_exercise:
        op.create_index('ix_exercise_video_preview_id', 'exercise', ['video_preview_id'], unique=False)
    
    if 'ix_exercise_reference_id' not in existing_indexes_exercise:
        op.create_index('ix_exercise_reference_id', 'exercise', ['exercise_reference_id'], unique=False)
    
    if 'ix_exercise_type' not in existing_indexes_exercise:
        op.create_index('ix_exercise_type', 'exercise', ['exercise_type'], unique=False)
    
    # === ИНДЕКСЫ ДЛЯ ТАБЛИЦЫ EXERCISE_REFERENCE ===
    existing_indexes_exercise_ref = [idx['name'] for idx in inspector.get_indexes('exercise_reference')]
    
    if 'ix_exercise_reference_user_id' not in existing_indexes_exercise_ref:
        op.create_index('ix_exercise_reference_user_id', 'exercise_reference', ['user_id'], unique=False)
    
    if 'ix_exercise_reference_image_id' not in existing_indexes_exercise_ref:
        op.create_index('ix_exercise_reference_image_id', 'exercise_reference', ['image_id'], unique=False)
    
    if 'ix_exercise_reference_video_id' not in existing_indexes_exercise_ref:
        op.create_index('ix_exercise_reference_video_id', 'exercise_reference', ['video_id'], unique=False)
    
    if 'ix_exercise_reference_gif_id' not in existing_indexes_exercise_ref:
        op.create_index('ix_exercise_reference_gif_id', 'exercise_reference', ['gif_id'], unique=False)
    
    if 'ix_exercise_reference_exercise_type' not in existing_indexes_exercise_ref:
        op.create_index('ix_exercise_reference_exercise_type', 'exercise_reference', ['exercise_type'], unique=False)
    
    # === ИНДЕКСЫ ДЛЯ ТАБЛИЦЫ USER_TRAINING ===
    # (Большинство индексов уже созданы в других миграциях, но добавим недостающие)
    existing_indexes_user_training = [idx['name'] for idx in inspector.get_indexes('user_training')]
    
    # Эти индексы должны быть, но проверим на всякий случай
    if 'ix_user_training_user_id' not in existing_indexes_user_training:
        op.create_index('ix_user_training_user_id', 'user_training', ['user_id'], unique=False)
    
    if 'ix_user_training_program_id' not in existing_indexes_user_training:
        op.create_index('ix_user_training_program_id', 'user_training', ['program_id'], unique=False)
    
    if 'ix_user_training_training_id' not in existing_indexes_user_training:
        op.create_index('ix_user_training_training_id', 'user_training', ['training_id'], unique=False)
    
    if 'ix_user_training_status' not in existing_indexes_user_training:
        op.create_index('ix_user_training_status', 'user_training', ['status'], unique=False)
    
    if 'ix_user_training_training_date' not in existing_indexes_user_training:
        op.create_index('ix_user_training_training_date', 'user_training', ['training_date'], unique=False)
    
    # === ИНДЕКСЫ ДЛЯ ТАБЛИЦЫ USER_EXERCISE ===
    existing_indexes_user_exercise = [idx['name'] for idx in inspector.get_indexes('user_exercise')]
    
    if 'ix_user_exercise_program_id' not in existing_indexes_user_exercise:
        op.create_index('ix_user_exercise_program_id', 'user_exercise', ['program_id'], unique=False)
    
    if 'ix_user_exercise_training_id' not in existing_indexes_user_exercise:
        op.create_index('ix_user_exercise_training_id', 'user_exercise', ['training_id'], unique=False)
    
    if 'ix_user_exercise_user_id' not in existing_indexes_user_exercise:
        op.create_index('ix_user_exercise_user_id', 'user_exercise', ['user_id'], unique=False)
    
    if 'ix_user_exercise_exercise_id' not in existing_indexes_user_exercise:
        op.create_index('ix_user_exercise_exercise_id', 'user_exercise', ['exercise_id'], unique=False)
    
    if 'ix_user_exercise_status' not in existing_indexes_user_exercise:
        op.create_index('ix_user_exercise_status', 'user_exercise', ['status'], unique=False)
    
    if 'ix_user_exercise_training_date' not in existing_indexes_user_exercise:
        op.create_index('ix_user_exercise_training_date', 'user_exercise', ['training_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Удаляем индексы для всех таблиц
    tables_to_check = [
        'program', 'training', 'exercise', 'exercise_reference', 
        'user_training', 'user_exercise'
    ]
    
    for table_name in tables_to_check:
        try:
            existing_indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
            # Удаляем только те индексы, которые мы создали
            index_prefix = f'ix_{table_name}_'
            for idx_name in existing_indexes:
                if idx_name.startswith(index_prefix) and idx_name not in [
                    # Оставляем UUID индексы и другие важные
                    f'ix_{table_name}_uuid'
                ]:
                    try:
                        op.drop_index(idx_name, table_name=table_name)
                    except:
                        pass  # Игнорируем ошибки, если индекс уже удален
        except:
            pass  # Игнорируем, если таблицы нет

