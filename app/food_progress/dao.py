from app.dao.base import BaseDAO
from app.food_progress.models import DailyTarget, Meal
from app.users.dao import UsersDAO
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, func, and_
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

