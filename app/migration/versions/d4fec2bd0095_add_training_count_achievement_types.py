"""add_training_count_achievement_types

Revision ID: d4fec2bd0095
Revises: 8b8c56f94add
Create Date: 2025-12-26 20:37:18.583105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd4fec2bd0095'
down_revision: Union[str, Sequence[str], None] = '8b8c56f94add'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляет новые типы достижений категории training_count"""
    connection = op.get_bind()
    
    # Данные для вставки
    achievement_types_data = [
        # training_count achievements
        ("Первый шаг", "Заверши свою первую тренировку", "training_count", None, "1", None, 1, True),
        ("Сила привычки", "5 завершённых тренировок", "training_count", None, "5", None, 5, True),
        ("Десятка", "10 успешных тренировок", "training_count", None, "10", None, 10, True),
        ("Стальной настрой", "25 завершённых тренировок", "training_count", None, "25", None, 25, True),
        ("Полсотни", "50 тренировок — сила в постоянстве", "training_count", None, "50", None, 50, True),
        ("Сотня!", "100 завершённых тренировок", "training_count", None, "100", None, 100, True),
        ("Титан", "200 тренировок — почти легенда", "training_count", None, "200", None, 200, True),
        ("Железный человек", "300 тренировок", "training_count", None, "300", None, 300, True),
    ]
    
    # Вставляем данные
    for name, description, category, subcategory, requirements, icon, points, is_active in achievement_types_data:
        # Проверяем, существует ли уже запись с таким именем
        check_result = connection.execute(
            text("SELECT id FROM achievement_types WHERE name = :name"),
            {"name": name}
        )
        existing = check_result.fetchone()
        
        if not existing:
            connection.execute(
                text("""
                    INSERT INTO achievement_types (uuid, name, description, category, subcategory, requirements, icon, points, is_active, created_at, updated_at)
                    VALUES (gen_random_uuid(), :name, :description, :category, :subcategory, :requirements, :icon, :points, :is_active, NOW(), NOW())
                """),
                {
                    "name": name,
                    "description": description,
                    "category": category,
                    "subcategory": subcategory,
                    "requirements": requirements,
                    "icon": icon,
                    "points": points,
                    "is_active": is_active
                }
            )


def downgrade() -> None:
    """Удаляет добавленные типы достижений категории training_count"""
    connection = op.get_bind()
    
    # Удаляем все вставленные записи
    names_to_delete = [
        "Первый шаг",
        "Сила привычки",
        "Десятка",
        "Стальной настрой",
        "Полсотни",
        "Сотня!",
        "Титан",
        "Железный человек"
    ]
    
    for name in names_to_delete:
        connection.execute(
            text("DELETE FROM achievement_types WHERE name = :name"),
            {"name": name}
        )
