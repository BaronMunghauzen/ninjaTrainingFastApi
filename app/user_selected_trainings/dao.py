from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.trainings.dao import TrainingDAO
from app.trainings.models import Training
from app.user_selected_trainings.models import UserSelectedTraining
from app.users.dao import UsersDAO


class UserSelectedTrainingDAO(BaseDAO):
    model = UserSelectedTraining
    uuid_fk_map = {
        "user_id": (UsersDAO, "user_uuid"),
        "training_id": (TrainingDAO, "training_uuid"),
    }

    @classmethod
    async def delete_for_user_by_training_uuid(cls, user_id: int, training_uuid: UUID) -> None:
        training = await TrainingDAO.find_one_or_none(uuid=training_uuid)
        if not training:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тренировка не найдена",
            )
        async with async_session_maker() as session:
            async with session.begin():
                result = await session.execute(
                    delete(cls.model).where(
                        cls.model.user_id == user_id,
                        cls.model.training_id == training.id,
                    )
                )
                if result.rowcount == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Запись о выборе этой тренировки не найдена",
                    )

    @classmethod
    async def get_selected_training_ids_for_user(cls, user_id: int) -> set[int]:
        """training_id, для которых у пользователя есть строка в user_selected_trainings."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(cls.model.training_id).where(cls.model.user_id == user_id)
            )
            return set(result.scalars().all())

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.training).joinedload(Training.image),
                )
                .filter_by(uuid=object_uuid)
            )
            result = await session.execute(query)
            result = result.unique()
            object_info = result.scalar_one_or_none()
            if not object_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Объект {cls.model.__name__} с uuid {object_uuid} не найден",
                )
            session.expunge(object_info)
            return object_info

    @classmethod
    async def find_all(cls, **filter_by):
        filters = filter_by.copy()
        for fk_field, (related_dao, uuid_field) in getattr(cls, "uuid_fk_map", {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                if uuid_value is not None:
                    related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                    if related_obj:
                        filters[fk_field] = related_obj.id
                    else:
                        return []
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.training).joinedload(Training.image),
                )
                .filter_by(**filters)
            )
            result = await session.execute(query)
            result = result.unique()
            objects = result.scalars().all()
            for obj in objects:
                session.expunge(obj)
            return objects
