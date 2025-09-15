from app.dao.base import BaseDAO
from app.exercise_reference.models import ExerciseReference
from app.files.dao import FilesDAO
from app.users.dao import UsersDAO
from app.exercises.models import Exercise
from app.user_exercises.models import UserExercise, ExerciseStatus
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
        'video_id': (FilesDAO, 'video_uuid'),
        'gif_id': (FilesDAO, 'gif_uuid'),
        'user_id': (UsersDAO, 'user_uuid')
    }

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.video),
                joinedload(cls.model.gif),
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
                joinedload(cls.model.video),
                joinedload(cls.model.gif),
                joinedload(cls.model.user)
            ).filter_by(**filters)
            result = await session.execute(query)
            objects = result.scalars().all()
            return objects

    @classmethod
    async def find_all_paginated(cls, *, page: int = 1, size: int = 20, **filter_by):
        """Получение всех элементов с пагинацией"""
        filters = filter_by.copy()
        for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                if related_obj:
                    filters[fk_field] = related_obj.id
                else:
                    return {"items": [], "total": 0, "page": page, "size": size, "pages": 0}
        
        async with async_session_maker() as session:
            # Базовый запрос для подсчета общего количества
            count_query = select(func.count(cls.model.id)).filter_by(**filters)
            
            # Запрос для получения данных
            data_query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.video),
                joinedload(cls.model.gif),
                joinedload(cls.model.user)
            ).filter_by(**filters)
            
            # Если пагинация не нужна (page=0 или size=0), возвращаем все элементы
            if page == 0 or size == 0:
                data_result = await session.execute(data_query)
                objects = data_result.scalars().all()
                total = len(objects)
                return {
                    "items": objects,
                    "total": total,
                    "page": 0,
                    "size": 0,
                    "pages": 1
                }
            
            # Добавляем пагинацию
            data_query = data_query.offset((page - 1) * size).limit(size)
            
            # Выполняем запросы
            count_result = await session.execute(count_query)
            total = count_result.scalar()
            
            data_result = await session.execute(data_query)
            objects = data_result.scalars().all()
            
            # Вычисляем количество страниц
            pages = (total + size - 1) // size if total > 0 else 0
            
            return {
                "items": objects,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages
            }

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
                joinedload(cls.model.video),
                joinedload(cls.model.gif),
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
                joinedload(cls.model.video),
                joinedload(cls.model.gif),
                joinedload(cls.model.user)
            ).filter(
                or_(
                    cls.model.exercise_type == "system",
                    (cls.model.exercise_type == "user") & (cls.model.user_id == user_id)
                )
            )
            
            # Добавляем фильтр по поисковому запросу только если он не пустой
            if search_query.strip():
                query = query.filter(func.lower(cls.model.caption).like(f"%{search_query.lower()}%"))
            
            result = await session.execute(query)
            objects = result.scalars().all()
            return objects

    @classmethod
    async def find_by_caption_paginated(cls, *, caption: str, page: int = 1, size: int = 20, **filter_by):
        """Поиск по caption с пагинацией"""
        filters = filter_by.copy()
        for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                if related_obj:
                    filters[fk_field] = related_obj.id
                else:
                    return {"items": [], "total": 0, "page": page, "size": size, "pages": 0}
        
        async with async_session_maker() as session:
            # Базовый запрос для подсчета общего количества
            count_query = select(func.count(cls.model.id)).filter(
                func.lower(cls.model.caption).like(f"%{caption.lower()}%"),
                *[getattr(cls.model, k) == v for k, v in filters.items()]
            )
            
            # Запрос для получения данных
            data_query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.video),
                joinedload(cls.model.gif),
                joinedload(cls.model.user)
            ).filter(
                func.lower(cls.model.caption).like(f"%{caption.lower()}%"),
                *[getattr(cls.model, k) == v for k, v in filters.items()]
            )
            
            # Если пагинация не нужна (page=0 или size=0), возвращаем все элементы
            if page == 0 or size == 0:
                data_result = await session.execute(data_query)
                objects = data_result.scalars().all()
                total = len(objects)
                return {
                    "items": objects,
                    "total": total,
                    "page": 0,
                    "size": 0,
                    "pages": 1
                }
            
            # Добавляем пагинацию
            data_query = data_query.offset((page - 1) * size).limit(size)
            
            # Выполняем запросы
            count_result = await session.execute(count_query)
            total = count_result.scalar()
            
            data_result = await session.execute(data_query)
            objects = data_result.scalars().all()
            
            # Вычисляем количество страниц
            pages = (total + size - 1) // size if total > 0 else 0
            
            return {
                "items": objects,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages
            }

    @classmethod
    async def search_by_caption_paginated(cls, *, search_query: str, user_id: int, page: int = 1, size: int = 20):
        """Поиск по caption с учетом exercise_type и user_id с пагинацией"""
        from sqlalchemy import or_
        
        async with async_session_maker() as session:
            # Базовый запрос для подсчета общего количества
            count_query = select(func.count(cls.model.id)).filter(
                or_(
                    cls.model.exercise_type == "system",
                    (cls.model.exercise_type == "user") & (cls.model.user_id == user_id)
                )
            )
            
            # Запрос для получения данных
            data_query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.video),
                joinedload(cls.model.gif),
                joinedload(cls.model.user)
            ).filter(
                or_(
                    cls.model.exercise_type == "system",
                    (cls.model.exercise_type == "user") & (cls.model.user_id == user_id)
                )
            )
            
            # Добавляем фильтр по поисковому запросу только если он не пустой
            if search_query.strip():
                count_query = count_query.filter(func.lower(cls.model.caption).like(f"%{search_query.lower()}%"))
                data_query = data_query.filter(func.lower(cls.model.caption).like(f"%{search_query.lower()}%"))
            
            # Если пагинация не нужна (page=0 или size=0), возвращаем все элементы
            if page == 0 or size == 0:
                data_result = await session.execute(data_query)
                objects = data_result.scalars().all()
                total = len(objects)
                return {
                    "items": objects,
                    "total": total,
                    "page": 0,
                    "size": 0,
                    "pages": 1
                }
            
            # Добавляем пагинацию к запросу данных
            data_query = data_query.offset((page - 1) * size).limit(size)
            
            # Выполняем запросы
            count_result = await session.execute(count_query)
            total = count_result.scalar()
            
            data_result = await session.execute(data_query)
            objects = data_result.scalars().all()
            
            # Вычисляем количество страниц
            pages = (total + size - 1) // size if total > 0 else 0
            
            return {
                "items": objects,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages
            }

    @classmethod
    async def get_exercise_statistics(cls, exercise_reference_uuid: UUID, user_uuid: UUID):
        """Получить статистику выполнения упражнения для конкретного пользователя"""
        from app.user_exercises.models import UserExercise, ExerciseStatus
        from app.exercises.models import Exercise
        from app.users.models import User
        from collections import defaultdict
        
        async with async_session_maker() as session:
            # Получаем ID пользователя
            user_query = select(User).filter_by(uuid=user_uuid)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            if not user:
                return None
            
            # Получаем ID exercise_reference
            exercise_ref_query = select(cls.model).filter_by(uuid=exercise_reference_uuid)
            exercise_ref_result = await session.execute(exercise_ref_query)
            exercise_ref = exercise_ref_result.scalar_one_or_none()
            if not exercise_ref:
                return None
            
            # Получаем все упражнения, связанные с этим exercise_reference
            exercises_query = select(Exercise).filter_by(exercise_reference_id=exercise_ref.id)
            exercises_result = await session.execute(exercises_query)
            exercises = exercises_result.scalars().all()
            
            if not exercises:
                return {
                    "exercise_reference_uuid": str(exercise_reference_uuid),
                    "user_uuid": str(user_uuid),
                    "max_sets_per_day": 0,
                    "total_training_days": 0,
                    "history": []
                }
            
            exercise_ids = [ex.id for ex in exercises]
            
            # Получаем все записи user_exercise для этих упражнений с фильтром по пользователю и статусу PASSED
            user_exercises_query = select(UserExercise).filter(
                UserExercise.exercise_id.in_(exercise_ids),
                UserExercise.user_id == user.id,
                UserExercise.status == ExerciseStatus.PASSED
            ).order_by(UserExercise.training_date.desc())
            
            user_exercises_result = await session.execute(user_exercises_query)
            user_exercises = user_exercises_result.scalars().all()
            
            # Группируем по дате тренировки
            history_by_date = defaultdict(list)
            for ue in user_exercises:
                history_by_date[ue.training_date].append({
                    "set_number": ue.set_number,
                    "reps": ue.reps,
                    "weight": ue.weight
                })
            
            # Формируем результат и вычисляем статистику
            history = []
            max_sets_per_day = 0
            total_training_days = len(history_by_date)
            
            for training_date in sorted(history_by_date.keys(), reverse=True):  # От новых к старым
                sets = sorted(history_by_date[training_date], key=lambda x: x["set_number"])
                sets_count = len(sets)
                
                # Обновляем максимальное количество подходов
                if sets_count > max_sets_per_day:
                    max_sets_per_day = sets_count
                
                history.append({
                    "training_date": training_date.isoformat(),
                    "sets": sets
                })
            
            return {
                "exercise_reference_uuid": str(exercise_reference_uuid),
                "user_uuid": str(user_uuid),
                "max_sets_per_day": max_sets_per_day,
                "total_training_days": total_training_days,
                "history": history
            }

    @classmethod
    async def find_passed_exercises(cls, caption: str = None) -> list:
        """
        Получить уникальные упражнения из exercise_reference, 
        по которым есть записи в user_exercise со статусом PASSED
        
        Args:
            caption: Поиск по названию упражнения (без учета регистра, частичное совпадение)
        """
        try:
            async with async_session_maker() as session:
                # Получаем записи user_exercise со статусом PASSED
                user_exercises_query = select(UserExercise).where(UserExercise.status == ExerciseStatus.PASSED)
                user_exercises_result = await session.execute(user_exercises_query)
                user_exercises = user_exercises_result.scalars().all()
                
                if not user_exercises:
                    return []
                
                # Получаем связанные упражнения
                exercise_ids = [ue.exercise_id for ue in user_exercises]
                exercises_query = select(Exercise).where(Exercise.id.in_(exercise_ids))
                exercises_result = await session.execute(exercises_query)
                exercises = exercises_result.scalars().all()
                
                # Фильтруем только те, у которых есть exercise_reference_id
                with_reference = [ex for ex in exercises if ex.exercise_reference_id is not None]
                
                if not with_reference:
                    return []
                
                # Получаем уникальные exercise_reference (загружаем только gif)
                reference_ids = [ex.exercise_reference_id for ex in with_reference]
                query = select(cls.model).options(
                    joinedload(cls.model.gif)
                ).where(cls.model.id.in_(reference_ids))
                
                # Добавляем фильтрацию по caption, если указана
                if caption:
                    query = query.where(cls.model.caption.ilike(f"%{caption}%"))
                
                query = query.distinct()
                
                result = await session.execute(query)
                return result.unique().scalars().all()
                
        except Exception as e:
            print(f"Ошибка в find_passed_exercises: {e}")
            return []