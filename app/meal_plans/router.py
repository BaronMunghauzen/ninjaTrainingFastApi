from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import json

from app.meal_plans.dao import MealPlanDAO
from app.meal_plans.schemas import SMealPlan, SMealPlanAdd, SMealPlanUpdate, SMealPlanGenerationResult
from app.meal_plans.service import MealPlanService
from app.users.dependencies import get_current_user_user
from app.users.models import User
from app.calorie_calculator.dao import CalorieCalculationDAO
from app.food_progress.dao import DailyTargetDAO
from app.logger import logger

router = APIRouter(prefix='/api/meal-plans', tags=['Программы питания'])


@router.post("/generate", response_model=SMealPlanGenerationResult, summary="Сгенерировать программу питания")
async def generate_meal_plan(
    data: SMealPlanAdd,
    user: User = Depends(get_current_user_user)
):
    """
    Автоматически создать программу питания
    
    Логика генерации:
    - Учитываются выбранные рецепты (или все доступные)
    - Соблюдается разнообразие блюд (ограничение на повторы в неделю)
    - Распределение КБЖУ по приемам пищи согласно лучшим практикам
    - Подбор блюд с учетом целевых КБЖУ с допуском ±15%
    - Для обеда возможно добавление супа + второго блюда (контролируется параметром include_soup_in_lunch)
    
    Целевые КБЖУ берутся из последнего актуального расчета калорий или целевого уровня.
    """
    try:
        # Получаем целевые КБЖУ
        target_calories = None
        target_proteins = None
        target_fats = None
        target_carbs = None
        
        # Сначала пытаемся взять из последнего расчета калорий
        calorie_calc = await CalorieCalculationDAO.find_last_actual(user.id)
        if calorie_calc:
            # Берем КБЖУ для цели из расчета
            if calorie_calc.goal.value == "weight_loss":
                macros = json.loads(calorie_calc.calories_for_weight_loss or "{}")
            elif calorie_calc.goal.value == "muscle_gain":
                macros = json.loads(calorie_calc.calories_for_gain or "{}")
            else:
                macros = json.loads(calorie_calc.calories_for_maintenance or "{}")
            
            target_calories = macros.get("calories", calorie_calc.tdee)
            target_proteins = macros.get("proteins", 0)
            target_fats = macros.get("fats", 0)
            target_carbs = macros.get("carbs", 0)
        
        # Если нет расчета, берем из целевых уровней
        if not target_calories:
            daily_target = await DailyTargetDAO.find_last_actual(user.id)
            if daily_target:
                target_calories = daily_target.target_calories
                target_proteins = daily_target.target_proteins
                target_fats = daily_target.target_fats
                target_carbs = daily_target.target_carbs
        
        if not target_calories:
            raise HTTPException(
                status_code=400,
                detail="Сначала установите целевые уровни КБЖУ (расчет калорий или целевые уровни)"
            )
        
        # Генерируем программу питания
        plan_data = await MealPlanService.generate_meal_plan(
            user_id=user.id,
            meals_per_day=data.meals_per_day,
            days_count=data.days_count,
            max_repeats_per_week=data.max_repeats_per_week or 2,
            allowed_recipe_uuids=[str(uuid) for uuid in data.allowed_recipe_uuids] if data.allowed_recipe_uuids else None,
            target_calories=target_calories,
            target_proteins=target_proteins,
            target_fats=target_fats,
            target_carbs=target_carbs,
            include_soup_in_lunch=data.include_soup_in_lunch
        )
        
        # Деактуализируем предыдущие программы
        prev_plans = await MealPlanDAO.find_all(user_uuid=str(user.uuid), actual=True)
        for prev in prev_plans:
            await MealPlanDAO.update(prev.uuid, actual=False)
        
        # Сохраняем программу в БД
        db_data = {
            "user_id": user.id,
            "meals_per_day": data.meals_per_day,
            "days_count": data.days_count,
            "max_repeats_per_week": data.max_repeats_per_week or 2,
            "allowed_recipe_uuids": json.dumps([str(uuid) for uuid in data.allowed_recipe_uuids], ensure_ascii=False) if data.allowed_recipe_uuids else None,
            "include_soup_in_lunch": data.include_soup_in_lunch,
            "target_calories": target_calories,
            "target_proteins": target_proteins,
            "target_fats": target_fats,
            "target_carbs": target_carbs,
            "plan_data": json.dumps(plan_data, ensure_ascii=False),
            "recommendations": json.dumps(MealPlanService.RECOMMENDATIONS, ensure_ascii=False)
        }
        
        plan_uuid = await MealPlanDAO.add(**db_data)
        
        return {
            "plan_uuid": plan_uuid,
            "message": f"Программа питания успешно создана на {data.days_count} дней"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации программы питания для пользователя {user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при генерации программы питания: {str(e)}"
        )


@router.get("/", summary="Получить все программы питания")
async def get_all_meal_plans(
    user: User = Depends(get_current_user_user)
) -> List[dict]:
    """Получить все программы питания пользователя"""
    try:
        plans = await MealPlanDAO.find_all(user_uuid=str(user.uuid))
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

