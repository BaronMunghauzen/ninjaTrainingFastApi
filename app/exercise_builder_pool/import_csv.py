"""
Импорт записей exercise_builder_pool из CSV.
Важно: импорт выполнять в порядке строк CSV, чтобы id в БД совпадали с exercise_builder_id из CSV
(для последующего импорта exercise_builder_equipment).
exercise_id из CSV может не существовать в exercise_reference (другая БД) — тогда ищем по caption или ставим NULL.
"""
import csv
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from app.database import async_session_maker
from app.exercise_builder_pool.models import ExerciseBuilderPool
from app.exercise_reference.models import ExerciseReference


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


def _str(v):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    return str(v).strip()


async def import_from_csv(file_path: str | Path) -> int:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    count = 0
    async with async_session_maker() as session:
        # Справочник exercise_reference: id и caption -> id (для подстановки при несовпадении id из CSV)
        refs = await session.execute(select(ExerciseReference.id, ExerciseReference.caption))
        ref_rows = refs.all()
        valid_ref_ids = {r[0] for r in ref_rows if r[0] is not None}
        caption_to_id = {}
        for r in ref_rows:
            if r[1]:
                key = str(r[1]).strip().lower()
                if key and key not in caption_to_id:
                    caption_to_id[key] = r[0]

        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_exercise_id = _int(row.get("exercise_id"))
                caption = _str(row.get("exercise_caption"))
                if csv_exercise_id is not None and csv_exercise_id in valid_ref_ids:
                    effective_exercise_id = csv_exercise_id
                elif caption and caption.strip():
                    effective_exercise_id = caption_to_id.get(caption.strip().lower())
                else:
                    effective_exercise_id = None

                # goal_*_weight и week*_weight в CSV — float (0.95, 1.0); в модели int — округляем
                goal_fat = row.get("goal_fat_loss_weight")
                goal_mass = row.get("goal_mass_gain_weight")
                goal_maint = row.get("goal_maintenance_weight")
                w1, w2, w3, w4 = row.get("week1_weight"), row.get("week2_weight"), row.get("week3_weight"), row.get("week4_weight")
                pool = ExerciseBuilderPool(
                    uuid=uuid4(),
                    actual=True,
                    exercise_id=effective_exercise_id,
                    exercise_caption=_str(row.get("exercise_caption")),
                    difficulty_level=_str(row.get("difficulty_level")),
                    primary_muscle_group=_str(row.get("primary_muscle_group")),
                    auxiliary_muscle_groups=_str(row.get("auxiliary_muscle_groups")),
                    preferred_role=_str(row.get("preferred_role")),
                    is_anchor_candidate=_bool(row.get("is_anchor_candidate")),
                    anchor_priority_tier=_str(row.get("anchor_priority_tier")),
                    uses_external_load=_bool(row.get("uses_external_load")),
                    default_min_reps=_int(row.get("default_min_reps")),
                    default_max_reps=_int(row.get("default_max_reps")),
                    default_min_sets=_int(row.get("default_min_sets")),
                    default_max_sets=_int(row.get("default_max_sets")),
                    default_rest_seconds=_int(row.get("default_rest_seconds")),
                    is_time_based=_bool(row.get("is_time_based")),
                    default_duration_seconds_min=_int(row.get("default_duration_seconds_min")),
                    default_duration_seconds_max=_int(row.get("default_duration_seconds_max")),
                    estimated_time_per_set_seconds=_int(row.get("estimated_time_per_set_seconds")),
                    variation_group_code=_str(row.get("variation_group_code")),
                    base_priority=_int(row.get("base_priority")),
                    goal_fat_loss_weight=_int(float(goal_fat)) if goal_fat and str(goal_fat).strip() else None,
                    goal_mass_gain_weight=_int(float(goal_mass)) if goal_mass and str(goal_mass).strip() else None,
                    goal_maintenance_weight=_int(float(goal_maint)) if goal_maint and str(goal_maint).strip() else None,
                    week1_weight=_int(float(w1)) if w1 and str(w1).strip() else None,
                    week2_weight=_int(float(w2)) if w2 and str(w2).strip() else None,
                    week3_weight=_int(float(w3)) if w3 and str(w3).strip() else None,
                    week4_weight=_int(float(w4)) if w4 and str(w4).strip() else None,
                    cooldown_sessions=_str(row.get("cooldown_sessions")) or None,
                    max_usage_per_28d=_int(row.get("max_usage_per_28d")),
                    can_use_in_heavy_push=_bool(row.get("can_use_in_heavy_push")),
                    can_use_in_heavy_pull=_bool(row.get("can_use_in_heavy_pull")),
                    can_use_in_heavy_legs=_bool(row.get("can_use_in_heavy_legs")),
                    can_use_in_light_recovery=_bool(row.get("can_use_in_light_recovery")),
                    can_use_in_light_pump=_bool(row.get("can_use_in_light_pump")),
                    can_use_in_light_core=_bool(row.get("can_use_in_light_core")),
                    can_be_secondary_in_heavy_push=_bool(row.get("can_be_secondary_in_heavy_push")),
                    can_be_secondary_in_heavy_pull=_bool(row.get("can_be_secondary_in_heavy_pull")),
                    can_be_secondary_in_heavy_legs=_bool(row.get("can_be_secondary_in_heavy_legs")),
                    anchor_order_push=_int(row.get("anchor_order_push")),
                    anchor_order_pull=_int(row.get("anchor_order_pull")),
                    anchor_order_legs=_int(row.get("anchor_order_legs")),
                    is_unilateral=_bool(row.get("is_unilateral")),
                    is_active=_bool(row.get("is_active")),
                    source_analysis_note=_str(row.get("source_analysis_note")),
                    anchor_priority_tier_push=_str(row.get("anchor_priority_tier_push")),
                    anchor_cycle_lock_recommended_push=_bool(row.get("anchor_cycle_lock_recommended_push")),
                    anchor_priority_tier_pull=_str(row.get("anchor_priority_tier_pull")),
                    anchor_cycle_lock_recommended_pull=_bool(row.get("anchor_cycle_lock_recommended_pull")),
                    anchor_priority_tier_legs=_str(row.get("anchor_priority_tier_legs")),
                    anchor_cycle_lock_recommended_legs=_bool(row.get("anchor_cycle_lock_recommended_legs")),
                    slot_family=_str(row.get("slot_family")),
                    fatigue_cost=_int(row.get("fatigue_cost")),
                    role_rank_in_slot=_int(row.get("role_rank_in_slot")),
                )
                session.add(pool)
                count += 1
        await session.commit()
    return count
