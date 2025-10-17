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
    
    @classmethod
    async def batch_set_passed(cls, user_exercise_uuids: list[UUID]):
        """
        Batch установка статуса PASSED для множества user_exercises
        
        Args:
            user_exercise_uuids: Список UUID пользовательских упражнений
            
        Returns:
            dict: Результат операции с детальной информацией
        """
        from app.user_exercises.models import ExerciseStatus
        
        success_uuids = []
        failed_uuids = []
        errors = []
        
        async with async_session_maker() as session:
            try:
                async with session.begin():
                    # Получаем все объекты одним запросом
                    query = select(cls.model).where(cls.model.uuid.in_(user_exercise_uuids))
                    result = await session.execute(query)
                    existing_exercises = {ex.uuid: ex for ex in result.scalars().all()}
                    
                    # Проверяем какие UUID существуют
                    existing_uuids = set(existing_exercises.keys())
                    missing_uuids = set(user_exercise_uuids) - existing_uuids
                    
                    if missing_uuids:
                        failed_uuids.extend(missing_uuids)
                        errors.append(f"Не найдены упражнения с UUID: {list(missing_uuids)}")
                    
                    # Обновляем существующие упражнения
                    for uuid in existing_uuids:
                        exercise = existing_exercises[uuid]
                        if exercise.status != ExerciseStatus.PASSED:
                            exercise.status = ExerciseStatus.PASSED
                            success_uuids.append(uuid)
                        else:
                            # Уже PASSED - считаем успешным
                            success_uuids.append(uuid)
                    
                    await session.commit()
                    
            except Exception as e:
                await session.rollback()
                failed_uuids.extend(user_exercise_uuids)
                errors.append(f"Ошибка batch обновления: {str(e)}")
                success_uuids = []
        
        return {
            'success_count': len(success_uuids),
            'failed_count': len(failed_uuids),
            'total_count': len(user_exercise_uuids),
            'success_uuids': success_uuids,
            'failed_uuids': failed_uuids,
            'errors': errors
        }