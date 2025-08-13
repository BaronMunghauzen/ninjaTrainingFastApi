from app.dao.base import BaseDAO
from app.user_exercises.models import UserExercise
from app.programs.dao import ProgramDAO
from app.trainings.dao import TrainingDAO
from app.users.dao import UsersDAO
from app.exercises.dao import ExerciseDAO
from app.database import async_session_maker
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.programs.models import Program
from app.trainings.models import Training
from app.users.models import User
from app.exercises.models import Exercise
from uuid import UUID


class UserExerciseDAO(BaseDAO):
    model = UserExercise
    uuid_fk_map = {
        'program_id': (ProgramDAO, 'program_uuid'),
        'training_id': (TrainingDAO, 'training_uuid'),
        'user_id': (UsersDAO, 'user_uuid'),
        'exercise_id': (ExerciseDAO, 'exercise_uuid')
    }

    @classmethod
    async def find_all_with_relations(cls, **filter_by):
        """Оптимизированный метод для загрузки user_exercises с предзагруженными связанными данными"""
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
                joinedload(cls.model.program).joinedload(Program.image),
                joinedload(cls.model.training).joinedload(Training.image),
                joinedload(cls.model.user),
                joinedload(cls.model.exercise).joinedload(Exercise.image),
                joinedload(cls.model.exercise).joinedload(Exercise.video),
                joinedload(cls.model.exercise).joinedload(Exercise.video_preview),
                joinedload(cls.model.exercise).joinedload(Exercise.exercise_reference)
            ).filter_by(**filters)
            
            if hasattr(cls.model, 'order'):
                query = query.order_by(cls.model.order.asc())
            
            result = await session.execute(query)
            result = result.unique()
            objects = result.scalars().all()
            return objects

    @classmethod
    async def find_full_data_with_relations(cls, object_uuid: UUID):
        """Оптимизированный метод для загрузки одного user_exercise с предзагруженными связанными данными"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.program).joinedload(Program.image),
                joinedload(cls.model.training).joinedload(Training.image),
                joinedload(cls.model.user),
                joinedload(cls.model.exercise).joinedload(Exercise.image),
                joinedload(cls.model.exercise).joinedload(Exercise.video),
                joinedload(cls.model.exercise).joinedload(Exercise.video_preview),
                joinedload(cls.model.exercise).joinedload(Exercise.exercise_reference)
            ).filter_by(uuid=object_uuid)
            
            result = await session.execute(query)
            result = result.unique()
            object_info = result.scalar_one_or_none()
            
            if not object_info:
                return None
            
            return object_info
