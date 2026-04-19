from datetime import date
from typing import Optional, TYPE_CHECKING

from uuid import UUID

from app.user_program_plan.models import UserProgramPlan
from app.user_program_plan.dao import UserProgramPlanDAO
from app.trainings.dao import TrainingDAO
from app.exercises.dao import ExerciseDAO
from app.training_composition_rules.dao import TrainingCompositionRuleDAO
from app.user_program_plan.training_builder import build_training_exercises
from app.exercise_reference.dao import ExerciseReferenceDAO
from app.database import async_session_maker
from sqlalchemy import select
from app.trainings.models import Training
from app.user_training.models import UserTraining, TrainingStatus
from app.user_exercises.models import UserExercise
from app.user_training.dao import UserTrainingDAO
from app.user_exercises.dao import UserExerciseDAO

if TYPE_CHECKING:
    from app.users.models import User


async def create_anonymous_pull_training(
    *,
    anonymous_session_id: UUID,
    difficulty_level: str,
    program_goal: str,
    train_at_gym: bool,
    train_at_home: bool,
    train_at_home_no_equipment: bool,
    has_dumbbells: bool,
    has_pullup_bar: bool,
    has_bands: bool,
    duration_target_minutes: int,
    training_days_per_week: int,
    current_user: Optional["User"] = None,
) -> dict:
    """
    Создание heavy_pull для анонимной сессии (или залогиненного пользователя).

    Если передан current_user и у него есть актуальный план — тренировка и сборка
    идут по этому плану (user_program_plan_id = актуальный план, user_id = пользователь).

    Иначе создаётся временный план с anonymous_session_id (для attach-session).
    """
    training_type = "heavy_pull"
    builder_user_id: Optional[int] = current_user.id if current_user else None

    # Если в этой анонимной сессии уже есть хотя бы одна training и хотя бы одна user_training,
    # считаем прошлые user_training "устаревшими" и переводим в SKIPPED.
    async with async_session_maker() as session:
        existing_trainings = await session.execute(
            select(Training.id).where(Training.anonymous_session_id == anonymous_session_id).limit(1)
        )
        has_training_for_session = existing_trainings.scalar_one_or_none() is not None

        existing_user_trainings = await session.execute(
            select(UserTraining).where(UserTraining.anonymous_session_id == anonymous_session_id)
        )
        user_trainings_for_session = existing_user_trainings.scalars().all()
        if has_training_for_session and user_trainings_for_session:
            for ut in user_trainings_for_session:
                ut.status = TrainingStatus.SKIPPED
            await session.commit()

    # 1. План: актуальный план пользователя (если авторизован) или временный анонимный
    plan: UserProgramPlan | None = None
    if current_user:
        actual_row = await UserProgramPlanDAO.find_actual_by_user_id(current_user.id)
        if actual_row:
            plan = await UserProgramPlanDAO.find_full_data(actual_row.uuid)

    if plan is None:
        plan_uuid = await UserProgramPlanDAO.add(
            user_uuid=None,
            anonymous_session_id=anonymous_session_id,
            train_at_gym=train_at_gym,
            train_at_home=train_at_home,
            train_at_home_no_equipment=train_at_home_no_equipment,
            has_dumbbells=has_dumbbells,
            has_pullup_bar=has_pullup_bar,
            has_bands=has_bands,
            duration_target_minutes=duration_target_minutes,
            difficulty_level=difficulty_level,
            program_goal=program_goal,
            start_date=date.today(),
            training_days_per_week=training_days_per_week,
            current_week_index=1,
            completed_heavy_training_count=0,
            actual=True,
        )
        plan = await UserProgramPlanDAO.find_one_or_none(uuid=plan_uuid)
    if not plan:
        return {
            "error": "plan_creation_failed",
            "training_type": training_type,
            "training_uuid": None,
            "exercises": [],
        }

    # 2. Подбираем правило состава
    all_rules = await TrainingCompositionRuleDAO.find_all(actual=True)
    rule = None
    for r in all_rules:
        if (
            (r.training_type or "").strip().lower() == training_type
            and (r.program_goal or "").strip().lower() == (plan.program_goal or "").strip().lower()
            and r.program_week_index == (plan.current_week_index or 1)
            and r.duration_target_minutes == plan.duration_target_minutes
        ):
            rule = r
            break
    if not rule:
        return {
            "error": "no_matching_rule",
            "training_type": training_type,
            "training_uuid": None,
            "exercises": [],
        }

    # 3. Создаём training
    caption = f"{training_type} ({plan.program_goal})"
    training_user_uuid = str(current_user.uuid) if current_user else None
    training_uuid = await TrainingDAO.add(
        program_uuid=None,
        training_type=training_type,
        user_uuid=training_user_uuid,
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
        anonymous_session_id=str(anonymous_session_id),
    )
    training_obj = await TrainingDAO.find_one_or_none(uuid=training_uuid)
    if not training_obj:
        return {
            "error": "training_creation_failed",
            "training_type": training_type,
            "training_uuid": None,
            "exercises": [],
        }

    # 4. Сборка упражнений
    exercise_items, limb, anchor_uuids_to_save = await build_training_exercises(
        plan, rule, training_type, user_id=builder_user_id, plan_id=plan.id
    )

    created_exercise_uuids = []
    order_idx = 0
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
        ex_uuid = await ExerciseDAO.add(
            exercise_type="strength",
            caption=item["caption"],
            muscle_group=p.primary_muscle_group or "",
            difficulty_level=1,
            pool_difficulty_level=pool_dl_str,
            order=order_idx,
            slot_type=item.get("role"),
            sets_count=sets_val,
            reps_count=reps_max,
            rest_time=rest_val,
            with_weight=bool(getattr(p, "uses_external_load", True)),
            weight=None,
            exercise_reference_uuid=ref_uuid,
            training_uuid=str(training_uuid),
        )
        created_exercise_uuids.append(str(ex_uuid))
        order_idx += 1

    # 5. Сохраняем якоря в плане
    if limb and anchor_uuids_to_save:
        update_payload = {
            f"anchor1_for_{limb}_uuid": anchor_uuids_to_save[0] if len(anchor_uuids_to_save) > 0 else None,
            f"anchor2_for_{limb}_uuid": anchor_uuids_to_save[1] if len(anchor_uuids_to_save) > 1 else None,
        }
        await UserProgramPlanDAO.update(plan.uuid, **update_payload)

    return {
        "training_type": training_type,
        "training_uuid": str(training_uuid),
        "exercises": created_exercise_uuids,
    }


