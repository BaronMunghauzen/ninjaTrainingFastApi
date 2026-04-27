from fastapi import APIRouter, HTTPException, status, Depends
from uuid import UUID

from app.anonymous_session.dao import AnonymousSessionDAO
from app.public_training.schemas import (
    SAnonymousSessionCreateResponse,
    SPublicTrainingCreateRequest,
    SPublicTrainingCreateResponse,
    SPublicExercise,
    SPublicTrainingWithExercises,
    SPublicUserTrainingCreateRequest,
    SPublicUserExerciseCreateRequest,
    SPublicUserTrainingSummaryResponse,
)
from app.public_training.service import (
    create_anonymous_pull_training,
    attach_anonymous_session_to_user,
    create_anonymous_user_training,
    create_anonymous_user_exercise,
)
from app.exercises.dao import ExerciseDAO
from app.trainings.dao import TrainingDAO
from app.user_training.dao import UserTrainingDAO
from app.user_training.models import TrainingStatus
from app.users.dependencies import get_current_user_user, get_optional_current_user_user
from app.users.models import User
from app.telegram_service import telegram_service
from app.logger import logger


router = APIRouter(prefix="/public-training", tags=["public-training"])


@router.post(
    "/anonymous-session",
    response_model=SAnonymousSessionCreateResponse,
    summary="Создать анонимную сессию",
)
async def create_anonymous_session() -> SAnonymousSessionCreateResponse:
    """Регистрирует новый anonymous_session_id в БД и возвращает его клиенту."""
    aid = await AnonymousSessionDAO.create_session()
    try:
        await telegram_service.send_message(
            "👤 <b>Создана анонимная сессия</b>\n"
            f"🆔 anonymous_session_id: <code>{aid}</code>"
        )
    except Exception as exc:
        # Не блокируем API-ответ из-за внешнего уведомления.
        logger.warning(f"Failed to send telegram notification for anonymous session {aid}: {exc}")
    return SAnonymousSessionCreateResponse(anonymous_session_id=aid)


