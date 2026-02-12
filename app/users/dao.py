from app.dao.base import BaseDAO
from app.users.models import User
from sqlalchemy import select, and_, func, desc, asc
from typing import Optional, Literal


class UsersDAO(BaseDAO):
    model = User
    
    @classmethod
    async def find_users_by_avatar_id(cls, avatar_id: int):
        """Поиск всех пользователей, которые ссылаются на файл как аватар"""
        from app.database import async_session_maker
        async with async_session_maker() as session:
            query = select(cls.model).where(cls.model.avatar_id == avatar_id)
            result = await session.execute(query)
            return result.scalars().all()
    
    @classmethod
    async def find_users_with_email_notifications_enabled(cls):
        """Найти всех пользователей с включенными email уведомлениями и actual = True"""
        from app.database import async_session_maker
        async with async_session_maker() as session:
            query = select(cls.model).where(
                and_(
                    cls.model.email_notifications_enabled == True,
                    cls.model.actual == True
                )
            )
            result = await session.execute(query)
            users = result.scalars().all()
            # Отключаем объекты от сессии
            for user in users:
                session.expunge(user)
            return users
    
    @classmethod
    async def find_all_paginated(
        cls,
        page: int = 1,
        size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: Literal["asc", "desc"] = "asc",
        **filter_by
    ):
        """
        Получить всех пользователей с пагинацией и сортировкой
        
        Args:
            page: Номер страницы (начиная с 1)
            size: Размер страницы
            sort_by: Поле для сортировки (id, login, email, first_name, last_name, etc.)
            sort_order: Порядок сортировки (asc или desc)
            **filter_by: Дополнительные фильтры
        """
        from app.database import async_session_maker
        
        # Список доступных полей для сортировки
        allowed_sort_fields = {
            'id', 'uuid', 'phone_number', 'first_name', 'last_name', 'email', 
            'login', 'middle_name', 'gender', 'description', 'subscription_status',
            'subscription_until', 'theme', 'is_user', 'is_admin', 'actual',
            'email_verified', 'email_verification_sent_at', 'trial_used',
            'trial_started_at', 'fcm_token', 'email_notifications_enabled',
            'last_login_at', 'score'
        }
        
        async with async_session_maker() as session:
            # Запрос для получения данных
            query = select(cls.model).filter_by(**filter_by)
            
            # Запрос для подсчета общего количества
            count_query = select(func.count(cls.model.id)).filter_by(**filter_by)
            
            # Применяем сортировку
            if sort_by and sort_by in allowed_sort_fields:
                sort_field = getattr(cls.model, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(sort_field))
                else:
                    query = query.order_by(asc(sort_field))
            else:
                # Сортировка по умолчанию по id
                query = query.order_by(asc(cls.model.id))
            
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