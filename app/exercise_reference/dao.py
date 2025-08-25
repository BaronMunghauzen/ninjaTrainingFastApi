from app.dao.base import BaseDAO
from app.exercise_reference.models import ExerciseReference
from app.files.dao import FilesDAO
from app.users.dao import UsersDAO
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
        'user_id': (UsersDAO, 'user_uuid')
    }

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.video),
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