async def attach_anonymous_session_to_user(
    anonymous_session_id: UUID,
    user_id: int,
) -> dict:
    """
    Привязать все анонимные тренировки/прохождения/подходы и планы программы к пользователю.
    - user_program_plan.user_id = user_id, anonymous_session_id = NULL
    - training.user_id = user_id, anonymous_session_id = NULL
    - user_training.user_id = user_id, anonymous_session_id = NULL
    - user_exercise.user_id = user_id (по training_id), если сейчас NULL
    """
    updated_trainings = 0
    updated_user_trainings = 0
    updated_user_exercises = 0
    updated_user_program_plans = 0

    async with async_session_maker() as session:
        async with session.begin():
            # 0. Планы программы по anonymous_session_id
            q_plans = await session.execute(
                select(UserProgramPlan).where(
                    UserProgramPlan.anonymous_session_id == anonymous_session_id
                )
            )
            plans = q_plans.scalars().all()
            for p in plans:
                p.user_id = user_id
                p.anonymous_session_id = None
                updated_user_program_plans += 1

            # 1. Training по anonymous_session_id
            q_tr = await session.execute(
                select(Training).where(
                    Training.anonymous_session_id == anonymous_session_id
                )
            )
            trainings = q_tr.scalars().all()
            training_ids = [t.id for t in trainings]
            for t in trainings:
                t.user_id = user_id
                t.anonymous_session_id = None
                updated_trainings += 1

            # 2. UserTraining по anonymous_session_id
            q_ut = await session.execute(
                select(UserTraining).where(
                    UserTraining.anonymous_session_id == anonymous_session_id
                )
            )
            uts = q_ut.scalars().all()
            for ut in uts:
                ut.user_id = user_id
                ut.anonymous_session_id = None
                updated_user_trainings += 1

            # 3. UserExercise по training_id и user_id IS NULL
            if training_ids:
                q_ue = await session.execute(
                    select(UserExercise).where(
                        UserExercise.training_id.in_(training_ids),
                        UserExercise.user_id.is_(None),
                    )
                )
                ues = q_ue.scalars().all()
                for ue in ues:
                    ue.user_id = user_id
                    updated_user_exercises += 1

    return {
        "anonymous_session_id": str(anonymous_session_id),
        "user_id": user_id,
        "updated_user_program_plans": updated_user_program_plans,
        "updated_trainings": updated_trainings,
        "updated_user_trainings": updated_user_trainings,
        "updated_user_exercises": updated_user_exercises,
    }


