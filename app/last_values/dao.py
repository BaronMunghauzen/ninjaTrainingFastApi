from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.dao.base import BaseDAO
from app.last_values.models import LastValue
from app.database import async_session_maker
from app.users.dao import UsersDAO
from fastapi import HTTPException, status


class LastValueDAO(BaseDAO):
    model = LastValue
    uuid_fk_map = {
        'user_id': (UsersDAO, 'user_uuid'),
    }

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        """Переопределяем find_full_data для загрузки связанного объекта user"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user)
            ).filter_by(uuid=object_uuid)
            result = await session.execute(query)
            object_info = result.unique().scalar_one_or_none()
            
            if not object_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Объект {cls.model.__name__} с ID {object_uuid} не найден"
                )
            
            # Отключаем объект от сессии, чтобы избежать проблем с lazy loading
            # Предзагруженные данные (user) останутся доступными
            session.expunge(object_info)
            return object_info

    @classmethod
    async def find_all(cls, **filter_by):
        """Переопределяем find_all для загрузки связанного объекта user"""
        filters = filter_by.copy()
        # Обрабатываем uuid_fk_map для связанных моделей
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
            
            result = await session.execute(query)
            result = result.unique()
            objects = result.scalars().all()
            
            # Отключаем объекты от сессии, чтобы избежать проблем с lazy loading
            # Предзагруженные данные (user) останутся доступными
            for obj in objects:
                session.expunge(obj)
            
            return objects

    @classmethod
    async def find_by_code(cls, code: str, user_id: int):
        """Поиск записи по коду и user_id"""
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(code=code, user_id=user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def add_or_update_by_code(cls, user_id: int, name: str, code: str, value: str):
        """
        Создает новую запись или обновляет существующую по коду и user_id.
        Если запись с таким code и user_id существует, обновляет value и устанавливает actual=True.
        Если не существует - создает новую запись.
        """
        async with async_session_maker() as session:
            async with session.begin():
                # Ищем существующую запись по code и user_id в той же сессии
                query = select(cls.model).filter_by(code=code, user_id=user_id)
                result = await session.execute(query)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Обновляем существующую запись
                    existing.value = value
                    existing.name = name
                    existing.actual = True
                    await session.flush()
                    await session.refresh(existing)
                    return existing.uuid
                else:
                    # Создаем новую запись
                    new_value = cls.model(
                        user_id=user_id,
                        name=name,
                        code=code,
                        value=value,
                        actual=True
                    )
                    session.add(new_value)
                    await session.flush()
                    await session.refresh(new_value)
                    return new_value.uuid

