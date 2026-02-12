from app.dao.base import BaseDAO
from app.food_progress.models import DailyTarget, Meal
from app.users.dao import UsersDAO
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime, date
from typing import Optional


class DailyTargetDAO(BaseDAO):
    model = DailyTarget
    uuid_fk_map = {
        'user_id': (UsersDAO, 'user_uuid')
    }
    
    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user)
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
                joinedload(cls.model.user)
            ).filter_by(**filters)
            
            # Сортировка по дате создания, самые новые первыми
            query = query.order_by(desc(cls.model.created_at))
            
            result = await session.execute(query)
            objects = result.unique().scalars().all()
            for obj in objects:
                session.expunge(obj)
            return objects
    
    @classmethod
    async def find_last_actual(cls, user_id: int):
        """Получить последний актуальный целевой уровень для пользователя"""
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .options(joinedload(cls.model.user))
                .where(
                    cls.model.user_id == user_id,
                    cls.model.actual == True
                )
                .order_by(desc(cls.model.created_at))
                .limit(1)
            )
            result = await session.execute(query)
            target = result.scalar_one_or_none()
            if target:
                session.expunge(target)
            return target


class MealDAO(BaseDAO):
    model = Meal
    uuid_fk_map = {
        'user_id': (UsersDAO, 'user_uuid')
    }
    
    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user)
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
                joinedload(cls.model.user)
            ).filter_by(**filters)
            
            # Сортировка по дате приема пищи, самые новые первыми
            query = query.order_by(desc(cls.model.meal_datetime))
            
            result = await session.execute(query)
            objects = result.unique().scalars().all()
            for obj in objects:
                session.expunge(obj)
            return objects
    
    @classmethod
    async def find_all_paginated(cls, page: int = 1, size: int = 20, **filter_by):
        """
        Получить приемы пищи с пагинацией
        
        Args:
            page: Номер страницы (начиная с 1)
            size: Размер страницы
            **filter_by: Фильтры для поиска
        
        Returns:
            Словарь с items и pagination
        """
        filters = filter_by.copy()
        for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                if uuid_value is not None:
                    related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                    if related_obj:
                        filters[fk_field] = related_obj.id
                    else:
                        return {
                            "items": [],
                            "pagination": {
                                "page": page,
                                "size": size,
                                "total_count": 0,
                                "total_pages": 0,
                                "has_next": False,
                                "has_prev": False
                            }
                        }
        
        async with async_session_maker() as session:
            # Запрос для получения данных
            query = select(cls.model).options(
                joinedload(cls.model.user)
            ).filter_by(**filters)
            
            # Запрос для подсчета общего количества
            count_query = select(func.count(cls.model.id)).filter_by(**filters)
            
            # Сортировка по дате приема пищи, самые новые первыми
            query = query.order_by(desc(cls.model.meal_datetime))
            
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
    async def get_daily_totals(cls, user_id: int, target_date: date) -> dict:
        """
        Получить суммарное количество съеденных КБЖУ за день
        
        Returns:
            Словарь с суммами: calories, proteins, fats, carbs
        """
        async with async_session_maker() as session:
            # Начало и конец дня
            day_start = datetime.combine(target_date, datetime.min.time())
            day_end = datetime.combine(target_date, datetime.max.time())
            
            query = (
                select(
                    func.sum(cls.model.calories).label('total_calories'),
                    func.sum(cls.model.proteins).label('total_proteins'),
                    func.sum(cls.model.fats).label('total_fats'),
                    func.sum(cls.model.carbs).label('total_carbs')
                )
                .where(
                    cls.model.user_id == user_id,
                    cls.model.actual == True,
                    cls.model.meal_datetime >= day_start,
                    cls.model.meal_datetime <= day_end
                )
            )
            
            result = await session.execute(query)
            row = result.first()
            
            return {
                "calories": float(row.total_calories or 0),
                "proteins": float(row.total_proteins or 0),
                "fats": float(row.total_fats or 0),
                "carbs": float(row.total_carbs or 0)
            }
    
    @classmethod
    async def search_by_name(cls, user_id: int, search_query: str, page: int = 1, size: int = 20):
        """
        Поиск приемов пищи по названию (по вхождению подстрок разделенных пробелом без учета регистра)
        
        Args:
            user_id: ID пользователя
            search_query: Строка поиска (подстроки разделены пробелом)
            page: Номер страницы (начиная с 1)
            size: Размер страницы
        
        Returns:
            Словарь с items и pagination
        """
        async with async_session_maker() as session:
            # Создаем базовый запрос
            query = select(cls.model).options(
                joinedload(cls.model.user)
            ).filter(
                cls.model.user_id == user_id,
                cls.model.actual == True
            )
            
            # Добавляем фильтр по поисковому запросу только если он не пустой
            if search_query.strip():
                # Разбиваем поисковый запрос на слова и ищем все слова в названии
                search_words = [word.strip() for word in search_query.strip().split() if word.strip()]
                if search_words:
                    # Создаем условия для каждого слова (все слова должны присутствовать)
                    word_conditions = [
                        func.lower(cls.model.name).like(f"%{word.lower()}%")
                        for word in search_words
                    ]
                    # Объединяем все условия через AND
                    search_filter = word_conditions[0]
                    for condition in word_conditions[1:]:
                        search_filter = search_filter & condition
                    
                    query = query.filter(search_filter)
            
            # Запрос для подсчета общего количества
            count_query = select(func.count(cls.model.id)).filter(
                cls.model.user_id == user_id,
                cls.model.actual == True
            )
            
            # Применяем те же условия поиска для подсчета
            if search_query.strip():
                search_words = [word.strip() for word in search_query.strip().split() if word.strip()]
                if search_words:
                    word_conditions = [
                        func.lower(cls.model.name).like(f"%{word.lower()}%")
                        for word in search_words
                    ]
                    search_filter = word_conditions[0]
                    for condition in word_conditions[1:]:
                        search_filter = search_filter & condition
                    
                    count_query = count_query.filter(search_filter)
            
            # Сортировка по дате приема пищи, самые новые первыми
            query = query.order_by(desc(cls.model.meal_datetime))
            
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

