"""
DAO для работы с промокодами
"""
from app.dao.base import BaseDAO
from app.promo_codes.models import PromoCode
from app.database import async_session_maker
from sqlalchemy import select, func, desc


class PromoCodeDAO(BaseDAO):
    """DAO для работы с промокодами"""
    model = PromoCode
    
    @classmethod
    async def find_by_code(cls, code: str):
        """Найти промокод по коду"""
        async with async_session_maker() as session:
            query = select(cls.model).where(cls.model.code == code.upper().strip())
            result = await session.execute(query)
            promo_code = result.scalar_one_or_none()
            if promo_code:
                session.expunge(promo_code)
            return promo_code
    
    @classmethod
    async def find_all_paginated(cls, page: int = 1, size: int = 20, **filter_by):
        """
        Получить промокоды с пагинацией и сортировкой по дате создания (новые первыми)
        """
        async with async_session_maker() as session:
            # Запрос для получения данных
            query = select(cls.model).filter_by(**filter_by)
            
            # Запрос для подсчета общего количества
            count_query = select(func.count(cls.model.id)).filter_by(**filter_by)
            
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
            items = result.scalars().all()
            
            # Вычисляем информацию о пагинации
            total_pages = (total_count + size - 1) // size if total_count > 0 else 0
            
            # Отключаем объекты от сессии
            for item in items:
                session.expunge(item)
            
            return {
                "items": items,
                "total": total_count,
                "page": page,
                "size": size,
                "pages": total_pages
            }

