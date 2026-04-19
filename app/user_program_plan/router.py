from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from app.user_program_plan.dao import UserProgramPlanDAO
from app.user_training.dao import UserTrainingDAO
from app.trainings.dao import TrainingDAO
from app.user_program_plan.schemas import (
    SUserProgramPlan,
    SUserProgramPlanAdd,
    SUserProgramPlanUpdate,
)
from app.user_program_plan.logic import (
    get_training_group_for_date,
    get_training_type_for_date,
    create_training_by_program,
)
from app.user_program_plan.on_training_passed import apply_recommended_next_date_after_anonymous_plan_link
from app.users.dao import UsersDAO
from app.users.dependencies import get_current_user_user

router = APIRouter(prefix="/user-program-plan", tags=["План программы тренировок (автоподбор)"])


class PreferredTrainingGroup(str, Enum):
    """Предпочтение группы тренировки для подбора типа (учитывается «с умом» в логике плана)."""

    heavy = "heavy"
    light = "light"


@router.post("/add/", summary="Создать план программы")
async def add_plan(body: SUserProgramPlanAdd, user_data=Depends(get_current_user_user)):
    values = body.model_dump()
    anonymous_session_id = values.pop("anonymous_session_id", None)
    # При создании: деактуализировать старые планы этого пользователя
    user_uuid = values.get("user_uuid")
    if user_uuid:
        user = await UsersDAO.find_one_or_none(uuid=user_uuid)
        if user:
            await UserProgramPlanDAO.deactualize_by_user_id(user.id)
    # По умолчанию при создании
    values.setdefault("current_week_index", 1)
    values.setdefault("completed_heavy_training_count", 0)
    values.pop("recommended_next_training_date", None)  # не заполнять при создании
    if anonymous_session_id is not None:
        values["anonymous_session_id"] = anonymous_session_id
    plan_uuid = await UserProgramPlanDAO.add(**values)
    linked_user_trainings_count = 0
    linked_trainings_count = 0
    if anonymous_session_id is not None:
        plan_row = await UserProgramPlanDAO.find_one_or_none(uuid=plan_uuid)
        if plan_row:
            linked_user_trainings_count = await UserTrainingDAO.set_program_plan_by_anonymous_session(
                anonymous_session_id, plan_row.id
            )
            linked_trainings_count = await TrainingDAO.set_program_plan_by_anonymous_session(
                anonymous_session_id, plan_row.id
            )
            await apply_recommended_next_date_after_anonymous_plan_link(plan_row.id)
    item = await UserProgramPlanDAO.find_full_data(plan_uuid)
    response = {
        "message": "План создан",
        "uuid": str(plan_uuid),
        "plan": SUserProgramPlan.model_validate(item),
    }
    if anonymous_session_id is not None:
        response["linked_user_trainings_count"] = linked_user_trainings_count
        response["linked_trainings_count"] = linked_trainings_count
    return response


@router.get("/", summary="Получить планы по параметрам")
async def get_plans(
    user_uuid: str | None = None,
    actual: bool | None = None,
    user_data=Depends(get_current_user_user),
):
    filters = {}
    if user_uuid is not None:
        filters["user_uuid"] = user_uuid
    if actual is not None:
        filters["actual"] = actual
    items = await UserProgramPlanDAO.find_all(**filters)
    return [SUserProgramPlan.model_validate(r) for r in items]


@router.get("/group-for-date", summary="Определить группу тренировки (heavy/light) на дату")
async def api_get_training_group_for_date(
    plan_uuid: str = Query(..., description="UUID плана программы"),
    datetime_iso: str = Query(..., description="Дата/время для расчёта (ISO)"),
    user_data=Depends(get_current_user_user),
):
    try:
        dt = datetime.fromisoformat(datetime_iso.replace("Z", "+00:00"))
    except Exception:
        from datetime import date
        dt = datetime.combine(date.today(), datetime.min.time())
    result = await get_training_group_for_date(plan_uuid, dt)
    return result


