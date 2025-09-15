from uuid import UUID
from typing import Optional, List
from datetime import date, datetime

from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.user_measurements.models import UserMeasurementType, UserMeasurement
from app.exceptions import CategotyNotFoundException
from app.users.dao import UsersDAO


class UserMeasurementTypeDAO(BaseDAO):
    model = UserMeasurementType
    uuid_fk_map = {
        'user_id': (UsersDAO, 'user_uuid')
    }

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        """Переопределяем find_full_data для загрузки связанных объектов"""
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
            return object_info

    @classmethod
    async def _check_uniqueness(cls, session, values: dict, exclude_uuid: UUID = None):
        """Переопределяем проверку уникальности для составного индекса (caption, user_id)"""
        # Проверяем только составной уникальный индекс (caption, user_id)
        caption = values.get('caption')
        user_id = values.get('user_id')
        
        # Если передан user_uuid, нужно его преобразовать в user_id
        if 'user_uuid' in values and not user_id:
            from app.users.dao import UsersDAO
            user = await UsersDAO.find_one_or_none(uuid=values['user_uuid'])
            if user:
                user_id = user.id
        
        if caption and user_id is not None:  # user_id может быть None для системных типов
            query = select(cls.model).where(
                and_(
                    cls.model.caption == caption,
                    cls.model.user_id == user_id
                )
            )
            if exclude_uuid:
                query = query.where(cls.model.uuid != exclude_uuid)
            
            exists = await session.execute(query)
            if exists.scalar():
                raise ValueError(f"Тип измерения с названием '{caption}' уже существует для данного пользователя")
        
        # Проверяем уникальность UUID (если есть)
        if 'uuid' in values:
            query = select(cls.model).where(cls.model.uuid == values['uuid'])
            if exclude_uuid:
                query = query.where(cls.model.uuid != exclude_uuid)
            
            exists = await session.execute(query)
            if exists.scalar():
                raise ValueError(f"Объект с uuid='{values['uuid']}' уже существует")

    @classmethod
    async def update(cls, object_uuid: UUID, **values):
        """Переопределяем update для использования правильной проверки уникальности"""
        # Фильтруем None значения
        values = {k: v for k, v in values.items() if v is not None}
        if not values:  # Если ничего не передали для обновления
            return 0
        async with async_session_maker() as session:
            try:
                async with session.begin():
                    # Проверяем уникальность с исключением текущего объекта
                    await cls._check_uniqueness(session, values, exclude_uuid=object_uuid)
                    
                    # Обновляем объект
                    query = select(cls.model).where(cls.model.uuid == object_uuid)
                    result = await session.execute(query)
                    obj = result.scalar_one_or_none()
                    
                    if not obj:
                        return 0
                    
                    for key, value in values.items():
                        setattr(obj, key, value)
                    
                    await session.commit()
                    return 1
            except ValueError as e:
                await session.rollback()
                raise e
            except Exception as e:
                await session.rollback()
                raise e

    @classmethod
    async def find_by_user_and_caption(cls, user_id: Optional[int], caption: str) -> Optional[UserMeasurementType]:
        """Поиск типа измерения по пользователю и названию"""
        async with async_session_maker() as session:
            query = select(cls.model).where(
                and_(
                    cls.model.user_id == user_id,
                    cls.model.caption == caption
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_system_types(cls) -> List[UserMeasurementType]:
        """Получение всех системных типов измерений"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user)
            ).where(
                and_(
                    cls.model.data_type == "system",
                    cls.model.actual == True
                )
            ).order_by(cls.model.caption)
            result = await session.execute(query)
            return result.unique().scalars().all()

    @classmethod
    async def find_user_types(cls, user_id: int) -> List[UserMeasurementType]:
        """Получение всех пользовательских типов измерений для конкретного пользователя"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user)
            ).where(
                and_(
                    cls.model.user_id == user_id,
                    cls.model.actual == True
                )
            ).order_by(cls.model.caption)
            result = await session.execute(query)
            return result.unique().scalars().all()

    @classmethod
    async def find_all(cls, **filters) -> List[UserMeasurementType]:
        """Переопределяем find_all для загрузки связанных объектов"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user)
            )
            
            # Применяем фильтры
            for key, value in filters.items():
                if hasattr(cls.model, key) and value is not None:
                    query = query.where(getattr(cls.model, key) == value)
            
            result = await session.execute(query)
            return result.unique().scalars().all()

    @classmethod
    async def archive(cls, measurement_type_uuid: UUID) -> bool:
        """Архивация типа измерения (установка actual = False)"""
        async with async_session_maker() as session:
            try:
                # Получаем тип измерения в текущей сессии
                measurement_type_query = select(cls.model).where(cls.model.uuid == measurement_type_uuid)
                measurement_type_result = await session.execute(measurement_type_query)
                measurement_type = measurement_type_result.scalar_one_or_none()
                
                if not measurement_type:
                    return False
                
                # Сначала архивируем все связанные измерения
                measurements_query = select(UserMeasurement).where(
                    UserMeasurement.measurement_type_id == measurement_type.id
                )
                measurements_result = await session.execute(measurements_query)
                measurements = measurements_result.scalars().all()
                
                for measurement in measurements:
                    measurement.actual = False
                    measurement.updated_at = datetime.utcnow()
                
                # Затем архивируем сам тип измерения
                measurement_type.actual = False
                measurement_type.updated_at = datetime.utcnow()
                
                await session.commit()
                return True
            except SQLAlchemyError as e:
                await session.rollback()
                raise e

    @classmethod
    async def unarchive(cls, measurement_type_uuid: UUID) -> bool:
        """Разархивация типа измерения (установка actual = True)"""
        async with async_session_maker() as session:
            try:
                # Получаем тип измерения в текущей сессии
                measurement_type_query = select(cls.model).where(cls.model.uuid == measurement_type_uuid)
                measurement_type_result = await session.execute(measurement_type_query)
                measurement_type = measurement_type_result.scalar_one_or_none()
                
                if not measurement_type:
                    return False
                
                measurement_type.actual = True
                measurement_type.updated_at = datetime.utcnow()
                
                await session.commit()
                return True
            except SQLAlchemyError as e:
                await session.rollback()
                raise e

    @classmethod
    async def delete_with_measurements(cls, measurement_type_uuid: UUID) -> bool:
        """Удаление типа измерения вместе с связанными измерениями"""
        async with async_session_maker() as session:
            try:
                # Получаем тип измерения в текущей сессии
                measurement_type_query = select(cls.model).where(cls.model.uuid == measurement_type_uuid)
                measurement_type_result = await session.execute(measurement_type_query)
                measurement_type = measurement_type_result.scalar_one_or_none()
                
                if not measurement_type:
                    return False
                
                # Сначала удаляем все связанные измерения
                measurements_query = select(UserMeasurement).where(
                    UserMeasurement.measurement_type_id == measurement_type.id
                )
                measurements_result = await session.execute(measurements_query)
                measurements = measurements_result.scalars().all()
                
                for measurement in measurements:
                    await session.delete(measurement)
                
                # Затем удаляем сам тип измерения
                await session.delete(measurement_type)
                await session.commit()
                return True
            except SQLAlchemyError as e:
                await session.rollback()
                raise e


class UserMeasurementDAO(BaseDAO):
    model = UserMeasurement
    uuid_fk_map = {
        'user_id': (UsersDAO, 'user_uuid'),
        'measurement_type_id': (UserMeasurementTypeDAO, 'measurement_type_uuid')
    }

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        """Переопределяем find_full_data для загрузки связанных объектов"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user),
                joinedload(cls.model.measurement_type)
            ).filter_by(uuid=object_uuid)
            result = await session.execute(query)
            object_info = result.unique().scalar_one_or_none()
            
            if not object_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Объект {cls.model.__name__} с ID {object_uuid} не найден"
                )
            return object_info

    @classmethod
    async def find_all(cls, **filters) -> List[UserMeasurement]:
        """Переопределяем find_all для загрузки связанных объектов"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user),
                joinedload(cls.model.measurement_type)
            )
            
            # Применяем фильтры
            for key, value in filters.items():
                if hasattr(cls.model, key) and value is not None:
                    query = query.where(getattr(cls.model, key) == value)
            
            result = await session.execute(query)
            return result.unique().scalars().all()

    @classmethod
    async def _check_uniqueness(cls, session, values: dict, exclude_uuid: UUID = None):
        """Переопределяем проверку уникальности для составного индекса (user_id, measurement_date, measurement_type_id)"""
        # Проверяем только составной уникальный индекс (user_id, measurement_date, measurement_type_id)
        user_id = values.get('user_id')
        measurement_date = values.get('measurement_date')
        measurement_type_id = values.get('measurement_type_id')
        
        # Если переданы UUID поля, нужно их преобразовать в ID
        if 'user_uuid' in values and not user_id:
            from app.users.dao import UsersDAO
            user = await UsersDAO.find_one_or_none(uuid=values['user_uuid'])
            if user:
                user_id = user.id
        
        if 'measurement_type_uuid' in values and not measurement_type_id:
            measurement_type = await UserMeasurementTypeDAO.find_one_or_none(uuid=values['measurement_type_uuid'])
            if measurement_type:
                measurement_type_id = measurement_type.id
        
        if all([user_id, measurement_date, measurement_type_id]):
            query = select(cls.model).where(
                and_(
                    cls.model.user_id == user_id,
                    cls.model.measurement_date == measurement_date,
                    cls.model.measurement_type_id == measurement_type_id
                )
            )
            if exclude_uuid:
                query = query.where(cls.model.uuid != exclude_uuid)
            
            exists = await session.execute(query)
            if exists.scalar():
                raise ValueError(f"Измерение для данного пользователя, даты и типа уже существует")
        
        # Проверяем уникальность UUID (если есть)
        if 'uuid' in values:
            query = select(cls.model).where(cls.model.uuid == values['uuid'])
            if exclude_uuid:
                query = query.where(cls.model.uuid != exclude_uuid)
            
            exists = await session.execute(query)
            if exists.scalar():
                raise ValueError(f"Объект с uuid='{values['uuid']}' уже существует")

    @classmethod
    async def update(cls, object_uuid: UUID, **values):
        """Переопределяем update для использования правильной проверки уникальности"""
        # Фильтруем None значения
        values = {k: v for k, v in values.items() if v is not None}
        if not values:  # Если ничего не передали для обновления
            return 0
        async with async_session_maker() as session:
            try:
                async with session.begin():
                    # Проверяем уникальность с исключением текущего объекта
                    await cls._check_uniqueness(session, values, exclude_uuid=object_uuid)
                    
                    # Обновляем объект
                    query = select(cls.model).where(cls.model.uuid == object_uuid)
                    result = await session.execute(query)
                    obj = result.scalar_one_or_none()
                    
                    if not obj:
                        return 0
                    
                    for key, value in values.items():
                        setattr(obj, key, value)
                    
                    await session.commit()
                    return 1
            except ValueError as e:
                await session.rollback()
                raise e
            except Exception as e:
                await session.rollback()
                raise e

    @classmethod
    async def find_by_user_with_pagination(
        cls, 
        user_id: int, 
        page: int = 1, 
        size: int = 10,
        measurement_type_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        actual: Optional[bool] = None
    ) -> dict:
        """Получение измерений пользователя с пагинацией и фильтрацией"""
        async with async_session_maker() as session:
            # Базовый запрос с загрузкой связанных объектов
            query = select(cls.model).options(
                joinedload(cls.model.user),
                joinedload(cls.model.measurement_type)
            ).where(cls.model.user_id == user_id)
            
            # Применяем фильтры
            if measurement_type_id:
                query = query.where(cls.model.measurement_type_id == measurement_type_id)
            
            if date_from:
                query = query.where(cls.model.measurement_date >= date_from)
            
            if date_to:
                query = query.where(cls.model.measurement_date <= date_to)
            
            if actual is not None:
                query = query.where(cls.model.actual == actual)
            
            # Сортируем по дате измерения (новые сначала)
            query = query.order_by(desc(cls.model.measurement_date), desc(cls.model.created_at))
            
            # Подсчитываем общее количество записей
            count_query = select(cls.model).where(cls.model.user_id == user_id)
            if measurement_type_id:
                count_query = count_query.where(cls.model.measurement_type_id == measurement_type_id)
            if date_from:
                count_query = count_query.where(cls.model.measurement_date >= date_from)
            if date_to:
                count_query = count_query.where(cls.model.measurement_date <= date_to)
            if actual is not None:
                count_query = count_query.where(cls.model.actual == actual)
            
            total_count_result = await session.execute(count_query)
            total_count = len(total_count_result.scalars().all())
            
            # Применяем пагинацию
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)
            
            # Выполняем запрос
            result = await session.execute(query)
            measurements = result.unique().scalars().all()
            
            # Вычисляем информацию о пагинации
            total_pages = (total_count + size - 1) // size
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "items": measurements,
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
    async def find_by_user_and_type(
        cls, 
        user_id: int, 
        measurement_type_id: int
    ) -> List[UserMeasurement]:
        """Получение всех измерений пользователя определенного типа"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user),
                joinedload(cls.model.measurement_type)
            ).where(
                and_(
                    cls.model.user_id == user_id,
                    cls.model.measurement_type_id == measurement_type_id,
                    cls.model.actual == True
                )
            ).order_by(desc(cls.model.measurement_date))
            result = await session.execute(query)
            return result.unique().scalars().all()

    @classmethod
    async def find_latest_by_type(
        cls, 
        user_id: int, 
        measurement_type_id: int
    ) -> Optional[UserMeasurement]:
        """Получение последнего измерения пользователя определенного типа"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user),
                joinedload(cls.model.measurement_type)
            ).where(
                and_(
                    cls.model.user_id == user_id,
                    cls.model.measurement_type_id == measurement_type_id,
                    cls.model.actual == True
                )
            ).order_by(desc(cls.model.measurement_date)).limit(1)
            result = await session.execute(query)
            return result.unique().scalar_one_or_none()
