from app.dao.base import BaseDAO
from app.programs.models import Program
from app.categories.dao import CategoryDAO
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.database import async_session_maker
from fastapi import HTTPException, status
from uuid import UUID

class ProgramDAO(BaseDAO):
    model = Program
    uuid_fk_map = {
        'category_id': (CategoryDAO, 'category_uuid'),
        'user_id': (UsersDAO, 'user_uuid'),
        'image_id': (FilesDAO, 'image_uuid')
    }

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.user_trainings),
                joinedload(cls.model.user_exercises),
                joinedload(cls.model.trainings),
                joinedload(cls.model.user_programs),
                joinedload(cls.model.category),
                joinedload(cls.model.user)
            ).filter_by(uuid=object_uuid)
            result = await session.execute(query)
            result = result.unique()
            object_info = result.scalar_one_or_none()
            if not object_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Объект {cls.model.__name__} с ID {object_uuid} не найден"
                )
            return object_info

    @classmethod
    async def find_full_data_by_id(cls, object_id: int):
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.user_trainings),
                joinedload(cls.model.user_exercises),
                joinedload(cls.model.trainings),
                joinedload(cls.model.user_programs),
                joinedload(cls.model.category),
                joinedload(cls.model.user)
            ).filter_by(id=object_id)
            result = await session.execute(query)
            result = result.unique()
            object_info = result.scalar_one_or_none()
            if not object_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Объект {cls.model.__name__} с ID {object_id} не найден"
                )
            return object_info

    @classmethod
    async def find_all(cls, **filter_by):
        filters = filter_by.copy()
        for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                if related_obj:
                    filters[fk_field] = related_obj.id
                else:
                    return []
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.user_trainings),
                joinedload(cls.model.user_exercises),
                joinedload(cls.model.trainings),
                joinedload(cls.model.user_programs),
                joinedload(cls.model.category),
                joinedload(cls.model.user)
            ).filter_by(**filters)
            if hasattr(cls.model, 'order'):
                query = query.order_by(cls.model.order.asc())
            result = await session.execute(query)
            result = result.unique()
            objects = result.scalars().all()
            return objects
