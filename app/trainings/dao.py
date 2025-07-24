from app.dao.base import BaseDAO
from app.trainings.models import Training
from app.programs.dao import ProgramDAO
from app.exercises.dao import ExerciseDAO
from app.files.dao import FilesDAO
from app.database import async_session_maker
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
from uuid import UUID
from app.programs.models import Program


class TrainingDAO(BaseDAO):
    model = Training
    uuid_fk_map = {
        'program_id': (ProgramDAO, 'program_uuid'),
        'main_exercise_id': (ExerciseDAO, 'exercise_uuid'),
        'image_id': (FilesDAO, 'image_uuid')
    }

    @classmethod
    async def find_by_program_and_stage(cls, program_id: int | None, stage: int):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(stage=stage)
            if program_id is not None:
                query = query.filter_by(program_id=program_id)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.program).joinedload(Program.image)
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
                joinedload(cls.model.program),
                joinedload(cls.model.user),
                joinedload(cls.model.exercise_groups),
                joinedload(cls.model.user_trainings),
                joinedload(cls.model.user_exercises)
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
                joinedload(cls.model.program).joinedload(Program.image)
            ).filter_by(**filters)
            if hasattr(cls.model, 'order'):
                query = query.order_by(cls.model.order.asc())
            result = await session.execute(query)
            result = result.unique()
            objects = result.scalars().all()
            return objects