@router.get(
    "/type-for-date",
    summary="Определить тип тренировки на дату",
    response_description=(
        "В т.ч. will_update_program_week_on_create: при создании тренировки с ответным training_type "
        "обновится ли current_week_index (для heavy_push — после цикла из трёх heavy). "
        "Без активной подписки (subscription_status=active) в ответе current_week_index=1, "
        "will_update_program_week_on_create=false."
    ),
)
async def api_get_training_type_for_date(
    plan_uuid: str = Query(..., description="UUID плана программы"),
    datetime_iso: str = Query(..., description="Дата/время для расчёта (ISO)"),
    preferred_group: Optional[PreferredTrainingGroup] = Query(
        None,
        description=(
            "Предпочтение группы: heavy или light. Если указано — тип тренировки всегда "
            "из этой группы; алгоритмическая причина остаётся в поле reason (префикс override)."
        ),
    ),
    user_data=Depends(get_current_user_user),
):
    try:
        dt = datetime.fromisoformat(datetime_iso.replace("Z", "+00:00"))
    except Exception:
        from datetime import date
        dt = datetime.combine(date.today(), datetime.min.time())
    pref = preferred_group.value if preferred_group is not None else None
    result = await get_training_type_for_date(plan_uuid, dt, preferred_group=pref, user=user_data)
    return result


class SCreateTraining(BaseModel):
    user_uuid: str
    training_type: str


class SRepeatTraining(BaseModel):
    user_training_uuid: str


