from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from datetime import datetime, date

from app.food_progress.dao import DailyTargetDAO, MealDAO
from sqlalchemy import select, and_
from app.food_progress.rb import RBDailyTarget, RBMeal
from app.food_progress.schemas import (
    SDailyTarget, SDailyTargetAdd, SDailyTargetUpdate,
    SMeal, SMealAdd, SMealUpdate, SDailyProgress
)
from app.users.dependencies import get_current_user_user
from app.users.models import User
from app.logger import logger

router = APIRouter(prefix='/api/food-progress', tags=['Прогресс по еде'])


class DefaultTarget:
    """Класс для дефолтных значений целевых уровней КБЖУ (все нули)"""
    target_calories = 0.0
    target_proteins = 0.0
    target_fats = 0.0
    target_carbs = 0.0


def get_target_or_default(target):
    """Возвращает target или DefaultTarget, если target отсутствует"""
    return target if target else DefaultTarget()


# ==================== DailyTarget методы ====================

@router.get("/targets/", summary="Получить все целевые уровни")
async def get_all_targets(
    request_body: RBDailyTarget = Depends(),
    user_data: User = Depends(get_current_user_user)
) -> List[dict]:
    """Получить все целевые уровни КБЖУ пользователя"""
    try:
        filters = request_body.to_dict()
        if 'user_uuid' not in filters:
            filters['user_uuid'] = str(user_data.uuid)
        targets = await DailyTargetDAO.find_all(**filters)
        return [t.to_dict() for t in targets]
    except Exception as e:
        logger.error(f"Ошибка при получении целевых уровней: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/targets/{target_uuid}", summary="Получить целевой уровень по UUID")
