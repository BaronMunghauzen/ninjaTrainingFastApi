"""
Логика определения группы (heavy/light), типа тренировки и создания тренировки по программе.
"""
from datetime import date, datetime, timedelta
from typing import Literal, Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from app.database import async_session_maker
from app.user_program_plan.models import UserProgramPlan
from app.user_training.models import UserTraining
from app.trainings.models import Training
from app.exercises.models import Exercise


# --- Вспомогательные запросы ---

async def _get_plan_by_uuid(plan_uuid) -> Optional[UserProgramPlan]:
    from app.user_program_plan.dao import UserProgramPlanDAO
    try:
        return await UserProgramPlanDAO.find_full_data(UUID(str(plan_uuid)))
    except Exception:
        return None


async def _get_last_passed_trainings_for_plan(plan_id: int, limit: int = 10) -> list:
    """Последние завершённые тренировки по плану (любой тип), по убыванию completed_at."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserTraining)
            .where(
                UserTraining.user_program_plan_id == plan_id,
                UserTraining.status == "PASSED",
                UserTraining.completed_at.isnot(None),
            )
            .order_by(UserTraining.completed_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        for r in rows:
            session.expunge(r)
        return rows


async def _count_heavy_passed_since_start(plan_id: int, start_date: date) -> int:
    """Количество heavy_* тренировок (PASSED) с completed_at >= start_date."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(func.count(UserTraining.id))
            .where(
                UserTraining.user_program_plan_id == plan_id,
                UserTraining.status == "PASSED",
                UserTraining.completed_at.isnot(None),
                UserTraining.completed_at >= datetime.combine(start_date, datetime.min.time()),
                UserTraining.training_type.like("heavy_%"),
            )
        )
        return result.scalar() or 0


