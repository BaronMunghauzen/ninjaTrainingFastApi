from app.dao.base import BaseDAO
from app.recipes.models import Recipe
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO
from app.user_favorite_recipes.models import UserFavoriteRecipe
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, or_, func
from app.database import async_session_maker
from fastapi import HTTPException, status
from uuid import UUID
from typing import Optional, Tuple


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
    
    @classmethod
    async def find_user_available_recipes(
        cls,
        user_id: int,
        actual: Optional[bool] = None,
        category: Optional[str] = None,
        name: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Tuple[list, int]:
        """
        Найти все рецепты, доступные пользователю:
        - Системные рецепты (user_id IS NULL)
        - Пользовательские рецепты (user_id = current_user.id)
        
        Параметры:
        - actual: Опциональная фильтрация по актуальности
        - category: Опциональная фильтрация по категории
        - name: Опциональный поиск по названию (без пробелов и без учета регистра)
        - page: Номер страницы (начиная с 1)
        - size: Размер страницы
        
        Возвращает: (список рецептов, общее количество)
        """
        async with async_session_maker() as session:
            # Базовое условие для доступных рецептов
            base_condition = or_(
                cls.model.user_id.is_(None),  # Системные рецепты
                cls.model.user_id == user_id  # Пользовательские рецепты
            )
            
            # Запрос для получения рецептов
            query = select(cls.model).options(
                joinedload(cls.model.user),
                joinedload(cls.model.image)
            ).where(base_condition)
            
            # Запрос для подсчета общего количества (без пагинации)
            count_query = select(func.count(cls.model.id)).where(base_condition)
            
            # Опциональная фильтрация по actual
            if actual is not None:
                query = query.where(cls.model.actual == actual)
                count_query = count_query.where(cls.model.actual == actual)
            
            # Опциональная фильтрация по category
            if category is not None:
                query = query.where(cls.model.category == category)
                count_query = count_query.where(cls.model.category == category)
            
            # Опциональный поиск по name (поиск по вхождению слов без пробелов и без учета регистра)
            if name is not None:
                # Разбиваем поисковый запрос на слова и убираем пробелы из каждого слова
                search_words = [word.strip().lower() for word in name.split() if word.strip()]
                
                if search_words:
                    # Исключаем записи с NULL name при поиске
                    query = query.where(cls.model.name.isnot(None))
                    count_query = count_query.where(cls.model.name.isnot(None))
                    
                    # Для каждого слова проверяем, что оно входит в название (без пробелов и без учета регистра)
                    # Используем COALESCE для обработки NULL значений
                    recipe_name_without_spaces = func.lower(
                        func.replace(func.coalesce(cls.model.name, ""), " ", "")
                    )
                    
                    # Проверяем, что каждое слово из поискового запроса входит в название рецепта
                    for search_word in search_words:
                        name_filter = recipe_name_without_spaces.contains(search_word)
                        query = query.where(name_filter)
                        count_query = count_query.where(name_filter)
            
            # Получаем общее количество
            count_result = await session.execute(count_query)
            total_count = count_result.scalar() or 0
            
            # Подзапрос для проверки, является ли рецепт избранным
            is_favorite_subq = select(
                func.count(UserFavoriteRecipe.id)
            ).where(
                UserFavoriteRecipe.recipe_id == cls.model.id,
                UserFavoriteRecipe.user_id == user_id
            ).scalar_subquery()
            
            # Сортировка: сначала избранные (is_favorite DESC), затем по дате создания (самые новые первыми)
            query = query.order_by(
                is_favorite_subq.desc(),  # Сначала избранные (1), затем не избранные (0)
                desc(cls.model.created_at)  # Затем по дате создания
            )
            
            # Применяем пагинацию
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)
            
            result = await session.execute(query)
            objects = result.unique().scalars().all()
            for obj in objects:
                session.expunge(obj)
            
            return objects, total_count