@router.post("/create-training", summary="Создать тренировку по программе")
async def api_create_training_by_program(
    body: SCreateTraining,
    user_data=Depends(get_current_user_user),
):
    result = await create_training_by_program(body.user_uuid, body.training_type)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post(
    "/repeat-training",
    summary="Повторить тренировку по плану по user_training",
    response_description="Создаёт копию training и user_training на основе переданного user_training_uuid",
)
async def api_repeat_training_by_user_training(
    body: SRepeatTraining,
    user_data=Depends(get_current_user_user),
):
    """
    Повторить тренировку по плану:
    - Принимает UUID записи user_training.
    - Работает только если у user_training заполнен user_program_plan_id.
    - Создаёт копию training с теми же основными полями и привязкой к тому же плану.
    - Создаёт новую запись user_training, ссылающуюся на новую training.
    """
    from uuid import UUID as _UUID
    from datetime import date

    try:
        ut_uuid = _UUID(body.user_training_uuid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_training_uuid format")

    user_training = await UserTrainingDAO.find_full_data(ut_uuid)

    if not user_training.user_program_plan_id:
        raise HTTPException(
            status_code=400,
            detail="user_training is not linked to user_program_plan (user_program_plan_id is empty)",
        )

    # Проверяем, нет ли уже другой незавершённой тренировки по этому плану
    # (status != PASSED) с заполненным user_program_plan_id для того же пользователя.
    from sqlalchemy import select
    from app.database import async_session_maker
    from app.user_training.models import UserTraining, TrainingStatus

    async with async_session_maker() as session:
        q = (
            select(UserTraining)
            .where(
                UserTraining.user_program_plan_id == user_training.user_program_plan_id,
                UserTraining.user_id == user_training.user_id,
                UserTraining.status != TrainingStatus.PASSED,
            )
        )
        res = await session.execute(q)
        existing_active = res.scalars().first()

    if existing_active:
        raise HTTPException(
            status_code=400,
            detail="Есть незавершенная тренировка в плане",
        )

    if not user_training.training_id:
        raise HTTPException(
            status_code=400,
            detail="user_training has no training_id to repeat",
        )

    # Берём исходную тренировку-шаблон
    original_training = await TrainingDAO.find_one_or_none_by_id(user_training.training_id)
    if not original_training:
        raise HTTPException(status_code=404, detail="Original training not found")

    # Клонируем training
    new_training_uuid = await TrainingDAO.add(
        program_id=original_training.program_id,
        training_type=original_training.training_type,
        user_id=original_training.user_id,
        caption=original_training.caption,
        description=original_training.description,
        difficulty_level=original_training.difficulty_level,
        duration=original_training.duration,
        order=original_training.order,
        muscle_group=original_training.muscle_group,
        stage=original_training.stage,
        image_id=original_training.image_id,
        actual=original_training.actual,
        user_program_plan_id=original_training.user_program_plan_id,
    )
    new_training = await TrainingDAO.find_one_or_none(uuid=new_training_uuid)

    # Клонируем упражнения из исходной тренировки в новую
    from app.exercises.dao import ExerciseDAO

    original_exercises = await ExerciseDAO.find_all(training_uuid=str(original_training.uuid))
    for ex in original_exercises:
        await ExerciseDAO.add(
            exercise_type=ex.exercise_type,
            user_id=ex.user_id,
            caption=ex.caption,
            description=ex.description,
            difficulty_level=ex.difficulty_level,
            pool_difficulty_level=ex.pool_difficulty_level,
            order=ex.order,
            muscle_group=ex.muscle_group,
            sets_count=ex.sets_count,
            reps_count=ex.reps_count,
            rest_time=ex.rest_time,
            with_weight=ex.with_weight,
            weight=ex.weight,
            image_id=ex.image_id,
            video_id=ex.video_id,
            video_preview_id=ex.video_preview_id,
            exercise_reference_id=ex.exercise_reference_id,
            training_id=new_training.id,
            slot_type=ex.slot_type,
            is_time_based=ex.is_time_based,
            duration_seconds=ex.duration_seconds,
        )

    # Создаём новую запись user_training, привязанную к копии training
    today = date.today()
    new_user_training_uuid = await UserTrainingDAO.add(
        user_program_id=user_training.user_program_id,
        program_id=user_training.program_id,
        training_id=new_training.id,
        user_program_plan_id=user_training.user_program_plan_id,
        training_type=user_training.training_type,
        user_id=user_training.user_id,
        training_date=today,
        status="ACTIVE",
        stage=user_training.stage,
        is_rest_day=user_training.is_rest_day,
        week=user_training.week,
        weekday=user_training.weekday,
    )

    return {
        "message": "training_repeated",
        "original_user_training_uuid": str(user_training.uuid),
        "original_training_uuid": str(original_training.uuid),
        "new_training_uuid": str(new_training_uuid),
        "new_user_training_uuid": str(new_user_training_uuid),
    }


@router.get("/actual/user/{user_uuid}", summary="Актуальный план пользователя")
async def get_actual_plan(user_uuid: UUID, user_data=Depends(get_current_user_user)):
    user = await UsersDAO.find_one_or_none(uuid=user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    plan = await UserProgramPlanDAO.find_actual_by_user_id(user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Актуальный план не найден")
    # Загрузить связи для сериализации
    plan = await UserProgramPlanDAO.find_full_data(plan.uuid)
    return SUserProgramPlan.model_validate(plan)


@router.get("/{plan_uuid}", summary="Получить план по uuid")
async def get_plan_by_uuid(plan_uuid: UUID, user_data=Depends(get_current_user_user)):
    try:
        item = await UserProgramPlanDAO.find_full_data(plan_uuid)
        return SUserProgramPlan.model_validate(item)
    except HTTPException as e:
        if e.status_code == 404:
            return {"message": f"План с uuid {plan_uuid} не найден!"}
        raise


@router.put("/update/{plan_uuid}", summary="Обновить план")
async def update_plan(plan_uuid: UUID, body: SUserProgramPlanUpdate, user_data=Depends(get_current_user_user)):
    values = body.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    await UserProgramPlanDAO.update(plan_uuid, **values)
    item = await UserProgramPlanDAO.find_full_data(plan_uuid)
    return {"message": "План обновлён", "plan": SUserProgramPlan.model_validate(item)}


@router.put("/deactualize/{plan_uuid}", summary="Деактуализировать план")
async def deactualize_plan(plan_uuid: UUID, user_data=Depends(get_current_user_user)):
    plan = await UserProgramPlanDAO.find_one_or_none(uuid=plan_uuid)
    if not plan:
        raise HTTPException(status_code=404, detail="План не найден")
    await UserProgramPlanDAO.update(plan_uuid, actual=False)
    return {"message": "План деактуализирован", "plan_uuid": str(plan_uuid)}


@router.delete("/delete/{plan_uuid}", summary="Удалить план")
async def delete_plan(plan_uuid: UUID, user_data=Depends(get_current_user_user)):
    await UserProgramPlanDAO.delete_by_id(plan_uuid)
    return {"message": f"План {plan_uuid} удалён"}