async def _get_last_heavy_for_plan(plan_id: int):
    """Последняя heavy_* тренировка по плану."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserTraining)
            .where(
                UserTraining.user_program_plan_id == plan_id,
                UserTraining.status == "PASSED",
                UserTraining.training_type.like("heavy_%"),
            )
            .order_by(UserTraining.completed_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            session.expunge(row)
        return row


def _to_iso(dt):
    if dt is None:
        return None
    return dt.isoformat() if hasattr(dt, "isoformat") else str(dt)


# --- Группа тренировки (heavy / light) ---

HEAVY_ROTATION = ["heavy_push", "heavy_pull", "heavy_legs"]


def _user_subscription_active(user) -> bool:
    """Активная подписка по полю user.subscription_status (значение active)."""
    if user is None:
        return False
    st = getattr(user, "subscription_status", None)
    if st is None:
        return False
    val = getattr(st, "value", st)
    return val == "active"


def _computed_program_week_from_completed_heavy(completed_heavy: int) -> int:
    """Неделя программы 1..4: каждые 3 завершённых heavy — следующая неделя (цикл по 4)."""
    ch = max(0, int(completed_heavy or 0))
    return (ch // 3) % 4 + 1


def _will_update_program_week_on_heavy_push_create(
    plan,
    completed_heavy: int,
    training_type: str,
    *,
    subscription_active: bool = True,
) -> bool:
    """
    True, если create_training_by_program для этого типа выставит current_week_index в БД
    (heavy_push: синхронизация с completed_heavy_training_count).
    Без активной подписки неделя в БД не перещёлкивается — всегда False.
    """
    if plan is None:
        return False
    if not subscription_active:
        return False
    if (training_type or "").strip().lower() != "heavy_push":
        return False
    computed = _computed_program_week_from_completed_heavy(completed_heavy)
    return computed != (getattr(plan, "current_week_index", None) or 1)


def _preference_meta(
    preferred_group: Optional[str],
    *,
    applied: bool = False,
    rejected_reason: Optional[str] = None,
) -> dict:
    """Поля ответа API про предпочтение пользователя (heavy/light)."""
    pref = (preferred_group or "").strip().lower() if preferred_group else None
    if pref not in ("heavy", "light"):
        pref = None
    return {
        "preferred_group": pref,
        "preference_applied": applied,
        "preference_rejected_reason": rejected_reason,
    }


def _type_response_pref(group_result: dict) -> dict:
    """Срез полей предпочтения для ответа type-for-date."""
    return {
        "preferred_group": group_result.get("preferred_group"),
        "preference_applied": group_result.get("preference_applied", False),
        "preference_rejected_reason": group_result.get("preference_rejected_reason"),
    }


def _normalize_preferred_group(preferred_group: Optional[str]) -> Optional[Literal["heavy", "light"]]:
    p = (preferred_group or "").strip().lower() if preferred_group else None
    if p == "heavy":
        return "heavy"
    if p == "light":
        return "light"
    return None


def _finalize_group_with_preference(
    algorithm_group: str,
    algorithm_reason: str,
    pref: Optional[Literal["heavy", "light"]],
) -> tuple[str, str, bool]:
    """
    Если pref задан — итоговая группа всегда совпадает с предпочтением пользователя.
    Возвращает (group, reason, preference_applied).
    """
    if not pref:
        return algorithm_group, algorithm_reason, False
    if pref == "heavy":
        if algorithm_group != "heavy":
            return "heavy", f"user_preferred_heavy_override:{algorithm_reason}", True
        return "heavy", algorithm_reason, False
    if algorithm_group != "light":
        return "light", f"user_preferred_light_override:{algorithm_reason}", True
    return "light", algorithm_reason, False


async def get_training_group_for_date(
    user_program_plan_uuid: str,
    training_datetime_to_plan: datetime,
    preferred_group: Optional[Literal["heavy", "light"]] = None,
) -> dict:
    """
    Определение группы тренировки на дату: heavy или light.
    Если передан preferred_group (heavy|light) — итоговая группа всегда равна ему
    (алгоритмическая рекомендация сохраняется в reason через префикс override).

    Возвращает также preferred_group, preference_applied, preference_rejected_reason (всегда null).
    """
    pref = _normalize_preferred_group(preferred_group)

    plan = await _get_plan_by_uuid(user_program_plan_uuid)
    if not plan:
        group, reason, applied = _finalize_group_with_preference("heavy", "plan_not_found", pref)
        return {
            "group": group,
            "reason": reason,
            "training_datetime_to_plan": _to_iso(training_datetime_to_plan),
            "start_date": None,
            "completed_heavy_training_count": 0,
            "current_week_index": 1,
            **_preference_meta(preferred_group, applied=applied, rejected_reason=None),
        }

    start_date = plan.start_date
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    completed_heavy = await _count_heavy_passed_since_start(plan.id, start_date)
    current_week = plan.current_week_index or 1

    last_trainings = await _get_last_passed_trainings_for_plan(plan.id, limit=1)
    if not last_trainings:
        group, reason, applied = _finalize_group_with_preference(
            "heavy", "no_previous_program_trainings", pref
        )
        return {
            "group": group,
            "reason": reason,
            "training_datetime_to_plan": _to_iso(training_datetime_to_plan),
            "start_date": start_date.isoformat() if start_date else None,
            "completed_heavy_training_count": completed_heavy,
            "current_week_index": current_week,
            **_preference_meta(preferred_group, applied=applied, rejected_reason=None),
        }

    last = last_trainings[0]
    completed_at = last.completed_at
    if not completed_at:
        group, reason, applied = _finalize_group_with_preference(
            "heavy", "no_previous_program_trainings", pref
        )
        return {
            "group": group,
            "reason": reason,
            "training_datetime_to_plan": _to_iso(training_datetime_to_plan),
            "start_date": start_date.isoformat() if start_date else None,
            "completed_heavy_training_count": completed_heavy,
            "current_week_index": current_week,
            **_preference_meta(preferred_group, applied=applied, rejected_reason=None),
        }

    delta_seconds = (training_datetime_to_plan - completed_at).total_seconds()
    delta_hours = delta_seconds / 3600
    training_type_val = (last.training_type or "").strip().lower()

    # Шаг 1: базовая группа (алгоритм)
    if delta_hours > 72:
        group = "heavy"
        reason = "long_break_more_than_72h"
    elif training_type_val.startswith("light_"):
        group = "heavy"
        reason = "last_training_was_light"
    elif delta_hours < 36:
        group = "light"
        reason = "last_heavy_less_than_36h"
    elif 36 <= delta_hours <= 72:
        group = "heavy"
        reason = "last_heavy_between_36h_72h"
    else:
        group = "heavy"
        reason = "last_heavy_between_36h_72h"

    # Шаг 2: коррекция — квота heavy (3 в неделю): если выполнена — сегодня light
    if group == "heavy" and completed_heavy > 0 and (completed_heavy % 3) == 0:
        group = "light"
        reason = "heavy_quota_completed_for_week"

    # Шаг 3: предпочтение пользователя — всегда даём запрошенную группу
    group, reason, preference_applied = _finalize_group_with_preference(group, reason, pref)

    return {
        "group": group,
        "reason": reason,
        "training_datetime_to_plan": _to_iso(training_datetime_to_plan),
        "start_date": start_date.isoformat() if start_date else None,
        "completed_heavy_training_count": completed_heavy,
        "current_week_index": current_week,
        **_preference_meta(
            preferred_group, applied=preference_applied, rejected_reason=None
        ),
    }


async def get_training_type_for_date(
    user_program_plan_uuid: str,
    training_datetime_to_plan: datetime,
    preferred_group: Optional[Literal["heavy", "light"]] = None,
    user=None,
) -> dict:
    """
    Определение типа тренировки: heavy_push/heavy_pull/heavy_legs или light_*.

    Для группы light сейчас всегда возвращается light_core (ротация pump/recovery — позже).

    preferred_group: опционально heavy|light — учитывается при выборе группы (см. get_training_group_for_date).

    user: текущий пользователь; без активной подписки в ответе current_week_index = 1 и при создании
    тренировки используется только неделя 1.

    will_update_program_week_on_create: для heavy_push — будет ли при POST create-training
    синхронизирован current_week_index с completed_heavy_training_count (после цикла push–pull–legs);
    без активной подписки всегда False.
    """
    from app.users.dao import UsersDAO

    group_result = await get_training_group_for_date(
        user_program_plan_uuid, training_datetime_to_plan, preferred_group=preferred_group
    )
    group = group_result.get("group", "heavy")
    plan = await _get_plan_by_uuid(user_program_plan_uuid)
    completed_heavy = group_result.get("completed_heavy_training_count", 0)
    plan_user = user
    if plan_user is None and plan is not None and getattr(plan, "user_id", None):
        plan_user = await UsersDAO.find_one_or_none(id=plan.user_id)
    sub_active = _user_subscription_active(plan_user)
    current_week = 1 if not sub_active else (group_result.get("current_week_index") or 1)

    def _week_on_create_meta(resolved_training_type: str) -> dict:
        return {
            "will_update_program_week_on_create": _will_update_program_week_on_heavy_push_create(
                plan, completed_heavy, resolved_training_type, subscription_active=sub_active
            ),
        }

    if group == "heavy":
        if completed_heavy == 0:
            return {
                "training_type": "heavy_push",
                "reason": "first_heavy_in_program",
                "training_datetime_to_plan": group_result["training_datetime_to_plan"],
                "start_date": group_result["start_date"],
                "completed_heavy_training_count": completed_heavy,
                "current_week_index": current_week,
                **_type_response_pref(group_result),
                **_week_on_create_meta("heavy_push"),
            }
        if not plan:
            return {
                "training_type": "heavy_push",
                "reason": "plan_not_found_fallback_heavy",
                "training_datetime_to_plan": group_result["training_datetime_to_plan"],
                "start_date": group_result["start_date"],
                "completed_heavy_training_count": completed_heavy,
                "current_week_index": current_week,
                **_type_response_pref(group_result),
                **_week_on_create_meta("heavy_push"),
            }
        last_heavy = await _get_last_heavy_for_plan(plan.id)
        if not last_heavy or not last_heavy.training_type:
            return {
                "training_type": "heavy_push",
                "reason": "next_heavy_in_rotation",
                "training_datetime_to_plan": group_result["training_datetime_to_plan"],
                "start_date": group_result["start_date"],
                "completed_heavy_training_count": completed_heavy,
                "current_week_index": current_week,
                **_type_response_pref(group_result),
                **_week_on_create_meta("heavy_push"),
            }
        last_type = (last_heavy.training_type or "").strip().lower()
        try:
            idx = HEAVY_ROTATION.index(last_type)
            next_type = HEAVY_ROTATION[(idx + 1) % 3]
        except ValueError:
            next_type = "heavy_push"
        return {
            "training_type": next_type,
            "reason": "next_heavy_in_rotation",
            "training_datetime_to_plan": group_result["training_datetime_to_plan"],
            "start_date": group_result["start_date"],
            "completed_heavy_training_count": completed_heavy,
            "current_week_index": current_week,
            **_type_response_pref(group_result),
            **_week_on_create_meta(next_type),
        }

    # light — пока без ротации: всегда core (остальные light_* подключим отдельно)
    chosen = "light_core"
    reason = "light_always_core"

    return {
        "training_type": chosen,
        "reason": reason,
        "training_datetime_to_plan": group_result["training_datetime_to_plan"],
        "start_date": group_result["start_date"],
        "completed_heavy_training_count": completed_heavy,
        "current_week_index": current_week,
        **_type_response_pref(group_result),
        **_week_on_create_meta(chosen),
    }


async def create_training_by_program(
    user_uuid: str,
    training_type: str,
) -> dict:
    """
    Создание тренировки по программе: правила из training_composition_rules,
    подбор упражнений из exercise_builder_pool (+ equipment), создание training и exercise, затем user_training.
    Без активной подписки (subscription_status != active) правила и user_training.week — только для недели 1;
    current_week_index в БД при heavy_push не обновляется.
    Возвращает: user_training_uuid, training_uuid, exercises (список uuid).
    """
    from app.user_program_plan.dao import UserProgramPlanDAO
    from app.users.dao import UsersDAO
    from app.training_composition_rules.dao import TrainingCompositionRuleDAO
    from app.exercise_builder_pool.dao import ExerciseBuilderPoolDAO
    from app.exercise_builder_equipment.dao import ExerciseBuilderEquipmentDAO
    from app.trainings.dao import TrainingDAO
    from app.exercises.dao import ExerciseDAO
    from app.user_training.dao import UserTrainingDAO

    user = await UsersDAO.find_one_or_none(uuid=user_uuid)
    if not user:
        return {"error": "user_not_found", "user_training_uuid": None, "training_uuid": None, "exercises": []}

    plan = await UserProgramPlanDAO.find_actual_by_user_id(user.id)
    if not plan:
        return {"error": "no_actual_plan", "user_training_uuid": None, "training_uuid": None, "exercises": []}

    sub_active = _user_subscription_active(user)

    # Перещелкивание недели программы: при старте нового цикла (первый heavy — push) после 3 завершённых heavy,
    # а не при завершении legs (см. on_training_passed). Только при активной подписке.
    tt_norm = (training_type or "").strip().lower()
    if tt_norm == "heavy_push" and sub_active:
        cw = _computed_program_week_from_completed_heavy(plan.completed_heavy_training_count or 0)
        if (plan.current_week_index or 1) != cw:
            await UserProgramPlanDAO.update(plan.uuid, current_week_index=cw)
        plan.current_week_index = cw
    elif not sub_active:
        plan.current_week_index = 1

    # Правило состава под тип, цель, неделю и длительность
    all_rules = await TrainingCompositionRuleDAO.find_all(actual=True)
    rule = None
    for r in all_rules:
        if (
            (r.training_type or "").strip().lower() == (training_type or "").strip().lower()
            and (r.program_goal or "").strip().lower() == (plan.program_goal or "").strip().lower()
            and r.program_week_index == (plan.current_week_index or 1)
            and r.duration_target_minutes == plan.duration_target_minutes
        ):
            rule = r
            break
    if not rule:
        return {"error": "no_matching_rule", "user_training_uuid": None, "training_uuid": None, "exercises": []}

    # Создаём запись training (шаблон тренировки)
    caption = f"{training_type} ({plan.program_goal})"
    training_uuid = await TrainingDAO.add(
        program_uuid=None,
        training_type=training_type,
        user_uuid=str(user.uuid),
        caption=caption,
        description=None,
        difficulty_level=1,
        duration=rule.duration_target_minutes,
        order=0,
        muscle_group="",
        stage=None,
        image_uuid=None,
        actual=True,
        user_program_plan_uuid=str(plan.uuid),
    )
    training_obj = await TrainingDAO.find_one_or_none(uuid=training_uuid)
    if not training_obj:
        return {"error": "training_creation_failed", "user_training_uuid": None, "training_uuid": None, "exercises": []}

    from app.user_program_plan.training_builder import (
        build_training_exercises,
        duration_seconds_for_time_based_pool_item,
    )
    from app.exercise_reference.dao import ExerciseReferenceDAO

    exercise_items, limb, anchor_uuids_to_save = await build_training_exercises(
        plan, rule, training_type, user.id, plan.id
    )

    created_exercise_uuids = []
    order = 0
    role_priority = {"anchor": 0, "main": 1, "accessory": 2, "core": 3, "mobility": 4}
    sorted_items = sorted(exercise_items, key=lambda i: role_priority.get((i.get("role") or "").lower(), 999))
    for item in sorted_items:
        p = item["pool_item"]
        sets_val = item["sets"]
        reps_max = item.get("reps_max") or 12
        rest_val = item["rest"]
        ref_id = item.get("exercise_reference_id")
        ref = await ExerciseReferenceDAO.find_one_or_none_by_id(ref_id) if ref_id else None
        ref_uuid = str(ref.uuid) if ref else None
        # Ограничение sets/reps по умолчаниям упражнения (из ТЗ)
        def_min_sets = getattr(p, "default_min_sets", None)
        def_max_sets = getattr(p, "default_max_sets", None)
        def_min_reps = getattr(p, "default_min_reps", None)
        def_max_reps = getattr(p, "default_max_reps", None)
        if def_min_sets is not None and sets_val < def_min_sets:
            sets_val = def_min_sets
        if def_max_sets is not None and sets_val > def_max_sets:
            sets_val = def_max_sets
        if def_min_reps is not None and reps_max < def_min_reps:
            reps_max = def_min_reps
        if def_max_reps is not None and reps_max > def_max_reps:
            reps_max = def_max_reps
        pool_dl = getattr(p, "difficulty_level", None)
        pool_dl_str = (str(pool_dl).strip() if pool_dl is not None else "") or None
        duration_sec = duration_seconds_for_time_based_pool_item(p, reps_max)
        ex_uuid = await ExerciseDAO.add(
            exercise_type="strength",
            caption=item["caption"],
            muscle_group=p.primary_muscle_group or "",
            difficulty_level=1,
            pool_difficulty_level=pool_dl_str,
            order=order,
            slot_type=item.get("role"),
            sets_count=sets_val,
            reps_count=reps_max,
            rest_time=rest_val,
            with_weight=bool(getattr(p, "uses_external_load", True)),
            weight=None,
            exercise_reference_uuid=ref_uuid,
            training_uuid=str(training_uuid),
            is_time_based=getattr(p, "is_time_based", None),
            duration_seconds=duration_sec,
        )
        created_exercise_uuids.append(str(ex_uuid))
        order += 1

    if limb and anchor_uuids_to_save:
        update_payload = {
            f"anchor1_for_{limb}_uuid": anchor_uuids_to_save[0] if len(anchor_uuids_to_save) > 0 else None,
            f"anchor2_for_{limb}_uuid": anchor_uuids_to_save[1] if len(anchor_uuids_to_save) > 1 else None,
        }
        await UserProgramPlanDAO.update(plan.uuid, **update_payload)

    # UserTraining на сегодня
    today = date.today()
    program_week = plan.current_week_index or 1
    user_training_uuid = await UserTrainingDAO.add(
        user_program_plan_uuid=str(plan.uuid),
        training_uuid=str(training_uuid),
        user_uuid=str(user.uuid),
        training_date=today,
        status="ACTIVE",
        training_type=training_type,
        week=program_week,
    )
    return {
        "user_training_uuid": str(user_training_uuid),
        "training_uuid": str(training_uuid),
        "exercises": created_exercise_uuids,
        "message": "ok",
    }
