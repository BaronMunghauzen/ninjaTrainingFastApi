"""
Подбор замен для упражнения в тренировке: переиспользует app.user_program_plan.training_builder.
"""
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy import select, update as sqlalchemy_update
from sqlalchemy.orm import joinedload

from app.database import async_session_maker
from app.exercise_builder_pool.models import ExerciseBuilderPool
from app.exercise_reference.models import ExerciseReference
from app.exercises.models import Exercise
from app.trainings.models import Training
from app.user_program_plan.models import UserProgramPlan
from app.user_program_plan.training_builder import (
    build_training_builder_context,
    normalize_replacement_action,
    pool_difficulty_for_reference,
    replacement_duration_seconds,
    suggest_anchor_replacements,
    suggest_pool_replacements_for_slot,
)
from app.training_composition_rules.dao import TrainingCompositionRuleDAO

# Сколько кандидатов ранжируем до пагинации (после — срез по page/page_size).
MAX_REPLACEMENT_CANDIDATES_RANKED = 500


async def _find_composition_rule(plan, training_type: str):
    all_rules = await TrainingCompositionRuleDAO.find_all(actual=True)
    tt = (training_type or "").strip().lower()
    for r in all_rules:
        if (
            (r.training_type or "").strip().lower() == tt
            and (r.program_goal or "").strip().lower() == (plan.program_goal or "").strip().lower()
            and r.program_week_index == (plan.current_week_index or 1)
            and r.duration_target_minutes == plan.duration_target_minutes
        ):
            return r
    return None


async def sibling_exercise_reference_ids(training_id: int) -> Set[int]:
    async with async_session_maker() as session:
        r = await session.execute(
            select(Exercise.exercise_reference_id).where(
                Exercise.training_id == training_id,
                Exercise.exercise_reference_id.isnot(None),
            )
        )
        return {row[0] for row in r.all() if row[0]}


async def load_exercise_training_plan(exercise_uuid: UUID):
    """Exercise + training + user_program_plan (если есть)."""
    async with async_session_maker() as session:
        q = (
            select(Exercise)
            .options(joinedload(Exercise.training))
            .where(Exercise.uuid == exercise_uuid)
        )
        ex = (await session.execute(q)).unique().scalar_one_or_none()
        if not ex:
            return None, None, None
        training = ex.training
        plan = None
        if training is not None and training.user_program_plan_id is not None:
            plan = (
                await session.execute(
                    select(UserProgramPlan).where(UserProgramPlan.id == training.user_program_plan_id)
                )
            ).scalar_one_or_none()
        session.expunge(ex)
        if training is not None:
            session.expunge(training)
        if plan is not None:
            session.expunge(plan)
        return ex, training, plan


def _serialize_exercise_reference(ref) -> Optional[dict]:
    if ref is None:
        return None
    gif = getattr(ref, "gif", None)
    return {
        "uuid": str(ref.uuid),
        "caption": ref.caption,
        "muscle_group": ref.muscle_group,
        "description": ref.description,
        "equipment_name": ref.equipment_name,
        "exercise_type": ref.exercise_type,
        "original_name": getattr(ref, "original_name", None),
        "gif_uuid": str(gif.uuid) if gif else None,
    }


def _serialize_pool_short(pool_row) -> dict:
    return {
        "uuid": str(pool_row.uuid),
        "exercise_caption": pool_row.exercise_caption,
        "difficulty_level": pool_row.difficulty_level,
        "primary_muscle_group": pool_row.primary_muscle_group,
        "preferred_role": pool_row.preferred_role,
        "uses_external_load": pool_row.uses_external_load,
        "variation_group_code": pool_row.variation_group_code,
    }


async def _pools_with_references(pool_ids: List[int]) -> Dict[int, ExerciseBuilderPool]:
    if not pool_ids:
        return {}
    async with async_session_maker() as session:
        r = await session.execute(
            select(ExerciseBuilderPool)
            .options(
                joinedload(ExerciseBuilderPool.exercise_reference).joinedload(ExerciseReference.gif),
            )
            .where(ExerciseBuilderPool.id.in_(pool_ids))
        )
        rows = r.unique().scalars().all()
        return {p.id: p for p in rows}


