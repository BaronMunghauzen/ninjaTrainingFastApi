"""
Сервис для работы с user_exercise_stats.
user_exercise — таблица подходов: каждая запись = один подход (set_number, weight, reps, status).
"""
from datetime import date, datetime
from typing import Optional, Tuple
from uuid import UUID
from collections import defaultdict

from app.database import async_session_maker
from app.user_exercise_stats.models import UserExerciseStats
from sqlalchemy import select
from app.user_exercises.models import UserExercise, ExerciseStatus
from app.exercises.models import Exercise


async def get_by_user_and_exercise(user_id: int, exercise_reference_id: int) -> Optional[UserExerciseStats]:
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserExerciseStats).filter_by(
                user_id=user_id,
                exercise_reference_id=exercise_reference_id,
                actual=True,
            )
        )
        obj = result.scalar_one_or_none()
        if obj:
            session.expunge(obj)
        return obj


async def bulk_get_by_user_and_exercise_ids(
    user_id: int, exercise_reference_ids: list[int]
) -> list[UserExerciseStats]:
    if not exercise_reference_ids:
        return []
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserExerciseStats).filter_by(user_id=user_id, actual=True).where(
                UserExerciseStats.exercise_reference_id.in_(exercise_reference_ids)
            )
        )
        items = result.scalars().all()
        for o in items:
            session.expunge(o)
        return items


def times_used_from_stats(stats: Optional[UserExerciseStats]) -> Tuple[int, int, int]:
    """По записи user_exercise_stats возвращает (times_used_last_7d, 14d, 28d)."""
    if not stats:
        return 0, 0, 0
    s7 = sum(getattr(stats, f"usage_day_{i}", 0) or 0 for i in range(7))
    s14 = sum(getattr(stats, f"usage_day_{i}", 0) or 0 for i in range(14))
    s28 = sum(getattr(stats, f"usage_day_{i}", 0) or 0 for i in range(28))
    return s7, s14, s28


def _shift_usage_ring(stats: UserExerciseStats, event_date: date) -> None:
    """Сдвиг ring-buffer использования на дату события."""
    shift_date = stats.usage_ring_last_shift_date
    if shift_date is None:
        stats.usage_ring_last_shift_date = event_date
        for i in range(28):
            setattr(stats, f"usage_day_{i}", 0)
        return
    delta = (event_date - shift_date).days
    if delta >= 28:
        stats.usage_ring_last_shift_date = event_date
        for i in range(28):
            setattr(stats, f"usage_day_{i}", 0)
        return
    if 1 <= delta <= 27:
        days = [getattr(stats, f"usage_day_{i}") for i in range(28)]
        for i in range(28 - delta):
            setattr(stats, f"usage_day_{i + delta}", days[i])
        for i in range(delta):
            setattr(stats, f"usage_day_{i}", 0)
        stats.usage_ring_last_shift_date = event_date


def _build_sets_summary_and_best(sets: list) -> Tuple[dict, Optional[float], Optional[int], Optional[int], Optional[float]]:
    """
    По списку подходов (словари с set_number, weight, reps) строит last_sets_summary_json
    и возвращает (summary_dict, best_weight, best_reps, best_duration, total_volume).
    duration_seconds в UserExercise нет — best_duration всегда None.
    """
    if not sets:
        return {}, None, None, None, None

    # Сортируем по set_number
    sorted_sets = sorted(sets, key=lambda s: s.get("set_number", 0))
    list_for_json = []
    best_weight = None
    best_reps = None
    total_volume = 0.0

    for s in sorted_sets:
        set_number = s.get("set_number", 0)
        weight = s.get("weight")
        reps = s.get("reps") or 0
        duration_seconds = s.get("duration_seconds")  # в модели user_exercise нет — оставляем null
        is_completed = s.get("is_completed", True)

        list_for_json.append({
            "set_number": set_number,
            "weight": weight,
            "reps": reps,
            "duration_seconds": duration_seconds,
            "is_completed": is_completed,
        })
        if is_completed:
            if weight is not None:
                if best_weight is None or weight > best_weight:
                    best_weight = float(weight)
                total_volume += float(weight) * reps
            if reps is not None and (best_reps is None or reps > best_reps):
                best_reps = int(reps)

    best_duration = None  # в user_exercise нет поля длительности
    summary = {
        "sets": list_for_json,
        "exercise_total_volume": total_volume if total_volume else None,
        "exercise_best_set_weight": best_weight,
        "exercise_best_set_reps": best_reps,
        "exercise_best_set_duration": best_duration,
    }
    return summary, best_weight, best_reps, best_duration, total_volume if total_volume else None


