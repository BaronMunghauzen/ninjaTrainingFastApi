from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
import json

from app.recipes.dao import RecipeDAO
from app.recipes.rb import RBRecipe
from app.recipes.schemas import SRecipe, SRecipeAdd, SRecipeUpdate
from app.users.dependencies import get_current_user_user
from app.users.models import User
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO
from app.files.service import FileService
from app.logger import logger

router = APIRouter(prefix='/api/recipes', tags=['Рецепты'])


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
        
        # Обрабатываем user_uuid
        if 'user_uuid' in values:
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
            # Если user_uuid не указан, по умолчанию создаем для текущего пользователя
            values['user_id'] = user_data.id
        
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
        
        # Сохраняем файл
        old_file_uuid = getattr(recipe.image, 'uuid', None) if recipe.image else None
        saved_file = await FileService.save_file(
            file=file,
            entity_type="recipe",
            entity_id=recipe.id,
            old_file_uuid=str(old_file_uuid) if old_file_uuid else None
        )
        
        # Обновляем image_id у рецепта
        await RecipeDAO.update(recipe_uuid, image_id=saved_file.id)
        
        return {"message": "Изображение успешно загружено", "image_uuid": saved_file.uuid}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при загрузке изображения для рецепта {recipe_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке изображения: {str(e)}"
        )

