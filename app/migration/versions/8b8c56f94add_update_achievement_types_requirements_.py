"""update_achievement_types_requirements_to_mm_dd_format

Revision ID: 8b8c56f94add
Revises: 978a3dc7089c
Create Date: 2025-12-26 20:22:32.779032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '8b8c56f94add'
down_revision: Union[str, Sequence[str], None] = '978a3dc7089c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Обновляет формат requirements для special_day достижений с YYYY-MM-DD на MM-DD"""
    connection = op.get_bind()
    
    # Маппинг старых дат (YYYY-MM-DD) на новые (MM-DD) для special_day достижений
    date_mapping = {
        "2025-01-01": "01-01",  # Новогодний старт
        "2025-01-07": "01-07",  # Рождественская сила
        "2025-02-14": "02-14",  # День Святого Валентина
        "2025-03-08": "03-08",  # 8 марта
        "2025-03-01": "03-01",  # Весенний подъём
        "2025-05-01": "05-01",  # День труда
        "2025-06-12": "06-12",  # День России
        "2025-09-01": "09-01",  # День знаний
        "2025-09-22": "09-22",  # Осенний старт
        "2025-10-31": "10-31",  # Хэллоуин-памп
        "2025-11-25": "11-25",  # День благодарности телу
        "2025-12-01": "12-01",  # Зимний заряд
        "2025-06-01": "06-01",  # Летний старт
        "2025-12-31": "12-31",  # Праздничная энергия
        "2025-06-15": "06-15",  # День отца
        "2025-05-26": "05-26",  # День матери
        "2025-04-07": "04-07",  # День здоровья
        "2025-05-09": "05-09",  # День победы силы
        "2025-06-21": "06-21",  # День лета
    }
    
    # Обновляем каждую дату
    for old_date, new_date in date_mapping.items():
        connection.execute(
            text("""
                UPDATE achievement_types 
                SET requirements = :new_date, updated_at = NOW()
                WHERE category = 'special_day' 
                AND requirements = :old_date
            """),
            {"old_date": old_date, "new_date": new_date}
        )


def downgrade() -> None:
    """Откатывает формат requirements для special_day достижений с MM-DD на YYYY-MM-DD"""
    connection = op.get_bind()
    
    # Обратный маппинг (MM-DD -> YYYY-MM-DD)
    # Используем 2025 как год по умолчанию для отката
    date_mapping = {
        "01-01": "2025-01-01",
        "01-07": "2025-01-07",
        "02-14": "2025-02-14",
        "03-08": "2025-03-08",
        "03-01": "2025-03-01",
        "05-01": "2025-05-01",
        "06-12": "2025-06-12",
        "09-01": "2025-09-01",
        "09-22": "2025-09-22",
        "10-31": "2025-10-31",
        "11-25": "2025-11-25",
        "12-01": "2025-12-01",
        "06-01": "2025-06-01",
        "12-31": "2025-12-31",
        "06-15": "2025-06-15",
        "05-26": "2025-05-26",
        "04-07": "2025-04-07",
        "05-09": "2025-05-09",
        "06-21": "2025-06-21",
    }
    
    # Обновляем каждую дату
    for new_date, old_date in date_mapping.items():
        connection.execute(
            text("""
                UPDATE achievement_types 
                SET requirements = :old_date, updated_at = NOW()
                WHERE category = 'special_day' 
                AND requirements = :new_date
            """),
            {"old_date": old_date, "new_date": new_date}
        )
