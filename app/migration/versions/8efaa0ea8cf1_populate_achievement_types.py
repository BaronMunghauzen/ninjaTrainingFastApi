"""populate_achievement_types

Revision ID: 8efaa0ea8cf1
Revises: 2d5fecfbf157
Create Date: 2025-12-26 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '8efaa0ea8cf1'
down_revision: Union[str, Sequence[str], None] = '2d5fecfbf157'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    
    # Данные для вставки
    # Для special_day используется формат MM-DD (месяц-день), чтобы достижения срабатывали каждый год
    achievement_types_data = [
        # special_day achievements (формат requirements: MM-DD)
        ("Новогодний старт", "Заверши тренировку в первый день года!", "special_day", None, "01-01", None, 5, True),
        ("Рождественская сила", "Проведи рождественскую тренировку!", "special_day", None, "01-07", None, 5, True),
        ("День Святого Валентина", "Позанимайся в День всех влюблённых!", "special_day", None, "02-14", None, 5, True),
        ("8 марта — сила и красота", "Заверши тренировку в Международный женский день", "special_day", None, "03-08", None, 5, True),
        ("Весенний подъём", "Начни весну с тренировки!", "special_day", None, "03-01", None, 5, True),
        ("День труда", "Заверши тренировку 1 мая — отличный способ отпраздновать труд!", "special_day", None, "05-01", None, 5, True),
        ("День России", "Празднуй активностью!", "special_day", None, "06-12", None, 5, True),
        ("День знаний", "Начни учебный год с энергии!", "special_day", None, "09-01", None, 5, True),
        ("Осенний старт", "Начни осень с движением!", "special_day", None, "09-22", None, 5, True),
        ("Хэллоуин-памп", "Тренируйся в ночь всех святых!", "special_day", None, "10-31", None, 5, True),
        ("День благодарности телу", "Поблагодари себя тренировкой!", "special_day", None, "11-25", None, 5, True),
        ("День рождения силы", "Заверши тренировку в свой день рождения!", "special_day", None, "user_birthday", None, 5, True),
        ("Зимний заряд", "Тренируйся в первый день зимы!", "special_day", None, "12-01", None, 5, True),
        ("Летний старт", "Начни лето с тренировки!", "special_day", None, "06-01", None, 5, True),
        ("Праздничная энергия", "Заверши тренировку в новогоднюю ночь!", "special_day", None, "12-31", None, 5, True),
        ("День отца", "Сделай совместную тренировку со своими близкими!", "special_day", None, "06-15", None, 5, True),
        ("День матери", "Подарок себе — тренировка!", "special_day", None, "05-26", None, 5, True),
        ("День здоровья", "Заверши тренировку в международный день здоровья!", "special_day", None, "04-07", None, 5, True),
        ("День победы силы", "Тренируйся 9 мая, отмечая силу духа!", "special_day", None, "05-09", None, 5, True),
        ("День лета", "Просто потренируйся в самый длинный день года!", "special_day", None, "06-21", None, 5, True),
        # training_count_in_week achievements
        ("Разгон недели", "2 тренировки за неделю", "training_count_in_week", None, "2", None, 5, True),
        ("Ритм недели", "3 тренировки за неделю", "training_count_in_week", None, "3", None, 5, True),
        ("Почти привычка", "4 тренировки за неделю", "training_count_in_week", None, "4", None, 10, True),
        ("Суперсерия", "5 тренировок за неделю", "training_count_in_week", None, "5", None, 10, True),
        ("Ниндзя недели", "6 тренировок за неделю", "training_count_in_week", None, "6", None, 15, True),
        ("Бессонная неделя", "7 тренировок за неделю — без выходных!", "training_count_in_week", None, "7", None, 20, True),
        ("Двойной удар", "10 тренировок за неделю (дважды в день!)", "training_count_in_week", None, "10", None, 25, True),
        # time_less_than achievements
        ("Ранняя пташка", "Заверши тренировку до 06:00 утра", "time_less_than", None, "06:00", None, 10, True),
        ("До рассвета", "Заверши тренировку до 05:00", "time_less_than", None, "05:00", None, 15, True),
        ("До будильника", "Заверши тренировку до времени, когда многие ещё спят — до 04:30", "time_less_than", None, "04:30", None, 25, True),
        ("Победа над подушкой", "Заверши тренировку до 06:30", "time_less_than", None, "06:30", None, 5, True),
        ("Опережая офис", "Закончить тренировку до 09:00, ещё до начала рабочего дня", "time_less_than", None, "09:00", None, 5, True),
        # time_more_than achievements
        ("Ночной воин", "Заверши тренировку после 22:00", "time_more_than", None, "22:00", None, 15, True),
        ("Поздний гринд", "Заверши тренировку после 21:00", "time_more_than", None, "21:00", None, 10, True),
        ("После всех дел", "Заверши тренировку позже 20:00", "time_more_than", None, "20:00", None, 5, True),
        ("Тренировка вместо сериала", "Закончить тренировку после 19:30", "time_more_than", None, "19:30", None, 5, True),
        ("До самого сна", "Заверши тренировку после 23:30", "time_more_than", None, "23:30", None, 25, True),
    ]
    
    # Вставляем данные
    for name, description, category, subcategory, requirements, icon, points, is_active in achievement_types_data:
        # Проверяем, существует ли уже запись с таким именем мит

        
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
    """Downgrade schema."""
    connection = op.get_bind()
    
    # Удаляем все вставленные записи
    names_to_delete = [
        "Новогодний старт", "Рождественская сила", "День Святого Валентина", "8 марта — сила и красота",
        "Весенний подъём", "День труда", "День России", "День знаний", "Осенний старт", "Хэллоуин-памп",
        "День благодарности телу", "День рождения силы", "Зимний заряд", "Летний старт", "Праздничная энергия",
        "День отца", "День матери", "День здоровья", "День победы силы", "День лета",
        "Разгон недели", "Ритм недели", "Почти привычка", "Суперсерия", "Ниндзя недели", "Бессонная неделя", "Двойной удар",
        "Ранняя пташка", "До рассвета", "До будильника", "Победа над подушкой", "Опережая офис",
        "Ночной воин", "Поздний гринд", "После всех дел", "Тренировка вместо сериала", "До самого сна"
    ]
    
    for name in names_to_delete:
        connection.execute(
            text("DELETE FROM achievement_types WHERE name = :name"),
            {"name": name}
        )