async def get_replacement_candidates(
    exercise_uuid: UUID,
    action: str,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    act = normalize_replacement_action(action)
    if act not in ("simplify", "replace", "complicate"):
        return {"error": "invalid_action", "action_normalized": act}

    page = max(1, int(page))
    page_size = min(100, max(1, int(page_size)))

    ex, training, plan = await load_exercise_training_plan(exercise_uuid)
    if ex is None:
        return {"error": "exercise_not_found"}
    if training is None:
        return {"error": "no_training"}
    if plan is None:
        return {"error": "no_program_plan"}

    if training.user_id != user_id:
        return {"error": "forbidden"}

    rule = await _find_composition_rule(plan, training.training_type)
    if rule is None:
        return {"error": "no_matching_rule"}

    exclude_refs = await sibling_exercise_reference_ids(training.id)
    ctx = await build_training_builder_context(plan, training.training_type, user_id, plan.id)
    anchor_line = (ex.pool_difficulty_level or "").strip() or pool_difficulty_for_reference(
        ctx["base_pool_items"], ex.exercise_reference_id
    )

    role = (ex.slot_type or "main").strip().lower()
    tt = (training.training_type or "").strip().lower()
    limb = None
    if "heavy_push" in tt:
        limb = "push"
    elif "heavy_pull" in tt:
        limb = "pull"
    elif "heavy_legs" in tt:
        limb = "legs"

    if role == "anchor" and limb:
        pools = await suggest_anchor_replacements(
            plan=plan,
            training_type=training.training_type,
            user_id=user_id,
            plan_id=plan.id,
            limb=limb,
            exclude_exercise_reference_ids=exclude_refs,
            anchor_diff_for_order=anchor_line,
            action=action,
            top_n=MAX_REPLACEMENT_CANDIDATES_RANKED,
            ctx=ctx,
        )
    elif role == "anchor":
        pools = []
    else:
        pools = await suggest_pool_replacements_for_slot(
            plan=plan,
            rule=rule,
            training_type=training.training_type,
            user_id=user_id,
            plan_id=plan.id,
            slot_role=role,
            action=action,
            exclude_exercise_reference_ids=exclude_refs,
            anchor_diff_for_order=anchor_line,
            top_n=MAX_REPLACEMENT_CANDIDATES_RANKED,
            ctx=ctx,
        )

    total = len(pools)
    start = (page - 1) * page_size
    page_pools = pools[start : start + page_size]

    by_id = await _pools_with_references([p.id for p in page_pools])
    items = []
    for p in page_pools:
        full = by_id.get(p.id)
        if not full:
            continue
        items.append(
            {
                "exercise_builder_pool": _serialize_pool_short(full),
                "exercise_reference": _serialize_exercise_reference(full.exercise_reference),
            }
        )

    total_pages = (total + page_size - 1) // page_size if total else 0

    return {
        "action_normalized": act,
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": start + page_size < total,
        "has_prev": page > 1,
    }


async def replace_exercise_from_pool(
    exercise_uuid: UUID,
    pool_uuid: UUID,
    user_id: int,
) -> Dict[str, Any]:
    from app.exercise_builder_pool.dao import ExerciseBuilderPoolDAO
    from app.exercise_reference.dao import ExerciseReferenceDAO
    from app.exercises.dao import ExerciseDAO

    ex, training, plan = await load_exercise_training_plan(exercise_uuid)
    if ex is None:
        return {"error": "exercise_not_found"}
    if training is None:
        return {"error": "no_training"}
    if training.user_id != user_id:
        return {"error": "forbidden"}

    pool = await ExerciseBuilderPoolDAO.find_one_or_none(uuid=pool_uuid)
    if pool is None or not pool.exercise_id:
        return {"error": "pool_not_found"}

    ref = await ExerciseReferenceDAO.find_one_or_none(id=pool.exercise_id)
    if ref is None:
        return {"error": "exercise_reference_not_found"}

    sibs = await sibling_exercise_reference_ids(training.id)
    if pool.exercise_id in sibs and pool.exercise_id != ex.exercise_reference_id:
        return {"error": "reference_already_in_workout"}

    caption = pool.exercise_caption or ref.caption
    muscle = pool.primary_muscle_group or ref.muscle_group or ""

    rule = await _find_composition_rule(plan, training.training_type) if plan else None
    duration_sec = replacement_duration_seconds(pool, rule, ex.slot_type, ex.reps_count)

    await ExerciseDAO.update(
        exercise_uuid,
        exercise_reference_uuid=str(ref.uuid),
        caption=caption,
        muscle_group=muscle,
        pool_difficulty_level=pool.difficulty_level,
        with_weight=bool(pool.uses_external_load) if pool.uses_external_load is not None else False,
        is_time_based=getattr(pool, "is_time_based", None),
    )
    async with async_session_maker() as session:
        async with session.begin():
            await session.execute(
                sqlalchemy_update(Exercise)
                .where(Exercise.uuid == exercise_uuid)
                .values(duration_seconds=duration_sec)
            )
    updated = await ExerciseDAO.find_full_data(exercise_uuid)
    data = updated.to_dict()
    data.pop("user_id", None)
    data["exercise_reference_uuid"] = (
        str(updated.exercise_reference.uuid) if getattr(updated, "exercise_reference", None) else None
    )
    return {"message": "ok", "exercise": data}
