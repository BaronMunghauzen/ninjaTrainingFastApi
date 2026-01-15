from app.dao.base import BaseDAO
from app.programs.models import Program
from app.categories.dao import CategoryDAO
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import and_
from app.database import async_session_maker
from fastapi import HTTPException, status
from uuid import UUID

class ProgramDAO(BaseDAO):
    model = Program
    uuid_fk_map = {
        'category_id': (CategoryDAO, 'category_uuid'),
        'user_id': (UsersDAO, 'user_uuid'),
        'image_id': (FilesDAO, 'image_uuid')
    }

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        """
        Оптимизированная версия find_full_data, которая загружает только необходимые данные.
        НЕ загружает коллекции user_trainings, user_exercises, trainings, user_programs,
        так как они могут содержать тысячи записей и не нужны для просмотра программы.
        """
        async with async_session_maker() as session:
            # Загружаем только необходимые связи: image, category, user
            # НЕ загружаем коллекции (user_trainings, user_exercises, trainings, user_programs)
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.category),
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
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.user_trainings),
                joinedload(cls.model.user_exercises),
                joinedload(cls.model.trainings),
                joinedload(cls.model.user_programs),
                joinedload(cls.model.category),
                joinedload(cls.model.user)
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
                # Если uuid_value не None, то ищем связанный объект
                if uuid_value is not None:
                    related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                    if related_obj:
                        filters[fk_field] = related_obj.id
                    else:
                        return []
                # Если uuid_value None, то не добавляем фильтр (позволяет искать записи без категории)
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.image),
                joinedload(cls.model.user_trainings),
                joinedload(cls.model.user_exercises),
                joinedload(cls.model.trainings),
                joinedload(cls.model.user_programs),
                joinedload(cls.model.category),
                joinedload(cls.model.user)
            ).filter_by(**filters)
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
    async def find_all_optimized(cls, **filter_by):
        """
        Оптимизированная версия find_all для быстрого получения списка программ
        без загрузки связанных данных
        """
        filters = filter_by.copy()
        for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                # Если uuid_value не None, то ищем связанный объект
                if uuid_value is not None:
                    related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                    if related_obj:
                        filters[fk_field] = related_obj.id
                    else:
                        return []
                # Если uuid_value None, то не добавляем фильтр (позволяет искать записи без категории)
        
        async with async_session_maker() as session:
            # Базовый запрос без JOIN'ов для быстрого получения программ
            query = select(cls.model).filter_by(**filters)
            
            # Добавляем сортировку по полю order, если оно существует в модели
            if hasattr(cls.model, 'order'):
                query = query.order_by(cls.model.order.asc())
            
            result = await session.execute(query)
            objects = result.scalars().all()
            
            # Отключаем объекты от сессии, чтобы избежать проблем с lazy loading
            for obj in objects:
                session.expunge(obj)
            
            return objects

    @classmethod
    async def find_all_with_categories_and_users(cls, **filter_by):
        """
        Оптимизированный метод для получения программ с категориями и пользователями
        Использует batch loading для избежания N+1 проблемы
        """
        # Сначала получаем программы с изображениями
        programs = await cls.find_all_with_images(**filter_by)
        
        if not programs:
            return []
        
        # Получаем все уникальные category_id и user_id (исключаем None значения)
        category_ids = {p.category_id for p in programs if p.category_id is not None}
        user_ids = {p.user_id for p in programs if p.user_id is not None}
        
        # Batch loading для категорий и пользователей
        categories = await CategoryDAO.find_in('id', list(category_ids)) if category_ids else []
        users = await UsersDAO.find_in('id', list(user_ids)) if user_ids else []
        
        # Создаем словари для быстрого поиска
        id_to_category = {c.id: c for c in categories}
        id_to_user = {u.id: u for u in users}
        
        # Формируем результат
        result = []
        for program in programs:
            # Используем безопасную версию to_dict
            program_data = program.to_dict_safe()
            
            # Добавляем связанные данные
            if program.category_id and program.category_id in id_to_category:
                program_data['category'] = id_to_category[program.category_id].to_dict()
            else:
                program_data['category'] = None
                
            if program.user_id and program.user_id in id_to_user:
                user_data = id_to_user[program.user_id]
                program_data['user'] = user_data.to_dict() if hasattr(user_data, 'to_dict') else None
            else:
                program_data['user'] = None
            
            result.append(program_data)
        
        return result

    @classmethod
    async def search_by_caption(cls, *, search_query: str, user_id: int):
        """Поиск по caption с учетом program_type и user_id"""
        from sqlalchemy import or_, func
        
        async with async_session_maker() as session:
            # Убираем избыточные JOIN'ы для поиска
            query = select(cls.model).filter(
                func.lower(cls.model.caption).like(f"%{search_query.lower()}%"),
                or_(
                    cls.model.program_type == "system",
                    (cls.model.program_type == "user") & (cls.model.user_id == user_id)
                )
            )
            
            # Добавляем сортировку по полю order, если оно существует в модели
            if hasattr(cls.model, 'order'):
                query = query.order_by(cls.model.order.asc())
                
            result = await session.execute(query)
            objects = result.scalars().all()
            
            # Отключаем объекты от сессии, чтобы избежать проблем с lazy loading
            for obj in objects:
                session.expunge(obj)
            
            return objects

    @classmethod
    async def find_all_with_images(cls, **filter_by):
        """
        Метод для получения программ с изображениями (если нужны)
        """
        filters = filter_by.copy()
        for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                # Если uuid_value не None, то ищем связанный объект
                if uuid_value is not None:
                    related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                    if related_obj:
                        filters[fk_field] = related_obj.id
                    else:
                        return []
                # Если uuid_value None, то не добавляем фильтр (позволяет искать записи без категории)
        
        async with async_session_maker() as session:
            # Загружаем только image, остальные связи не нужны для списка
            query = select(cls.model).options(
                joinedload(cls.model.image)
            ).filter_by(**filters)
            
            if hasattr(cls.model, 'order'):
                query = query.order_by(cls.model.order.asc())
            
            result = await session.execute(query)
            objects = result.scalars().all()
            
            # Отключаем объекты от сессии, чтобы избежать проблем с lazy loading
            for obj in objects:
                session.expunge(obj)
            
            return objects

    @classmethod
    async def find_by_id_with_image(cls, object_id: int):
        """
        Оптимизированный метод для получения программы по ID только с изображением
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
