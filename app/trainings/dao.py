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
from typing import Optional
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
            # Сортировка: сначала актуальные записи (actual=True), затем неактуальные (actual=False)
            if hasattr(cls.model, 'actual'):
                query = query.order_by(cls.model.actual.desc())
            result = await session.execute(query)
            objects = result.scalars().all()
            
            # Отключаем объекты от сессии, чтобы избежать проблем с lazy loading
            for obj in objects:
                session.expunge(obj)
            
            return objects

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.program).joinedload(Program.image),
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
            
            # Отключаем объект от сессии, чтобы избежать проблем с lazy loading
            session.expunge(object_info)
            return object_info

    @classmethod
    async def find_full_data_by_id(cls, object_id: int):
        """
        Оптимизированная версия find_full_data_by_id.
        НЕ загружает коллекции exercise_groups, user_trainings, user_exercises,
        так как они могут содержать тысячи записей и не нужны для просмотра одной тренировки.
        """
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.program).joinedload(Program.image),
                joinedload(cls.model.user)
                # НЕ загружаем: exercise_groups, user_trainings, user_exercises (большие коллекции)
            ).filter_by(id=object_id)
            result = await session.execute(query)
            result = result.unique()
            object_info = result.scalar_one_or_none()
            if not object_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Объект {cls.model.__name__} с ID {object_id} не найден"
                )
            
            # Отключаем объект от сессии, чтобы избежать проблем с lazy loading
            session.expunge(object_info)
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
                joinedload(cls.model.program).joinedload(Program.image),
                joinedload(cls.model.user)
            ).filter_by(**filters)
            # Сортировка: сначала актуальные записи (actual=True), затем неактуальные (actual=False)
            if hasattr(cls.model, 'actual'):
                query = query.order_by(cls.model.actual.desc())
            if hasattr(cls.model, 'order'):
                query = query.order_by(cls.model.order.asc())
            result = await session.execute(query)
            result = result.unique()
            objects = result.scalars().all()
            
            # Отключаем объекты от сессии, чтобы избежать проблем с lazy loading
            for obj in objects:
                session.expunge(obj)
            
            return objects

    @classmethod
    async def search_by_caption(cls, *, search_query: str, user_id: int):
        """Поиск по caption с учетом training_type и user_id"""
        from sqlalchemy import or_, func
        
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.program).joinedload(Program.image)
            ).filter(
                func.lower(cls.model.caption).like(f"%{search_query.lower()}%"),
                or_(
                    cls.model.training_type == "system_training",
                    (cls.model.training_type == "user") & (cls.model.user_id == user_id)
                )
            )
            # Сортировка: сначала актуальные записи (actual=True), затем неактуальные (actual=False)
            if hasattr(cls.model, 'actual'):
                query = query.order_by(cls.model.actual.desc())
            result = await session.execute(query)
            result = result.unique()
            objects = result.scalars().all()
            
            # Отключаем объекты от сессии, чтобы избежать проблем с lazy loading
            for obj in objects:
                session.expunge(obj)
            
            return objects

    @classmethod
    async def find_by_id_with_image(cls, object_id: int):
        """
        Оптимизированный метод для получения тренировки по ID только с изображением
        """
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image)
            ).filter_by(id=object_id)
            result = await session.execute(query)
            object_info = result.scalar_one_or_none()
            if not object_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Объект {cls.model.__name__} с ID {object_id} не найден"
                )
            
            # Отключаем объект от сессии, чтобы избежать проблем с lazy loading
            session.expunge(object_info)
            return object_info

    @classmethod
    async def archive_training(cls, training_uuid: UUID):
        """
        Архивировать тренировку (установить actual = False)
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(uuid=training_uuid)
            result = await session.execute(query)
            training = result.scalar_one_or_none()
            
            if not training:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Тренировка с UUID {training_uuid} не найдена"
                )
            
            training.actual = False
            await session.commit()
            
            # Обновляем состояние объекта из БД перед отключением от сессии
            await session.refresh(training)
            
            # Отключаем объект от сессии
            session.expunge(training)
            return training

    @classmethod
    async def restore_training(cls, training_uuid: UUID):
        """
        Восстановить тренировку из архива (установить actual = True)
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(uuid=training_uuid)
            result = await session.execute(query)
            training = result.scalar_one_or_none()
            
            if not training:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Тренировка с UUID {training_uuid} не найдена"
                )
            
            training.actual = True
            await session.commit()
            
            # Обновляем состояние объекта из БД перед отключением от сессии
            await session.refresh(training)
            
            # Отключаем объект от сессии
            session.expunge(training)
            return training