async def upsert_on_training_passed(user_training_uuid: UUID) -> dict:
    """
    Обновить user_exercise_stats по завершённой тренировке (status=PASSED).
    Учитываются только упражнения, у которых есть хотя бы один подход со статусом PASSED.
    Для каждого такого упражнения: сборка last_sets_summary_json по подходам, обновление best_* через max.
    """
    from app.user_training.dao import UserTrainingDAO

    user_training = await UserTrainingDAO.find_full_data(user_training_uuid)
    if not user_training or (getattr(user_training.status, "value", str(user_training.status)) != "PASSED"):
        return {"updated_count": 0, "exercise_ids_updated": [], "completed_at": None, "user_training_uuid": str(user_training_uuid)}

    completed_at = user_training.completed_at
    if not completed_at:
        return {"updated_count": 0, "exercise_ids_updated": [], "completed_at": None, "user_training_uuid": str(user_training_uuid)}

    event_date = completed_at.date() if hasattr(completed_at, "date") else date(completed_at.year, completed_at.month, completed_at.day)
    user_id = user_training.user_id
    training_id = user_training.training_id
    training_type = getattr(user_training, "training_type", None)

    if not training_id:
        return {"updated_count": 0, "exercise_ids_updated": [], "completed_at": completed_at.isoformat() if hasattr(completed_at, "isoformat") else str(completed_at), "user_training_uuid": str(user_training_uuid)}

    # Все подходы этой тренировки со статусом PASSED (завершённые)
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserExercise)
            .where(
                UserExercise.training_id == training_id,
                UserExercise.status == ExerciseStatus.PASSED,
            )
            .order_by(UserExercise.exercise_id, UserExercise.set_number)
        )
        all_sets = result.scalars().all()

    # Группируем по exercise_id: для каждого упражнения — список подходов
    by_exercise: dict[int, list] = defaultdict(list)
    for ue in all_sets:
        by_exercise[ue.exercise_id].append({
            "set_number": ue.set_number,
            "weight": ue.weight,
            "reps": ue.reps,
            "duration_seconds": getattr(ue, "duration_seconds", None),
            "is_completed": True,
        })

    # exercise_id -> exercise_reference_id (нужен один запрос по всем exercise_id)
    exercise_ids = list(by_exercise.keys())
    if not exercise_ids:
        return {"updated_count": 0, "exercise_ids_updated": [], "completed_at": completed_at.isoformat() if hasattr(completed_at, "isoformat") else str(completed_at), "user_training_uuid": str(user_training_uuid)}

    async with async_session_maker() as session:
        ex_result = await session.execute(select(Exercise).where(Exercise.id.in_(exercise_ids)))
        exercises = {e.id: e for e in ex_result.scalars().all()}

    updated_ref_ids = []
    async with async_session_maker() as session:
        for exercise_id, sets in by_exercise.items():
            exercise = exercises.get(exercise_id)
            if not exercise or not exercise.exercise_reference_id:
                continue
            ref_id = exercise.exercise_reference_id

            # Только если есть хотя бы один завершённый подход (у нас все в списке уже PASSED)
            if not sets:
                continue

            summary, exercise_best_weight, exercise_best_reps, exercise_best_duration, exercise_total_volume = _build_sets_summary_and_best(sets)

            # Найти или создать UserExerciseStats
            r = await session.execute(
                select(UserExerciseStats).filter_by(
                    user_id=user_id, exercise_reference_id=ref_id, actual=True
                )
            )
            stats = r.scalar_one_or_none()
            if not stats:
                stats = UserExerciseStats(
                    user_id=user_id,
                    exercise_reference_id=ref_id,
                    actual=True,
                    total_usage_count=0,
                    usage_ring_last_shift_date=event_date,
                )
                for i in range(28):
                    setattr(stats, f"usage_day_{i}", 0)
                session.add(stats)
                await session.flush()

            _shift_usage_ring(stats, event_date)
            setattr(stats, "usage_day_0", getattr(stats, "usage_day_0", 0) + 1)

            stats.last_used_at = completed_at
            stats.total_usage_count = (stats.total_usage_count or 0) + 1
            stats.last_workout_uuid = user_training.uuid
            stats.last_training_type = training_type
            stats.last_sets_summary_json = summary

            if exercise_best_weight is not None:
                stats.best_weight_value = max(stats.best_weight_value or 0, exercise_best_weight)
            if exercise_best_reps is not None:
                stats.best_reps_value = max(stats.best_reps_value or 0, exercise_best_reps)
            if exercise_best_duration is not None:
                stats.best_duration_seconds = max(stats.best_duration_seconds or 0, exercise_best_duration)
            if exercise_total_volume is not None:
                stats.best_volume_value = max(stats.best_volume_value or 0, exercise_total_volume)

            updated_ref_ids.append(ref_id)

        await session.commit()

    return {
        "updated_count": len(updated_ref_ids),
        "exercise_ids_updated": updated_ref_ids,
        "completed_at": completed_at.isoformat() if hasattr(completed_at, "isoformat") else str(completed_at),
        "user_training_uuid": str(user_training_uuid),
    }
