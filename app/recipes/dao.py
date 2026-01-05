from app.dao.base import BaseDAO
from app.recipes.models import Recipe
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import desc
from app.database import async_session_maker
from fastapi import HTTPException, status
from uuid import UUID


class RecipeDAO(BaseDAO):
    model = Recipe
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
                # Если uuid_value None, то не добавляем фильтр (для поиска системных рецептов)
                elif uuid_field == 'user_uuid' and uuid_value is None:
                    filters['user_id'] = None
        
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

