from app.dao.base import BaseDAO
from app.user_training.models import UserTraining
from app.user_program.dao import UserProgramDAO
from app.programs.dao import ProgramDAO
from app.trainings.dao import TrainingDAO
from app.users.dao import UsersDAO
from app.database import async_session_maker
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from functools import lru_cache
import hashlib
import json
from uuid import UUID
import sqlalchemy as sa
import asyncio


class UserTrainingDAO(BaseDAO):
    model = UserTraining
    uuid_fk_map = {
        'user_program_id': (UserProgramDAO, 'user_program_uuid'),
        'program_id': (ProgramDAO, 'program_uuid'),
        'training_id': (TrainingDAO, 'training_uuid'),
        'user_id': (UsersDAO, 'user_uuid')
    }
    
    # Простой кэш для результатов запросов
    _cache = {}
    _cache_ttl = 300  # 5 минут
    
    @classmethod
    async def find_active_trainings(cls, user_program_id: int | None):
        """Получить активные тренировки для программы пользователя без исключения"""
        async with async_session_maker() as session:
            query = select(cls.model)
            if user_program_id is not None:
                query = query.filter_by(user_program_id=user_program_id, status='active')
            else:
                query = query.filter_by(status='active')
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    def _get_cache_key(cls, **filter_by):
        """Генерирует ключ кэша на основе параметров фильтрации"""
        # Сортируем параметры для стабильного ключа
        sorted_params = sorted(filter_by.items())
        params_str = json.dumps(sorted_params, sort_keys=True)
        return hashlib.md5(params_str.encode()).hexdigest()

    @classmethod
    async def find_all_with_relations(cls, **filter_by):
        """Оптимизированный метод для загрузки user_trainings без задержки"""
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
            query = select(cls.model).filter_by(**filters)
            query = query.order_by(cls.model.training_date.asc())
            result = await session.execute(query)
            objects = result.scalars().all()
            return objects

    @classmethod
    async def find_all_with_relations_paginated(cls, page: int = 1, page_size: int = 50, **filter_by):
        """Оптимизированный метод с пагинацией на уровне БД без задержки"""
        filters = filter_by.copy()
        for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                if related_obj:
                    filters[fk_field] = related_obj.id
                else:
                    return [], 0
        async with async_session_maker() as session:
            count_query = select(sa.func.count(cls.model.id)).filter_by(**filters)
            total_count = await session.scalar(count_query)
            query = select(cls.model).filter_by(**filters)
            query = query.order_by(cls.model.training_date.asc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            objects = result.scalars().all()
            return objects, total_count

    @classmethod
    def clear_cache(cls):
        """Очищает кэш"""
        pass  # Кэш больше не используется

    @classmethod
    async def update(cls, object_uuid: UUID, **values):
        """Переопределяем метод update для очистки кэша при обновлении"""
        # Кэш больше не используется
        return await super().update(object_uuid, **values)
