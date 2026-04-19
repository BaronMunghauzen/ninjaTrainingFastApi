"""
Импорт записей exercise_builder_equipment из CSV.
Выполнять после импорта exercise_builder_pool.
exercise_builder_id в CSV — порядковый номер строки пула (1-based). Сопоставляем с реальными id в БД по порядку.
"""
import csv
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from app.database import async_session_maker
from app.exercise_builder_equipment.models import ExerciseBuilderEquipment
from app.exercise_builder_pool.models import ExerciseBuilderPool


def _str(v):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    return str(v).strip()


def _int(v):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


async def import_from_csv(file_path: str | Path) -> int:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    count = 0
    async with async_session_maker() as session:
        # Список id exercise_builder_pool по возрастанию (порядок вставки = порядок в CSV пула)
        pool_ids_result = await session.execute(
            select(ExerciseBuilderPool.id).order_by(ExerciseBuilderPool.id)
        )
        pool_ids_ordered = [r[0] for r in pool_ids_result.all()]
        csv_index_to_pool_id = {}
        for i, pid in enumerate(pool_ids_ordered):
            csv_index_to_pool_id[i + 1] = pid  # 1-based index как в CSV

        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_builder_id = _int(row.get("exercise_builder_id"))
                real_pool_id = csv_index_to_pool_id.get(csv_builder_id) if csv_builder_id else None
                if real_pool_id is None:
                    continue
                eq = ExerciseBuilderEquipment(
                    uuid=uuid4(),
                    actual=True,
                    exercise_builder_id=real_pool_id,
                    equipment_code=_str(row.get("equipment_code")),
                    exercise_caption=_str(row.get("exercise_caption")),
                )
                session.add(eq)
                count += 1
        await session.commit()
    return count
