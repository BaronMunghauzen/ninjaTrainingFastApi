"""
Импорт правил состава тренировок из CSV.
Файл: training_composition_rules_import.csv (разместить в проекте или указать путь).
"""
import csv
from pathlib import Path
from uuid import uuid4
from app.database import async_session_maker
from app.training_composition_rules.models import TrainingCompositionRule


def _int(v):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _bool(v):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "да"):
        return True
    if s in ("0", "false", "no", "нет"):
        return False
    return None


async def import_from_csv(file_path: str | Path) -> int:
    """Импорт из CSV. Колонка training_composition_rule_id пропускается."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    count = 0
    async with async_session_maker() as session:
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rule = TrainingCompositionRule(
                    uuid=uuid4(),
                    actual=_bool(row.get("actual")) if row.get("actual") else True,
                    training_type=row.get("training_type") or None,
                    program_goal=row.get("program_goal") or None,
                    program_week_index=_int(row.get("program_week_index")),
                    duration_target_minutes=_int(row.get("duration_target_minutes")),
                    location_scope=row.get("location_scope") or None,
                    anchor_slots_count=_int(row.get("anchor_slots_count")),
                    main_slots_count=_int(row.get("main_slots_count")),
                    accessory_slots_count=_int(row.get("accessory_slots_count")),
                    core_slots_count=_int(row.get("core_slots_count")),
                    mobility_slots_count=_int(row.get("mobility_slots_count")),
                    allow_second_anchor=_bool(row.get("allow_second_anchor")),
                    anchor_sets=_int(row.get("anchor_sets")),
                    anchor_reps_min=_int(row.get("anchor_reps_min")),
                    anchor_reps_max=_int(row.get("anchor_reps_max")),
                    anchor_rest_seconds=_int(row.get("anchor_rest_seconds")),
                    main_sets=_int(row.get("main_sets")),
                    main_reps_min=_int(row.get("main_reps_min")),
                    main_reps_max=_int(row.get("main_reps_max")),
                    main_rest_seconds=_int(row.get("main_rest_seconds")),
                    accessory_sets=_int(row.get("accessory_sets")),
                    accessory_reps_min=_int(row.get("accessory_reps_min")),
                    accessory_reps_max=_int(row.get("accessory_reps_max")),
                    accessory_rest_seconds=_int(row.get("accessory_rest_seconds")),
                    core_sets=_int(row.get("core_sets")),
                    core_reps_min=_int(row.get("core_reps_min")),
                    core_reps_max=_int(row.get("core_reps_max")),
                    core_rest_seconds=_int(row.get("core_rest_seconds")),
                    mobility_sets=_int(row.get("mobility_sets")),
                    mobility_reps_min=_int(row.get("mobility_reps_min")),
                    mobility_reps_max=_int(row.get("mobility_reps_max")),
                    mobility_rest_seconds=_int(row.get("mobility_rest_seconds")),
                    notes_ru=row.get("notes_ru") or None,
                )
                session.add(rule)
                count += 1
        await session.commit()
    return count
