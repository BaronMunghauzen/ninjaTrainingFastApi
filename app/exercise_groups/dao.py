from app.dao.base import BaseDAO
from app.exercise_groups.models import ExerciseGroup
from app.trainings.dao import TrainingDAO
from app.files.dao import FilesDAO
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.database import async_session_maker
from fastapi import HTTPException, status
from uuid import UUID
from app.trainings.models import Training

class ExerciseGroupDAO(BaseDAO):
    model = ExerciseGroup
    uuid_fk_map = {
        'training_id': (TrainingDAO, 'training_uuid'),
        'image_id': (FilesDAO, 'image_uuid')
    }

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.training).joinedload(Training.image)
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
                joinedload(cls.model.training).joinedload(Training.image)
            ).filter_by(**filters)
            result = await session.execute(query)
            result = result.unique()
            objects = result.scalars().all()
            return objects 