@router.post("/create-pull", response_model=SPublicTrainingCreateResponse)
async def create_public_pull_training(
    payload: SPublicTrainingCreateRequest,
    current_user: User | None = Depends(get_optional_current_user_user),
) -> SPublicTrainingCreateResponse:
    """
    Создание heavy_pull для анонимной сессии или (с cookie авторизации) с привязкой
    к актуальному плану пользователя.
    """
    result = await create_anonymous_pull_training(
        anonymous_session_id=payload.anonymous_session_id,
        difficulty_level=payload.difficulty_level,
        program_goal=payload.program_goal,
        train_at_gym=payload.train_at_gym,
        train_at_home=payload.train_at_home,
        train_at_home_no_equipment=payload.train_at_home_no_equipment,
        has_dumbbells=payload.has_dumbbells,
        has_pullup_bar=payload.has_pullup_bar,
        has_bands=payload.has_bands,
        duration_target_minutes=payload.duration_target_minutes,
        training_days_per_week=payload.training_days_per_week,
        current_user=current_user,
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    # Загружаем упражнения по uuid, чтобы отдать фронту все нужные поля
    exercises: list[SPublicExercise] = []
    for ex_uuid in result["exercises"]:
        ex = await ExerciseDAO.find_one_or_none(uuid=ex_uuid)
        if not ex:
            continue
        exercises.append(
            SPublicExercise(
                exercise_uuid=str(ex.uuid),
                caption=ex.caption,
                muscle_group=ex.muscle_group,
                sets_count=ex.sets_count,
                reps_count=ex.reps_count,
                rest_time=ex.rest_time,
            )
        )

    return SPublicTrainingCreateResponse(
        anonymous_session_id=payload.anonymous_session_id,
        training_type=result["training_type"],
        training_uuid=result["training_uuid"],
        exercises=exercises,
    )


@router.get(
    "/trainings/by-session/{anonymous_session_id}",
    response_model=SPublicTrainingWithExercises | None,
)
async def get_trainings_by_anonymous_session(anonymous_session_id: UUID):
    """
    Получить только самую последнюю тренировку и её упражнения для anonymous_session_id.
    """
    trainings = await TrainingDAO.find_all(anonymous_session_id=str(anonymous_session_id))
    if not trainings:
        return None

    # Берем самую последнюю по created_at (fallback: id)
    last_training = max(trainings, key=lambda t: (t.created_at or t.updated_at, t.id))

    exs = await ExerciseDAO.find_all(training_uuid=str(last_training.uuid))
    exercises: list[SPublicExercise] = [
        SPublicExercise(
            exercise_uuid=str(ex.uuid),
            caption=ex.caption,
            muscle_group=ex.muscle_group,
            sets_count=ex.sets_count,
            reps_count=ex.reps_count,
            rest_time=ex.rest_time,
        )
        for ex in exs
    ]
    return SPublicTrainingWithExercises(
        training_uuid=str(last_training.uuid),
        training_type=last_training.training_type,
        caption=last_training.caption,
        description=last_training.description,
        difficulty_level=last_training.difficulty_level,
        duration=last_training.duration,
        muscle_group=last_training.muscle_group,
        stage=last_training.stage,
        actual=last_training.actual,
        # Не трогаем отношения (объекты отсоединены от сессии), используем только простые поля.
        user_program_plan_uuid=None,
        anonymous_session_id=str(anonymous_session_id),
        exercises=exercises,
    )


@router.get("/user-trainings/by-session/{anonymous_session_id}")
async def get_user_trainings_by_anonymous_session(anonymous_session_id: UUID):
    """
    Получить user_training по anonymous_session_id, исключая статус SKIPPED.
    """
    uts = await UserTrainingDAO.find_all(anonymous_session_id=str(anonymous_session_id))
    return [ut.to_dict() for ut in uts if ut.status != TrainingStatus.SKIPPED]


@router.post("/attach-session/{anonymous_session_id}")
async def attach_session_to_user(anonymous_session_id: UUID, current_user: User = Depends(get_current_user_user)):
    """
    Преобразовать анонимные user_program_plan, тренировки, user_training и user_exercise
    с данным anonymous_session_id к текущему пользователю.
    """
    result = await attach_anonymous_session_to_user(anonymous_session_id, current_user.id)
    return result


@router.post("/user-training/create-anonymous")
async def create_anonymous_user_training_endpoint(
    payload: SPublicUserTrainingCreateRequest,
    current_user: User | None = Depends(get_optional_current_user_user),
):
    """
    Создать user_training для анонимной сессии; user_program_plan_id — с training или актуальный план (с cookie).
    """
    from datetime import date as _date

    training_date = (
        _date.fromisoformat(payload.training_date) if payload.training_date else None
    )
    ut_uuid = await create_anonymous_user_training(
        anonymous_session_id=payload.anonymous_session_id,
        training_uuid=payload.training_uuid,
        training_date=training_date,
        status=payload.status,
        training_type=payload.training_type,
        current_user=current_user,
    )
    return {"user_training_uuid": ut_uuid}


@router.post("/user-exercise/create-anonymous")
async def create_anonymous_user_exercise_endpoint(payload: SPublicUserExerciseCreateRequest):
    """
    Создать user_exercise (подход) для анонимной сессии.
    """
    from datetime import date as _date

    training_date = (
        _date.fromisoformat(payload.training_date) if payload.training_date else None
    )
    ue_uuid = await create_anonymous_user_exercise(
        anonymous_session_id=payload.anonymous_session_id,
        training_uuid=payload.training_uuid,
        exercise_uuid=payload.exercise_uuid,
        program_uuid=payload.program_uuid,
        training_date=training_date,
        status=payload.status,
        set_number=payload.set_number,
        weight=payload.weight,
        reps=payload.reps,
        duration_seconds=payload.duration_seconds,
    )
    return {"user_exercise_uuid": ue_uuid}


@router.post("/user-training/{user_training_uuid}/summary", response_model=SPublicUserTrainingSummaryResponse)
async def get_user_training_summary(user_training_uuid: UUID):
    """
    Подвести итоги тренировки по user_training_uuid:
    - длительность (completed_at - created_at)
    - количество выполненных упражнений
    - количество подходов и повторений по каждому упражнению
    - общий тоннаж
    """
    from app.user_training.summary_service import build_user_training_summary

    result = await build_user_training_summary(user_training_uuid=user_training_uuid)
    if result.get("error") == "user_training_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User training not found")
    if result.get("error") == "training_id_not_found":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User training has no training_id")
    return result

