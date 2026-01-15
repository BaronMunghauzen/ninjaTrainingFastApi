from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import json

from app.meal_plans.dao import MealPlanDAO
from app.meal_plans.schemas import SMealPlan, SMealPlanAdd, SMealPlanUpdate, SMealPlanGenerationResult
from app.meal_plans.service import MealPlanService
from app.users.dependencies import get_current_user_user
from app.users.models import User
from app.logger import logger

router = APIRouter(prefix='/api/meal-plans', tags=['Программы питания'])


@router.post("/generate", response_model=SMealPlanGenerationResult, summary="Сгенерировать программу питания")
async def generate_meal_plan(
    data: SMealPlanAdd,
    user: User = Depends(get_current_user_user)
):
    """
    Автоматически создать программу питания
    
    Новая логика:
    - Обязательные приёмы пищи: breakfast, lunch, dinner (всегда создаются)
    - Опциональные приёмы пищи: snack1, snack2, snack3 (добавляются при необходимости)
    - Система автоматически определяет количество приёмов пищи на основе целевых КБЖУ
    - Максимум 6 приёмов пищи в день
    - Жёсткие правила категорий блюд
    - Batch cooking для breakfast, lunch, dinner (готовка на 2 дня)
    """
    try:
        # Подготавливаем список UUID рецептов
        allowed_recipe_uuids = None
        if not data.use_all_recipes:
            if not data.allowed_recipe_uuids:
                raise HTTPException(
                    status_code=400,
                    detail="Необходимо указать allowed_recipe_uuids или установить use_all_recipes=True"
                )
            allowed_recipe_uuids = [str(uuid) for uuid in data.allowed_recipe_uuids]
        
        # Генерируем программу питания
        logger.info(f"Генерация программы питания для пользователя {user.id}")
        plan_data = await MealPlanService.generate_meal_plan(
            user_id=user.id,
            days_count=data.days_count,
            allowed_recipe_uuids=allowed_recipe_uuids,
            target_calories=data.target_nutrition.calories,
            target_proteins=data.target_nutrition.proteins,
            target_fats=data.target_nutrition.fats,
            target_carbs=data.target_nutrition.carbs
        )
        
        # Деактуализируем предыдущие программы
        prev_plans = await MealPlanDAO.find_all(user_uuid=str(user.uuid), actual=True)
        for prev in prev_plans:
            await MealPlanDAO.update(prev.uuid, actual=False)
        
        # Подсчитываем среднее количество приёмов пищи в день для сохранения в БД (опционально, для статистики)
        avg_meals_per_day = 3  # Минимум 3 (breakfast, lunch, dinner)
        if plan_data.get("days") and len(plan_data["days"]) > 0:
            total_meals = sum(len(day.get("meals", [])) for day in plan_data["days"])
            avg_meals_per_day = round(total_meals / len(plan_data["days"]))
        
        # Подготавливаем целевые КБЖУ для сохранения
        target_nutrition = {
            "calories": data.target_nutrition.calories,
            "proteins": data.target_nutrition.proteins,
            "fats": data.target_nutrition.fats,
            "carbs": data.target_nutrition.carbs
        }
        
        # Сохраняем программу в БД
        db_data = {
            "user_id": user.id,
            "meals_per_day": avg_meals_per_day,  # Сохраняем для обратной совместимости (система сама определяет)
            "days_count": data.days_count,
            "allowed_recipe_uuids": json.dumps([str(uuid) for uuid in data.allowed_recipe_uuids], ensure_ascii=False) if data.allowed_recipe_uuids else None,
            "use_all_recipes": data.use_all_recipes,
            "target_nutrition": json.dumps(target_nutrition, ensure_ascii=False),
            "response_data": json.dumps(plan_data, ensure_ascii=False)  # Сохраняем plan_data в response_data
        }
        
        plan_uuid = await MealPlanDAO.add(**db_data)
        
        logger.info(f"Программа питания успешно создана для пользователя {user.id}, UUID: {plan_uuid}")
        
        return {
            "plan_uuid": plan_uuid,
            "message": f"Программа питания успешно создана на {data.days_count} дней"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Ошибка валидации при генерации программы питания для пользователя {user.id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при генерации программы питания для пользователя {user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при генерации программы питания: {str(e)}"
        )


@router.get("/", summary="Получить все программы питания")
async def get_all_meal_plans(
    actual: Optional[bool] = Query(None, description="Фильтр по актуальности записи"),
    user: User = Depends(get_current_user_user)
) -> List[dict]:
    """Получить все программы питания пользователя"""
    try:
        filters = {"user_uuid": str(user.uuid)}
        if actual is not None:
            filters["actual"] = actual
        
        plans = await MealPlanDAO.find_all(**filters)
        return [p.to_dict() for p in plans]
    except Exception as e:
        logger.error(f"Ошибка при получении программ питания: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plan_uuid}", summary="Получить программу питания по UUID")
async def get_meal_plan_by_uuid(
    plan_uuid: UUID,
    user: User = Depends(get_current_user_user)
) -> dict:
    """Получить программу питания по UUID"""
    try:
        plan = await MealPlanDAO.find_full_data(plan_uuid)
        if plan.user_id != user.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        return plan.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении программы питания: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{plan_uuid}/deactivate", summary="Деактуализировать программу питания")
async def deactivate_meal_plan(
    plan_uuid: UUID,
    user: User = Depends(get_current_user_user)
) -> dict:
    """Деактуализировать программу питания"""
    try:
        plan = await MealPlanDAO.find_one_or_none(uuid=plan_uuid)
        if not plan or plan.user_id != user.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        await MealPlanDAO.update(plan_uuid, actual=False)
        return {"message": "Программа питания деактуализирована", "uuid": str(plan_uuid)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при деактуализации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{plan_uuid}/activate", summary="Актуализировать программу питания")
async def activate_meal_plan(
    plan_uuid: UUID,
    user: User = Depends(get_current_user_user)
) -> dict:
    """Актуализировать программу питания"""
    try:
        plan = await MealPlanDAO.find_one_or_none(uuid=plan_uuid)
        if not plan or plan.user_id != user.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        
        # Деактуализируем другие программы
        prev_plans = await MealPlanDAO.find_all(user_uuid=str(user.uuid), actual=True)
        for prev in prev_plans:
            if prev.uuid != plan.uuid:
                await MealPlanDAO.update(prev.uuid, actual=False)
        
        await MealPlanDAO.update(plan_uuid, actual=True)
        return {"message": "Программа питания актуализирована", "uuid": str(plan_uuid)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при актуализации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{plan_uuid}", summary="Удалить программу питания")
async def delete_meal_plan(
    plan_uuid: UUID,
    user: User = Depends(get_current_user_user)
) -> dict:
    """Удалить программу питания"""
    try:
        plan = await MealPlanDAO.find_one_or_none(uuid=plan_uuid)
        if not plan or plan.user_id != user.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        await MealPlanDAO.delete_by_id(plan_uuid)
        return {"message": f"Программа питания с UUID {plan_uuid} удалена"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении: {e}")
        raise HTTPException(status_code=500, detail=str(e))

