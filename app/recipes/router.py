from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import List, Optional, Dict, Any
import json
from collections import defaultdict
from sqlalchemy import update as sqlalchemy_update

from app.recipes.dao import RecipeDAO
from app.recipes.models import Recipe
from app.database import async_session_maker
from app.recipes.rb import RBRecipe
from app.recipes.schemas import SRecipe, SRecipeAdd, SRecipeUpdate
from app.users.dependencies import get_current_user_user
from app.users.models import User
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO
from app.files.service import FileService
from app.user_favorite_recipes.dao import UserFavoriteRecipeDAO
from app.logger import logger
from fastapi import status

router = APIRouter(prefix='/api/recipes', tags=['Рецепты'])


@router.get("/grouped-by-category", summary="Получить рецепты, сгруппированные по категориям")
async def get_recipes_grouped_by_category(
    actual: Optional[bool] = Query(None, description="Фильтр по актуальности записи"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    name: Optional[str] = Query(None, description="Поиск по названию (без пробелов и без учета регистра)"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    user_data: User = Depends(get_current_user_user)
) -> Dict[str, Any]:
    """
    Получить все рецепты, доступные пользователю, сгруппированные по категориям.
    
    Пользователю доступны:
    - Все системные рецепты (user_id IS NULL)
    - Все пользовательские рецепты (user_id = текущий пользователь)
    
    Параметры:
    - actual: Опциональный фильтр по актуальности (True/False)
    - category: Опциональный фильтр по категории
    - name: Опциональный поиск по названию (поиск по вхождению слов без пробелов и без учета регистра)
    - page: Номер страницы (начиная с 1)
    - size: Размер страницы (от 1 до 100)
    
    Результат: Объект с группированными рецептами и информацией о пагинации.
    Ключ в data - категория, значение - список рецептов в этой категории.
    Рецепты без категории попадают в группу с ключом "Без категории".
    """
    try:
        # Получаем доступные рецепты пользователя с пагинацией
        recipes, total_count = await RecipeDAO.find_user_available_recipes(
            user_id=user_data.id,
            actual=actual,
            category=category,
            name=name,
            page=page,
            size=size
        )
        
        # Получаем список ID избранных рецептов для текущего пользователя
        favorite_recipe_ids = await UserFavoriteRecipeDAO.get_user_favorite_recipe_ids(user_data.id)
        
        # Группируем по категориям
        grouped_recipes = defaultdict(list)
        
        for recipe in recipes:
            recipe_dict = recipe.to_dict()
            # Добавляем флаг is_favorite
            recipe_dict['is_favorite'] = recipe.id in favorite_recipe_ids
            recipe_category = recipe.category if recipe.category else "Без категории"
            grouped_recipes[recipe_category].append(recipe_dict)
        
        # Сортируем рецепты внутри каждой категории: сначала избранные, затем по дате создания (новые первыми)
        for category in grouped_recipes:
            grouped_recipes[category].sort(
                key=lambda x: (
                    not x.get('is_favorite', False),  # Сначала избранные (True), затем не избранные (False)
                    x.get('created_at', '') or ''  # Затем по дате создания (пустая строка будет в конце)
                ),
                reverse=False  # False означает: сначала True (избранные), затем False (не избранные)
            )
            # Дополнительно сортируем по дате создания в обратном порядке (новые первыми) внутри каждой группы
            # Разделяем на избранные и не избранные
            favorites = [r for r in grouped_recipes[category] if r.get('is_favorite', False)]
            non_favorites = [r for r in grouped_recipes[category] if not r.get('is_favorite', False)]
            
            # Сортируем каждую группу по дате создания (новые первыми)
            favorites.sort(key=lambda x: x.get('created_at', '') or '', reverse=True)
            non_favorites.sort(key=lambda x: x.get('created_at', '') or '', reverse=True)
            
            # Объединяем: сначала избранные, затем не избранные
            grouped_recipes[category] = favorites + non_favorites
        
        # Вычисляем информацию о пагинации
        total_pages = (total_count + size - 1) // size if total_count > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1
        
        # Возвращаем результат с пагинацией
        return {
            "data": dict(grouped_recipes),
            "pagination": {
                "page": page,
                "size": size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении рецептов по категориям: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении рецептов: {str(e)}"
        )


@router.get("/", summary="Получить все рецепты")
async def get_all_recipes(
    request_body: RBRecipe = Depends(),
    user_data: User = Depends(get_current_user_user)
) -> List[dict]:
    """
    Получить все рецепты с фильтрацией
    
    Фильтры:
    - user_uuid: UUID пользователя (None для системных рецептов)
    - category: категория рецепта
    - type: тип рецепта
    - name: название рецепта
    - actual: актуальность записи
    
    Сортировка: по дате создания, самые новые первыми
    """
    try:
        recipes = await RecipeDAO.find_all(**request_body.to_dict())
        
        result = []
        for r in recipes:
            data = r.to_dict()
            result.append(data)
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при получении рецептов: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении рецептов: {str(e)}"
        )


@router.get("/{recipe_uuid}", summary="Получить рецепт по UUID")
async def get_recipe_by_uuid(
    recipe_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Получить рецепт по UUID"""
    try:
        recipe = await RecipeDAO.find_full_data(recipe_uuid)
        return recipe.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении рецепта {recipe_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении рецепта: {str(e)}"
        )


@router.post("/add/", summary="Создать рецепт")
async def add_recipe(
    recipe: SRecipeAdd,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """
    Создать новый рецепт
    
    Пользователь может создавать только свои рецепты (user_uuid должен быть его UUID или None).
    Если user_uuid не указан, рецепт будет системным (только для админов).
    """
    try:
        values = recipe.model_dump(exclude_unset=True)
        
        # Проверяем, было ли поле user_uuid явно установлено в запросе
        # В Pydantic v2 используется model_fields_set для отслеживания установленных полей
        user_uuid_was_provided = False
        if hasattr(recipe, 'model_fields_set'):
            user_uuid_was_provided = 'user_uuid' in recipe.model_fields_set
        else:
            # Fallback для Pydantic v1 или если model_fields_set недоступен
            # Если user_uuid в values, значит оно было установлено (даже если None)
            user_uuid_was_provided = 'user_uuid' in values
        
        # Обрабатываем user_uuid
        # Если user_uuid не передан в запросе, рецепт создается для текущего пользователя
        # Если user_uuid передан как None, рецепт системный (только для админов)
        # Если user_uuid передан с UUID, рецепт пользовательский (только для своего UUID)
        if user_uuid_was_provided and 'user_uuid' in values:
            user_uuid = values.pop('user_uuid')
            if user_uuid is None:
                # Системный рецепт - только для админов
                if not user_data.is_admin:
                    raise HTTPException(
                        status_code=403,
                        detail="Только администраторы могут создавать системные рецепты"
                    )
                values['user_id'] = None
            else:
                # Пользовательский рецепт
                if user_uuid != user_data.uuid:
                    raise HTTPException(
                        status_code=403,
                        detail="Вы можете создавать рецепты только для своего профиля"
                    )
                values['user_id'] = user_data.id
        else:
            # Если user_uuid не указан в запросе, НЕ устанавливаем user_id автоматически
            # Рецепт будет создан без владельца (системный), что допустимо только для админов
            # Для обычных пользователей нужно явно указать user_uuid
            if not user_data.is_admin:
                raise HTTPException(
                    status_code=400,
                    detail="Необходимо указать user_uuid. Для создания рецепта передайте user_uuid с вашим UUID или None для системного рецепта (только для админов)"
                )
            # Для админов, если user_uuid не указан, создаем системный рецепт
            values['user_id'] = None
        
        # Обрабатываем ingredients (преобразуем в JSON строку)
        if 'ingredients' in values and values['ingredients'] is not None:
            values['ingredients'] = json.dumps(values['ingredients'], ensure_ascii=False)
        
        # Обрабатываем image_uuid
        if 'image_uuid' in values:
            image_uuid = values.pop('image_uuid')
            if image_uuid:
                image = await FilesDAO.find_one_or_none(uuid=image_uuid)
                if not image:
                    raise HTTPException(status_code=404, detail="Изображение не найдено")
                values['image_id'] = image.id
            else:
                values['image_id'] = None
        else:
            values['image_id'] = None
        
        # Создаем рецепт
        recipe_uuid = await RecipeDAO.add(**values)
        recipe_obj = await RecipeDAO.find_full_data(recipe_uuid)
        
        return recipe_obj.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании рецепта: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании рецепта: {str(e)}"
        )


@router.put("/update/{recipe_uuid}", summary="Обновить рецепт")
async def update_recipe(
    recipe_uuid: UUID,
    recipe: SRecipeUpdate,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """
    Обновить рецепт
    
    Пользователь может обновлять только свои рецепты.
    Администраторы могут обновлять любые рецепты.
    """
    try:
        # Проверяем существование рецепта
        existing_recipe = await RecipeDAO.find_one_or_none(uuid=recipe_uuid)
        if not existing_recipe:
            raise HTTPException(status_code=404, detail="Рецепт не найден")
        
        # Проверяем права доступа
        if existing_recipe.user_id is not None:  # Пользовательский рецепт
            if existing_recipe.user_id != user_data.id and not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Вы можете редактировать только свои рецепты"
                )
        else:  # Системный рецепт
            if not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Только администраторы могут редактировать системные рецепты"
                )
        
        update_data = recipe.model_dump(exclude_unset=True)
        
        # Обрабатываем ingredients (преобразуем в JSON строку)
        if 'ingredients' in update_data and update_data['ingredients'] is not None:
            update_data['ingredients'] = json.dumps(update_data['ingredients'], ensure_ascii=False)
        
        # Обрабатываем image_uuid
        if 'image_uuid' in update_data:
            image_uuid = update_data.pop('image_uuid')
            if image_uuid:
                image = await FilesDAO.find_one_or_none(uuid=image_uuid)
                if not image:
                    raise HTTPException(status_code=404, detail="Изображение не найдено")
                update_data['image_id'] = image.id
            else:
                update_data['image_id'] = None
        
        # Обновляем рецепт
        check = await RecipeDAO.update(recipe_uuid, **update_data)
        if check:
            updated_recipe = await RecipeDAO.find_full_data(recipe_uuid)
            return updated_recipe.to_dict()
        else:
            return {"message": "Ошибка при обновлении рецепта!"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении рецепта {recipe_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обновлении рецепта: {str(e)}"
        )


@router.put("/{recipe_uuid}/deactivate", summary="Деактуализировать рецепт")
async def deactivate_recipe(
    recipe_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """
    Деактуализировать рецепт (установить actual = False)
    
    Пользователь может деактуализировать только свои рецепты.
    Администраторы могут деактуализировать любые рецепты.
    """
    try:
        # Проверяем существование рецепта
        existing_recipe = await RecipeDAO.find_one_or_none(uuid=recipe_uuid)
        if not existing_recipe:
            raise HTTPException(status_code=404, detail="Рецепт не найден")
        
        # Проверяем права доступа
        if existing_recipe.user_id is not None:  # Пользовательский рецепт
            if existing_recipe.user_id != user_data.id and not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Вы можете деактуализировать только свои рецепты"
                )
        else:  # Системный рецепт
            if not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Только администраторы могут деактуализировать системные рецепты"
                )
        
        # Деактуализируем рецепт
        await RecipeDAO.update(recipe_uuid, actual=False)
        
        return {"message": "Рецепт деактуализирован", "uuid": str(recipe_uuid)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при деактуализации рецепта {recipe_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при деактуализации рецепта: {str(e)}"
        )


@router.put("/{recipe_uuid}/activate", summary="Актуализировать рецепт")
async def activate_recipe(
    recipe_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """
    Актуализировать рецепт (установить actual = True)
    
    Пользователь может актуализировать только свои рецепты.
    Администраторы могут актуализировать любые рецепты.
    """
    try:
        # Проверяем существование рецепта
        existing_recipe = await RecipeDAO.find_one_or_none(uuid=recipe_uuid)
        if not existing_recipe:
            raise HTTPException(status_code=404, detail="Рецепт не найден")
        
        # Проверяем права доступа
        if existing_recipe.user_id is not None:  # Пользовательский рецепт
            if existing_recipe.user_id != user_data.id and not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Вы можете актуализировать только свои рецепты"
                )
        else:  # Системный рецепт
            if not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Только администраторы могут актуализировать системные рецепты"
                )
        
        # Актуализируем рецепт
        await RecipeDAO.update(recipe_uuid, actual=True)
        
        return {"message": "Рецепт актуализирован", "uuid": str(recipe_uuid)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при актуализации рецепта {recipe_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при актуализации рецепта: {str(e)}"
        )


@router.delete("/delete/{recipe_uuid}", summary="Удалить рецепт")
async def delete_recipe_by_uuid(
    recipe_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """
    Удалить рецепт
    
    Пользователь может удалять только свои рецепты.
    Администраторы могут удалять любые рецепты.
    """
    try:
        # Проверяем существование рецепта
        existing_recipe = await RecipeDAO.find_one_or_none(uuid=recipe_uuid)
        if not existing_recipe:
            raise HTTPException(status_code=404, detail="Рецепт не найден")
        
        # Проверяем права доступа
        if existing_recipe.user_id is not None:  # Пользовательский рецепт
            if existing_recipe.user_id != user_data.id and not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Вы можете удалять только свои рецепты"
                )
        else:  # Системный рецепт
            if not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Только администраторы могут удалять системные рецепты"
                )
        
        # Удаляем рецепт
        check = await RecipeDAO.delete_by_id(recipe_uuid)
        if check:
            return {"message": f"Рецепт с UUID {recipe_uuid} удален!"}
        else:
            return {"message": "Ошибка при удалении рецепта!"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении рецепта {recipe_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении рецепта: {str(e)}"
        )


@router.post("/{recipe_uuid}/upload-image", summary="Загрузить изображение для рецепта")
async def upload_recipe_image(
    recipe_uuid: UUID,
    file: UploadFile = File(...),
    user_data: User = Depends(get_current_user_user)
):
    """
    Загрузить изображение для рецепта
    
    Пользователь может загружать изображения только для своих рецептов.
    Администраторы могут загружать изображения для любых рецептов.
    """
    try:
        recipe = await RecipeDAO.find_full_data(recipe_uuid)
        if not recipe:
            raise HTTPException(status_code=404, detail="Рецепт не найден")
        
        # Проверяем права доступа
        if recipe.user_id is not None:  # Пользовательский рецепт
            if recipe.user_id != user_data.id and not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Вы можете загружать изображения только для своих рецептов"
                )
        else:  # Системный рецепт
            if not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Только администраторы могут загружать изображения для системных рецептов"
                )
        
        # Сохраняем информацию о старом файле перед обновлением
        old_file_uuid = getattr(recipe.image, 'uuid', None) if recipe.image else None
        
        # Сохраняем новый файл (без удаления старого)
        saved_file = await FileService.save_file(
            file=file,
            entity_type="recipe",
            entity_id=recipe.id,
            old_file_uuid=None  # Не удаляем старый файл здесь
        )
        
        # Обновляем image_id у рецепта на новый файл
        await RecipeDAO.update(recipe_uuid, image_id=saved_file.id)
        
        # Теперь удаляем старый файл, если он был
        if old_file_uuid:
            try:
                await FileService.delete_file_by_uuid(str(old_file_uuid))
            except Exception as e:
                # Логируем ошибку, но не прерываем выполнение, так как новый файл уже сохранен
                logger.warning(f"Не удалось удалить старый файл {old_file_uuid}: {e}")
        
        return {"message": "Изображение успешно загружено", "image_uuid": saved_file.uuid}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при загрузке изображения для рецепта {recipe_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке изображения: {str(e)}"
        )


@router.delete("/{recipe_uuid}/delete-image", summary="Удалить изображение у рецепта")
async def delete_recipe_image(
    recipe_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
):
    """
    Удалить изображение у рецепта
    
    Пользователь может удалять изображения только у своих рецептов.
    Администраторы могут удалять изображения у любых рецептов.
    """
    try:
        recipe = await RecipeDAO.find_full_data(recipe_uuid)
        if not recipe:
            raise HTTPException(status_code=404, detail="Рецепт не найден")
        
        # Проверяем права доступа
        if recipe.user_id is not None:  # Пользовательский рецепт
            if recipe.user_id != user_data.id and not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Вы можете удалять изображения только у своих рецептов"
                )
        else:  # Системный рецепт
            if not user_data.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Только администраторы могут удалять изображения у системных рецептов"
                )
        
        # Проверяем, есть ли изображение
        if not recipe.image:
            raise HTTPException(status_code=404, detail="Изображение не найдено")
        
        image_uuid = recipe.image.uuid
        
        # Сначала обновляем рецепт, убирая ссылку на изображение (используем прямой SQL запрос)
        async with async_session_maker() as session:
            async with session.begin():
                update_query = (
                    sqlalchemy_update(Recipe)
                    .where(Recipe.uuid == recipe_uuid)
                    .values(image_id=None)
                )
                await session.execute(update_query)
                await session.commit()
        
        # Потом удаляем файл
        try:
            await FileService.delete_file_by_uuid(str(image_uuid))
        except Exception as e:
            logger.error(f"Ошибка при удалении файла {image_uuid}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при удалении файла: {str(e)}"
            )
        
        return {"message": "Изображение успешно удалено"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении изображения для рецепта {recipe_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении изображения: {str(e)}"
        )


@router.post("/{recipe_uuid}/favorite", summary="Добавить рецепт в избранное")
async def add_recipe_to_favorites(
    recipe_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Добавляет рецепт в избранное текущего пользователя"""
    try:
        # Получаем рецепт
        recipe = await RecipeDAO.find_full_data(recipe_uuid)
        
        # Добавляем в избранное
        favorite_uuid = await UserFavoriteRecipeDAO.add_to_favorites(
            user_id=user_data.id,
            recipe_id=recipe.id
        )
        
        return {
            "message": "Рецепт добавлен в избранное",
            "recipe_uuid": str(recipe_uuid),
            "favorite_uuid": str(favorite_uuid)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при добавлении рецепта в избранное {recipe_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при добавлении рецепта в избранное: {str(e)}"
        )


@router.delete("/{recipe_uuid}/favorite", summary="Удалить рецепт из избранного")
async def remove_recipe_from_favorites(
    recipe_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Удаляет рецепт из избранного текущего пользователя"""
    try:
        # Получаем рецепт
        recipe = await RecipeDAO.find_full_data(recipe_uuid)
        
        # Удаляем из избранного
        removed = await UserFavoriteRecipeDAO.remove_from_favorites(
            user_id=user_data.id,
            recipe_id=recipe.id
        )
        
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Рецепт не найден в избранном"
            )
        
        return {
            "message": "Рецепт удален из избранного",
            "recipe_uuid": str(recipe_uuid)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении рецепта из избранного {recipe_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении рецепта из избранного: {str(e)}"
        )

