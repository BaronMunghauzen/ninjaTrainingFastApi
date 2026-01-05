from app.dao.base import BaseDAO
from app.food_recognition.models import FoodRecognition
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import joinedload
from app.database import async_session_maker
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime, date
from typing import Optional


class FoodRecognitionDAO(BaseDAO):
    model = FoodRecognition
    uuid_fk_map = {
        'user_id': (UsersDAO, 'user_uuid'),
        'image_id': (FilesDAO, 'image_uuid')
    }
    
    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user),
                joinedload(cls.model.image)
            ).filter_by(uuid=object_uuid)
            result = await session.execute(query)
            object_info = result.scalar_one_or_none()
            if not object_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Объект {cls.model.__name__} с ID {object_uuid} не найден"
                )
            session.expunge(object_info)
            return object_info
    
    @classmethod
    async def find_all(cls, **filter_by):
        filters = filter_by.copy()
        for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                if uuid_value is not None:
                    related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                    if related_obj:
                        filters[fk_field] = related_obj.id
                    else:
                        return []
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user),
                joinedload(cls.model.image)
            ).filter_by(**filters)
            
            # Сортировка по дате создания, самые новые первыми
            query = query.order_by(desc(cls.model.created_at))
            
            result = await session.execute(query)
            objects = result.unique().scalars().all()
            for obj in objects:
                session.expunge(obj)
            return objects
    
    @classmethod
    async def find_by_user_with_pagination(
        cls,
        user_id: int,
        page: int = 1,
        size: int = 10,
        created_from: Optional[date] = None,
        created_to: Optional[date] = None,
        actual: Optional[bool] = None,
        name: Optional[str] = None
    ) -> dict:
        async with async_session_maker() as session:
            # Основной запрос
            query = select(cls.model).options(
                joinedload(cls.model.user),
                joinedload(cls.model.image)
            ).where(cls.model.user_id == user_id)
            
            # Запрос для подсчета
            count_query = select(func.count(cls.model.id)).where(cls.model.user_id == user_id)
            
            # Применяем фильтры
            if created_from:
                query = query.where(cls.model.created_at >= created_from)
                count_query = count_query.where(cls.model.created_at >= created_from)
            
            if created_to:
                # Для created_to учитываем весь день, поэтому добавляем 1 день и используем <
                from datetime import timedelta
                created_to_end = datetime.combine(created_to, datetime.max.time())
                query = query.where(cls.model.created_at <= created_to_end)
                count_query = count_query.where(cls.model.created_at <= created_to_end)
            
            if actual is not None:
                query = query.where(cls.model.actual == actual)
                count_query = count_query.where(cls.model.actual == actual)
            
            if name:
                # Поиск по вхождению строки без учета регистра
                query = query.where(func.lower(cls.model.name).contains(func.lower(name)))
                count_query = count_query.where(func.lower(cls.model.name).contains(func.lower(name)))
            
            # Сортировка по дате создания, самые новые первыми
            query = query.order_by(desc(cls.model.created_at))
            
            # Получаем общее количество
            total_count_result = await session.execute(count_query)
            total_count = total_count_result.scalar() or 0
            
            # Применяем пагинацию
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)
            
            # Выполняем запрос
            result = await session.execute(query)
            items = result.unique().scalars().all()
            
            # Вычисляем информацию о пагинации
            total_pages = (total_count + size - 1) // size if total_count > 0 else 0
            has_next = page < total_pages
            has_prev = page > 1
            
            # Отключаем объекты от сессии
            for item in items:
                session.expunge(item)
            
            return {
                "items": items,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
    
    @classmethod
    async def count_requests_today(cls, user_id: int) -> int:
        """Подсчитать количество запросов пользователя за сегодня"""
        async with async_session_maker() as session:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            query = select(func.count(cls.model.id)).where(
                cls.model.user_id == user_id,
                cls.model.created_at >= today_start
            )
            result = await session.execute(query)
            return result.scalar() or 0

