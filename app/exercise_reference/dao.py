from app.dao.base import BaseDAO
from app.exercise_reference.models import ExerciseReference
from app.files.dao import FilesDAO
from app.users.dao import UsersDAO
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.database import async_session_maker
from fastapi import HTTPException, status
from uuid import UUID
from sqlalchemy import select, or_, func

class ExerciseReferenceDAO(BaseDAO):
    model = ExerciseReference
    uuid_fk_map = {
        'image_id': (FilesDAO, 'image_uuid'),
        'user_id': (UsersDAO, 'user_uuid')
    }

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.user)
            ).filter_by(uuid=object_uuid)
            result = await session.execute(query)
            object_info = result.scalar_one_or_none()
            if not object_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Объект {cls.model.__name__} с ID {object_uuid} не найден"
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
                joinedload(cls.model.user)
            ).filter_by(**filters)
            result = await session.execute(query)
            objects = result.scalars().all()
            return objects

    @classmethod
    async def find_by_caption(cls, * , caption: str, **filter_by):
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
                joinedload(cls.model.user)
            ).filter(
                func.lower(cls.model.caption).like(f"%{caption.lower()}%"),
                *[getattr(cls.model, k) == v for k, v in filters.items()]
            )
            result = await session.execute(query)
            objects = result.scalars().all()
            return objects

    @classmethod
    async def search_by_caption(cls, *, search_query: str, user_id: int):
        """Поиск по caption с учетом exercise_type и user_id"""
        from sqlalchemy import or_
        
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.user)
            ).filter(
                func.lower(cls.model.caption).like(f"%{search_query.lower()}%"),
                or_(
                    cls.model.exercise_type == "system",
                    (cls.model.exercise_type == "user") & (cls.model.user_id == user_id)
                )
            )
            result = await session.execute(query)
            objects = result.scalars().all()
            return objects 