async def get_target_by_uuid(
    target_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Получить целевой уровень по UUID"""
    try:
        target = await DailyTargetDAO.find_full_data(target_uuid)
        if target.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        return target.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении целевого уровня: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/targets/add/", summary="Создать целевой уровень")
async def add_target(
    target: SDailyTargetAdd,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Создать новый целевой уровень КБЖУ"""
    try:
        # Деактуализируем предыдущие целевые уровни
        prev_targets = await DailyTargetDAO.find_all(user_uuid=str(user_data.uuid), actual=True)
        for prev in prev_targets:
            await DailyTargetDAO.update(prev.uuid, actual=False)
        
        values = target.model_dump()
        values['user_id'] = user_data.id
        target_uuid = await DailyTargetDAO.add(**values)
        target_obj = await DailyTargetDAO.find_full_data(target_uuid)
        return target_obj.to_dict()
    except Exception as e:
        logger.error(f"Ошибка при создании целевого уровня: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/targets/update/{target_uuid}", summary="Обновить целевой уровень")
async def update_target(
    target_uuid: UUID,
    target: SDailyTargetUpdate,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Обновить целевой уровень"""
    try:
        existing = await DailyTargetDAO.find_one_or_none(uuid=target_uuid)
        if not existing or existing.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        
        update_data = target.model_dump(exclude_unset=True)
        await DailyTargetDAO.update(target_uuid, **update_data)
        updated = await DailyTargetDAO.find_full_data(target_uuid)
        return updated.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении целевого уровня: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/targets/{target_uuid}/deactivate", summary="Деактуализировать целевой уровень")
async def deactivate_target(
    target_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Деактуализировать целевой уровень"""
    try:
        existing = await DailyTargetDAO.find_one_or_none(uuid=target_uuid)
        if not existing or existing.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        await DailyTargetDAO.update(target_uuid, actual=False)
        return {"message": "Целевой уровень деактуализирован", "uuid": str(target_uuid)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при деактуализации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/targets/{target_uuid}/activate", summary="Актуализировать целевой уровень")
async def activate_target(
    target_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Актуализировать целевой уровень"""
    try:
        existing = await DailyTargetDAO.find_one_or_none(uuid=target_uuid)
        if not existing or existing.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        
        # Деактуализируем другие целевые уровни
        prev_targets = await DailyTargetDAO.find_all(user_uuid=str(user_data.uuid), actual=True)
        for prev in prev_targets:
            if prev.uuid != existing.uuid:
                await DailyTargetDAO.update(prev.uuid, actual=False)
        
        await DailyTargetDAO.update(target_uuid, actual=True)
        return {"message": "Целевой уровень актуализирован", "uuid": str(target_uuid)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при актуализации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/targets/delete/{target_uuid}", summary="Удалить целевой уровень")
async def delete_target(
    target_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Удалить целевой уровень"""
    try:
        existing = await DailyTargetDAO.find_one_or_none(uuid=target_uuid)
        if not existing or existing.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        await DailyTargetDAO.delete_by_id(target_uuid)
        return {"message": f"Целевой уровень с UUID {target_uuid} удален"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Meal методы ====================

@router.get("/meals/", summary="Получить все приемы пищи")
async def get_all_meals(
    request_body: RBMeal = Depends(),
    user_data: User = Depends(get_current_user_user),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы")
) -> dict:
    """Получить все приемы пищи пользователя с пагинацией"""
    try:
        filters = request_body.to_dict()
        if 'user_uuid' not in filters:
            filters['user_uuid'] = str(user_data.uuid)
        
        result = await MealDAO.find_all_paginated(page=page, size=size, **filters)
        
        return {
            "items": [m.to_dict() for m in result["items"]],
            "pagination": result["pagination"]
        }
    except Exception as e:
        logger.error(f"Ошибка при получении приемов пищи: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meals/{meal_uuid}", summary="Получить прием пищи по UUID")
async def get_meal_by_uuid(
    meal_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Получить прием пищи по UUID"""
    try:
        meal = await MealDAO.find_full_data(meal_uuid)
        if meal.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        return meal.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении приема пищи: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meals/add/", summary="Создать прием пищи")
async def add_meal(
    meal: SMealAdd,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Создать новый прием пищи"""
    try:
        # Получаем последний актуальный целевой уровень или используем нули по умолчанию
        target = get_target_or_default(await DailyTargetDAO.find_last_actual(user_data.id))
        
        # Получаем сумму съеденного за день
        meal_date = meal.meal_datetime.date()
        daily_totals = await MealDAO.get_daily_totals(user_data.id, meal_date)
        
        # Рассчитываем остатки с учетом нового приема пищи
        # Используем 0 для None значений
        proteins_value = meal.proteins or 0
        fats_value = meal.fats or 0
        carbs_value = meal.carbs or 0
        
        total_calories = daily_totals["calories"] + meal.calories
        total_proteins = daily_totals["proteins"] + proteins_value
        total_fats = daily_totals["fats"] + fats_value
        total_carbs = daily_totals["carbs"] + carbs_value
        
        remaining_calories = target.target_calories - total_calories
        remaining_proteins = target.target_proteins - total_proteins
        remaining_fats = target.target_fats - total_fats
        remaining_carbs = target.target_carbs - total_carbs
        
        values = meal.model_dump()
        # Убеждаемся, что None значения заменены на 0
        values['proteins'] = proteins_value
        values['fats'] = fats_value
        values['carbs'] = carbs_value
        values['user_id'] = user_data.id
        values['target_calories'] = target.target_calories
        values['target_proteins'] = target.target_proteins
        values['target_fats'] = target.target_fats
        values['target_carbs'] = target.target_carbs
        values['remaining_calories'] = remaining_calories
        values['remaining_proteins'] = remaining_proteins
        values['remaining_fats'] = remaining_fats
        values['remaining_carbs'] = remaining_carbs
        
        meal_uuid = await MealDAO.add(**values)
        
        # Пересчитываем остатки для всех приемов пищи за этот день
        await _recalculate_day_remainders(user_data.id, meal_date, target)
        
        meal_obj = await MealDAO.find_full_data(meal_uuid)
        return meal_obj.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании приема пищи: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/meals/update/{meal_uuid}", summary="Обновить прием пищи")
async def update_meal(
    meal_uuid: UUID,
    meal: SMealUpdate,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Обновить прием пищи"""
    try:
        existing = await MealDAO.find_one_or_none(uuid=meal_uuid)
        if not existing or existing.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        
        # Получаем дату для пересчета остатков
        meal_date = existing.meal_datetime.date()
        target = get_target_or_default(await DailyTargetDAO.find_last_actual(user_data.id))
        
        update_data = meal.model_dump(exclude_unset=True)
        await MealDAO.update(meal_uuid, **update_data)
        
        # Пересчитываем остатки для всех приемов пищи за этот день
        await _recalculate_day_remainders(user_data.id, meal_date, target)
        
        updated = await MealDAO.find_full_data(meal_uuid)
        return updated.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении приема пищи: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/meals/{meal_uuid}/deactivate", summary="Деактуализировать прием пищи")
async def deactivate_meal(
    meal_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Деактуализировать прием пищи"""
    try:
        existing = await MealDAO.find_one_or_none(uuid=meal_uuid)
        if not existing or existing.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        
        meal_date = existing.meal_datetime.date()
        target = get_target_or_default(await DailyTargetDAO.find_last_actual(user_data.id))
        
        await MealDAO.update(meal_uuid, actual=False)
        
        await _recalculate_day_remainders(user_data.id, meal_date, target)
        
        return {"message": "Прием пищи деактуализирован", "uuid": str(meal_uuid)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при деактуализации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/meals/{meal_uuid}/activate", summary="Актуализировать прием пищи")
async def activate_meal(
    meal_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Актуализировать прием пищи"""
    try:
        existing = await MealDAO.find_one_or_none(uuid=meal_uuid)
        if not existing or existing.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        
        meal_date = existing.meal_datetime.date()
        target = get_target_or_default(await DailyTargetDAO.find_last_actual(user_data.id))
        
        await MealDAO.update(meal_uuid, actual=True)
        
        await _recalculate_day_remainders(user_data.id, meal_date, target)
        
        return {"message": "Прием пищи актуализирован", "uuid": str(meal_uuid)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при актуализации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/meals/delete/{meal_uuid}", summary="Удалить прием пищи")
async def delete_meal(
    meal_uuid: UUID,
    user_data: User = Depends(get_current_user_user)
) -> dict:
    """Удалить прием пищи"""
    try:
        existing = await MealDAO.find_one_or_none(uuid=meal_uuid)
        if not existing or existing.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Нет доступа")
        
        meal_date = existing.meal_datetime.date()
        target = get_target_or_default(await DailyTargetDAO.find_last_actual(user_data.id))
        
        await MealDAO.delete_by_id(meal_uuid)
        
        await _recalculate_day_remainders(user_data.id, meal_date, target)
        
        return {"message": f"Прием пищи с UUID {meal_uuid} удален"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meals/daily/{target_date}", response_model=SDailyProgress, summary="Получить прогресс за день")
async def get_daily_progress(
    target_date: date,
    user_data: User = Depends(get_current_user_user)
):
    """
    Получить прогресс за день: сколько съедено, целевые уровни, остатки
    """
    try:
        # Получаем целевые уровни или используем нули по умолчанию
        target = get_target_or_default(await DailyTargetDAO.find_last_actual(user_data.id))
        
        # Получаем суммарное количество съеденного за день
        daily_totals = await MealDAO.get_daily_totals(user_data.id, target_date)
        
        # Рассчитываем остатки
        remaining_calories = target.target_calories - daily_totals["calories"]
        remaining_proteins = target.target_proteins - daily_totals["proteins"]
        remaining_fats = target.target_fats - daily_totals["fats"]
        remaining_carbs = target.target_carbs - daily_totals["carbs"]
        
        return {
            "date": target_date,
            "eaten_calories": daily_totals["calories"],
            "eaten_proteins": daily_totals["proteins"],
            "eaten_fats": daily_totals["fats"],
            "eaten_carbs": daily_totals["carbs"],
            "target_calories": target.target_calories,
            "target_proteins": target.target_proteins,
            "target_fats": target.target_fats,
            "target_carbs": target.target_carbs,
            "remaining_calories": remaining_calories,
            "remaining_proteins": remaining_proteins,
            "remaining_fats": remaining_fats,
            "remaining_carbs": remaining_carbs
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении прогресса за день: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _recalculate_day_remainders(user_id: int, meal_date: date, target):
    """Пересчитать остатки для всех приемов пищи за день"""
    from sqlalchemy import and_
    from app.database import async_session_maker
    from app.food_progress.models import Meal
    
    async with async_session_maker() as session:
        day_start = datetime.combine(meal_date, datetime.min.time())
        day_end = datetime.combine(meal_date, datetime.max.time())
        
        # Получаем все приемы пищи за день
        query = select(Meal).where(
            and_(
                Meal.user_id == user_id,
                Meal.actual == True,
                Meal.meal_datetime >= day_start,
                Meal.meal_datetime <= day_end
            )
        ).order_by(Meal.meal_datetime)
        
        result = await session.execute(query)
        meals = result.scalars().all()
        
        # Накапливаем суммы по мере обработки приемов пищи
        cumulative_calories = 0
        cumulative_proteins = 0
        cumulative_fats = 0
        cumulative_carbs = 0
        
        for meal in meals:
            cumulative_calories += meal.calories
            cumulative_proteins += meal.proteins
            cumulative_fats += meal.fats
            cumulative_carbs += meal.carbs
            
            # Обновляем остатки
            meal.remaining_calories = target.target_calories - cumulative_calories
            meal.remaining_proteins = target.target_proteins - cumulative_proteins
            meal.remaining_fats = target.target_fats - cumulative_fats
            meal.remaining_carbs = target.target_carbs - cumulative_carbs
            
            # Обновляем целевые уровни
            meal.target_calories = target.target_calories
            meal.target_proteins = target.target_proteins
            meal.target_fats = target.target_fats
            meal.target_carbs = target.target_carbs
        
        await session.commit()

