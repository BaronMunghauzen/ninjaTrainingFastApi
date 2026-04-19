from app.dao.base import BaseDAO
from app.user_program_plan.models import UserProgramPlan
from app.users.dao import UsersDAO
from app.exercise_builder_pool.dao import ExerciseBuilderPoolDAO
from app.database import async_session_maker
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
from uuid import UUID


class UserProgramPlanDAO(BaseDAO):
    model = UserProgramPlan
    uuid_fk_map = {
        "user_id": (UsersDAO, "user_uuid"),
        "anchor1_for_pull_id": (ExerciseBuilderPoolDAO, "anchor1_for_pull_uuid"),
        "anchor2_for_pull_id": (ExerciseBuilderPoolDAO, "anchor2_for_pull_uuid"),
        "anchor1_for_push_id": (ExerciseBuilderPoolDAO, "anchor1_for_push_uuid"),
        "anchor2_for_push_id": (ExerciseBuilderPoolDAO, "anchor2_for_push_uuid"),
        "anchor1_for_legs_id": (ExerciseBuilderPoolDAO, "anchor1_for_legs_uuid"),
        "anchor2_for_legs_id": (ExerciseBuilderPoolDAO, "anchor2_for_legs_uuid"),
    }

    @classmethod
    async def find_actual_by_user_id(cls, user_id: int):
        """Актуальный план программы по user_id."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(cls.model).filter_by(user_id=user_id, actual=True)
            )
            obj = result.scalar_one_or_none()
            if obj:
                session.expunge(obj)
            return obj

    @classmethod
    async def deactualize_by_user_id(cls, user_id: int) -> int:
        """Деактуализировать все планы пользователя. Возвращает количество обновлённых."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(cls.model).filter_by(user_id=user_id, actual=True)
            )
            plans = result.scalars().all()
            for p in plans:
                p.actual = False
            await session.commit()
            return len(plans)

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        """План по uuid с загрузкой связей для ответа (user_uuid, anchor*_uuid)."""
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.anchor1_for_pull),
                    joinedload(cls.model.anchor2_for_pull),
                    joinedload(cls.model.anchor1_for_push),
                    joinedload(cls.model.anchor2_for_push),
                    joinedload(cls.model.anchor1_for_legs),
                    joinedload(cls.model.anchor2_for_legs),
                )
                .filter_by(uuid=object_uuid)
            )
            result = await session.execute(query)
            result = result.unique()
            obj = result.scalar_one_or_none()
            if not obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Объект {cls.model.__name__} с uuid {object_uuid} не найден"
                )
            session.expunge(obj)
            return obj