async def create_anonymous_user_training(
    *,
    anonymous_session_id: UUID,
    training_uuid: str,
    training_date: Optional[date],
    status: str,
    training_type: Optional[str],
    current_user: Optional["User"] = None,
) -> str:
    """
    Создать user_training для анонимной сессии.

    user_program_plan_id: с training (если есть), иначе актуальный план залогиненного пользователя.
    user_id: если передан current_user — проставляется.
    """
    if training_date is None:
        training_date = date.today()

    t_uuid = UUID(training_uuid) if isinstance(training_uuid, str) else training_uuid
    training_obj = await TrainingDAO.find_one_or_none(uuid=t_uuid)

    user_program_plan_uuid: Optional[str] = None
    if training_obj and training_obj.user_program_plan_id:
        pp = await UserProgramPlanDAO.find_one_or_none_by_id(training_obj.user_program_plan_id)
        if pp:
            user_program_plan_uuid = str(pp.uuid)
    if user_program_plan_uuid is None and current_user:
        ap = await UserProgramPlanDAO.find_actual_by_user_id(current_user.id)
        if ap:
            user_program_plan_uuid = str(ap.uuid)

    ut_user_uuid = str(current_user.uuid) if current_user else None

    user_training_uuid = await UserTrainingDAO.add(
        user_uuid=ut_user_uuid,
        program_uuid=None,
        training_uuid=training_uuid,
        user_program_plan_uuid=user_program_plan_uuid,
        training_date=training_date,
        status=status,
        training_type=training_type,
        anonymous_session_id=str(anonymous_session_id),
        is_rest_day=False,
    )
    return str(user_training_uuid)


async def create_anonymous_user_exercise(
    *,
    anonymous_session_id: UUID,
    training_uuid: str,
    exercise_uuid: str,
    program_uuid: Optional[str],
    training_date: Optional[date],
    status: str,
    set_number: int,
    weight: Optional[float],
    reps: int,
    duration_seconds: Optional[int] = None,
) -> str:
    """
    Создать запись user_exercise для анонимной сессии (user_id NULL, anonymous_session_id задан).
    """
    if training_date is None:
        training_date = date.today()

    ue_uuid = await UserExerciseDAO.add(
        anonymous_session_id=str(anonymous_session_id),
        program_uuid=program_uuid,
        training_uuid=training_uuid,
        user_uuid=None,
        exercise_uuid=exercise_uuid,
        training_date=training_date,
        status=status,
        set_number=set_number,
        weight=weight,
        reps=reps,
        duration_seconds=duration_seconds,
    )
    return str(ue_uuid)
