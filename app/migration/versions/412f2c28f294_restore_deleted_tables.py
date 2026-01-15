"""restore deleted tables

Revision ID: 412f2c28f294
Revises: 1f51a7081696
Create Date: 2026-01-08 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '412f2c28f294'
down_revision: Union[str, Sequence[str], None] = '1f51a7081696'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Восстанавливаем удаленные таблицы, если они были удалены
    # Проверяем существование таблиц перед созданием
    
    # Восстанавливаем food_recognition
    op.execute("""
        CREATE TABLE IF NOT EXISTS food_recognition (
            id SERIAL PRIMARY KEY,
            uuid UUID NOT NULL UNIQUE,
            actual BOOLEAN NOT NULL DEFAULT true,
            image_id INTEGER REFERENCES files(id),
            user_id INTEGER NOT NULL REFERENCES "user"(id),
            comment TEXT,
            json_response TEXT,
            name VARCHAR,
            confidence DOUBLE PRECISION,
            calories_per_100g DOUBLE PRECISION,
            proteins_per_100g DOUBLE PRECISION,
            fats_per_100g DOUBLE PRECISION,
            carbs_per_100g DOUBLE PRECISION,
            weight_g DOUBLE PRECISION,
            volume_ml DOUBLE PRECISION,
            estimated_portion_size VARCHAR,
            calories_total DOUBLE PRECISION,
            proteins_total DOUBLE PRECISION,
            fats_total DOUBLE PRECISION,
            carbs_total DOUBLE PRECISION,
            ingredients TEXT,
            recommendations_tip TEXT,
            recommendations_alternative TEXT,
            micronutrients TEXT,
            message TEXT,
            processing_time_seconds DOUBLE PRECISION,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_food_recognition_uuid ON food_recognition (uuid)")
    
    # Восстанавливаем meal_plans
    op.execute("""
        CREATE TABLE IF NOT EXISTS meal_plans (
            id SERIAL PRIMARY KEY,
            uuid UUID NOT NULL UNIQUE,
            actual BOOLEAN NOT NULL DEFAULT true,
            user_id INTEGER NOT NULL REFERENCES "user"(id),
            meals_per_day INTEGER NOT NULL,
            days_count INTEGER NOT NULL,
            max_repeats_per_week INTEGER,
            allowed_recipe_uuids TEXT,
            include_soup_in_lunch BOOLEAN NOT NULL DEFAULT true,
            target_calories DOUBLE PRECISION NOT NULL,
            target_proteins DOUBLE PRECISION NOT NULL,
            target_fats DOUBLE PRECISION NOT NULL,
            target_carbs DOUBLE PRECISION NOT NULL,
            plan_data TEXT NOT NULL,
            recommendations TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_meal_plans_uuid ON meal_plans (uuid)")
    
    # Восстанавливаем meals
    op.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id SERIAL PRIMARY KEY,
            uuid UUID NOT NULL UNIQUE,
            actual BOOLEAN NOT NULL DEFAULT true,
            user_id INTEGER NOT NULL REFERENCES "user"(id),
            meal_datetime TIMESTAMP NOT NULL,
            calories DOUBLE PRECISION NOT NULL,
            proteins DOUBLE PRECISION NOT NULL,
            fats DOUBLE PRECISION NOT NULL,
            carbs DOUBLE PRECISION NOT NULL,
            target_calories DOUBLE PRECISION NOT NULL,
            target_proteins DOUBLE PRECISION NOT NULL,
            target_fats DOUBLE PRECISION NOT NULL,
            target_carbs DOUBLE PRECISION NOT NULL,
            remaining_calories DOUBLE PRECISION NOT NULL,
            remaining_proteins DOUBLE PRECISION NOT NULL,
            remaining_fats DOUBLE PRECISION NOT NULL,
            remaining_carbs DOUBLE PRECISION NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_meals_uuid ON meals (uuid)")
    
    # Восстанавливаем calorie_calculations
    # Сначала создаем ENUM типы, если их нет
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE goalenum AS ENUM ('weight_loss', 'muscle_gain', 'maintenance');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE genderenum AS ENUM ('male', 'female');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS calorie_calculations (
            id SERIAL PRIMARY KEY,
            uuid UUID NOT NULL UNIQUE,
            actual BOOLEAN NOT NULL DEFAULT true,
            user_id INTEGER NOT NULL REFERENCES "user"(id),
            goal goalenum NOT NULL,
            gender genderenum NOT NULL,
            weight DOUBLE PRECISION NOT NULL,
            height DOUBLE PRECISION NOT NULL,
            age INTEGER NOT NULL,
            activity_coefficient VARCHAR NOT NULL,
            bmr DOUBLE PRECISION NOT NULL,
            tdee DOUBLE PRECISION NOT NULL,
            calories_for_weight_loss TEXT,
            calories_for_gain TEXT,
            calories_for_maintenance TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_calorie_calculations_uuid ON calorie_calculations (uuid)")
    
    # Восстанавливаем last_values
    op.execute("""
        CREATE TABLE IF NOT EXISTS last_values (
            id SERIAL PRIMARY KEY,
            uuid UUID NOT NULL UNIQUE,
            user_id INTEGER NOT NULL REFERENCES "user"(id),
            name VARCHAR NOT NULL,
            code VARCHAR NOT NULL,
            value TEXT NOT NULL,
            actual BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            UNIQUE(user_id, code)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_last_values_uuid ON last_values (uuid)")
    
    # Восстанавливаем daily_targets
    op.execute("""
        CREATE TABLE IF NOT EXISTS daily_targets (
            id SERIAL PRIMARY KEY,
            uuid UUID NOT NULL UNIQUE,
            actual BOOLEAN NOT NULL DEFAULT true,
            user_id INTEGER NOT NULL REFERENCES "user"(id),
            target_calories DOUBLE PRECISION NOT NULL,
            target_proteins DOUBLE PRECISION NOT NULL,
            target_fats DOUBLE PRECISION NOT NULL,
            target_carbs DOUBLE PRECISION NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_daily_targets_uuid ON daily_targets (uuid)")


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем восстановленные таблицы
    op.drop_index('ix_daily_targets_uuid', table_name='daily_targets')
    op.drop_table('daily_targets')
    op.drop_index('ix_last_values_uuid', table_name='last_values')
    op.drop_table('last_values')
    op.drop_index('ix_calorie_calculations_uuid', table_name='calorie_calculations')
    op.drop_table('calorie_calculations')
    op.drop_index('ix_meals_uuid', table_name='meals')
    op.drop_table('meals')
    op.drop_index('ix_meal_plans_uuid', table_name='meal_plans')
    op.drop_table('meal_plans')
    op.drop_index('ix_food_recognition_uuid', table_name='food_recognition')
    op.drop_table('food_recognition')
