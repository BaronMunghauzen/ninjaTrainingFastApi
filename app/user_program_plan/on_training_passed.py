"""
Обновление user_program_plan после завершения тренировки (status=PASSED).
- Для heavy: пересчёт completed_heavy_training_count (current_week_index не меняется здесь —
  выравнивается при создании heavy_push, см. create_training_by_program).
- Расчёт recommended_next_training_date по training_days_per_week и последним датам тренировок.
"""
from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func
from app.database import async_session_maker
from app.user_training.models import UserTraining, TrainingStatus
from app.user_program_plan.models import UserProgramPlan
from app.trainings.models import Training


def _is_passed_status(status) -> bool:
    if status is None:
        return False
    if isinstance(status, TrainingStatus):
        return status == TrainingStatus.PASSED
    return str(status).upper() == "PASSED"


async def update_plan_on_training_passed(user_training_uuid: UUID) -> dict:
    """
    Вызывать после перевода user_training в PASSED.
    Если тренировка привязана к плану (user_program_plan_id или через training.user_program_plan_id),
    обновляет план: completed_heavy_training_count, recommended_next_training_date.
    """
    async with async_session_maker() as session:
        result = await session.execute(
            select(UserTraining).where(UserTraining.uuid == user_training_uuid)
        )
        ut = result.scalar_one_or_none()
        if not ut or not _is_passed_status(ut.status):
            return {"updated": False, "reason": "not_passed"}

        plan_id = ut.user_program_plan_id
        # План может быть только у связанной training (user_training.user_program_plan_id не заполнен)
        if plan_id is None and ut.training_id is not None:
            plan_id = await session.scalar(
                select(Training.user_program_plan_id).where(Training.id == ut.training_id)
            )
            if plan_id is not None:
                ut.user_program_plan_id = plan_id
                await session.flush()

        if not plan_id:
            return {"updated": False, "reason": "no_program_plan"}
        plan_result = await session.execute(select(UserProgramPlan).where(UserProgramPlan.id == plan_id))
        plan = plan_result.scalar_one_or_none()
        if not plan:
            return {"updated": False, "reason": "plan_not_found"}

        start_date = plan.start_date
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        training_type = (ut.training_type or "").strip().lower()

        if training_type.startswith("heavy_"):
            # Пересчёт completed_heavy_training_count
            count_result = await session.execute(
                select(func.count(UserTraining.id)).where(
                    UserTraining.user_program_plan_id == plan_id,
                    UserTraining.status == TrainingStatus.PASSED,
                    UserTraining.completed_at.isnot(None),
                    UserTraining.completed_at >= datetime.combine(start_date, datetime.min.time()),
                    UserTraining.training_type.like("heavy_%"),
                )
            )
            completed_heavy = count_result.scalar() or 0
            plan.completed_heavy_training_count = completed_heavy

        # Рекомендованная следующая дата
        next_date = await _compute_next_recommended_date(
            session, plan_id, plan.training_days_per_week or 3, plan.start_date
        )
        plan.recommended_next_training_date = next_date
        await session.commit()
        return {"updated": True, "recommended_next_training_date": next_date.isoformat() if next_date else None}


async def apply_recommended_next_date_after_anonymous_plan_link(plan_id: int) -> date:
    """
    После POST /user-program-plan/add/ с anonymous_session_id и привязкой user_training:
    - если есть завершённая тренировка (PASSED и completed_at задан) — дата по _compute_next_recommended_date;
    - иначе — recommended_next_training_date = сегодня.
    """
    async with async_session_maker() as session:
        plan_result = await session.execute(select(UserProgramPlan).where(UserProgramPlan.id == plan_id))
        plan = plan_result.scalar_one_or_none()
        if not plan:
            return date.today()

        passed_cnt = await session.scalar(
            select(func.count(UserTraining.id)).where(
                UserTraining.user_program_plan_id == plan_id,
                UserTraining.status == TrainingStatus.PASSED,
                UserTraining.completed_at.isnot(None),
            )
        )
        if (passed_cnt or 0) > 0:
            next_date = await _compute_next_recommended_date(
                session, plan_id, plan.training_days_per_week or 3, plan.start_date
            )
        else:
            next_date = date.today()

        plan.recommended_next_training_date = next_date
        await session.commit()
        return next_date


async def _compute_next_recommended_date(session, plan_id: int, days_per_week: int, start_date: date) -> date:
    """Простой расчёт: следующие дни после последней тренировки с шагом ~(7/days_per_week) дней."""
    from sqlalchemy import select
    result = await session.execute(
        select(UserTraining.completed_at)
        .where(
            UserTraining.user_program_plan_id == plan_id,
            UserTraining.status == TrainingStatus.PASSED,
            UserTraining.completed_at.isnot(None),
        )
        .order_by(UserTraining.completed_at.desc())
        .limit(1)
    )
    last_completed = result.scalar()
    if not last_completed:
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        base = start_date or date.today()
        return base + timedelta(days=1)
    if isinstance(last_completed, datetime):
        last_date = last_completed.date()
    else:
        last_date = last_completed
    gap = max(1, round(7 / max(1, days_per_week)))
    return last_date + timedelta(days=gap)
