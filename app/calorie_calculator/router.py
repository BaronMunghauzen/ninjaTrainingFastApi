from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import json

from app.calorie_calculator.dao import CalorieCalculationDAO
from app.calorie_calculator.schemas import (
    SCalorieCalculation,
    SCalorieCalculationAdd,
    SCalorieCalculationUpdate
)
from app.calorie_calculator.service import CalorieCalculatorService
from app.calorie_calculator.models import GoalEnum, GenderEnum, ActivityCoefficientEnum
from app.users.dependencies import get_current_user_user
from app.users.models import User
from app.logger import logger

router = APIRouter(prefix='/api/calorie-calculator', tags=['Калькулятор калорий'])


@router.post("/calculate", response_model=SCalorieCalculation, summary="Рассчитать калории и БЖУ")
async def calculate_calories(
    data: SCalorieCalculationAdd,
    user: User = Depends(get_current_user_user)
):
    """
    Рассчитать необходимые калории и БЖУ на основе параметров пользователя
    
    Формулы:
    - BMR для мужчин: 10×вес(кг)+6.25×рост(см)−5×возраст+5
    - BMR для женщин: 10×вес(кг)+6.25×рост(см)−5×возраст−161
    - TDEE = BMR × коэффициент активности
    
    Корректировка по цели:
    - Похудение: TDEE - 15-20%
    - Набор мышц: TDEE + 10-20%
    - Поддержание: TDEE
    
    БЖУ рассчитывается в граммах из калорий с учетом соотношений:
    - Похудение: 30% белки, 25-30% жиры, 40-45% углеводы
    - Набор: 25-30% белки, 20-25% жиры, 45-55% углеводы
    - Поддержание: 20-25% белки, 25-30% жиры, 45-55% углеводы
    
    Коэффициенты активности:
    - 1.2 - Сидячий образ жизни
    - 1.375 - Слабая активность (легкие упражнения 1-3 раза в неделю)
    - 1.55 - Средняя активность (умеренные упражнения 3-5 раз в неделю)
    - 1.725 - Высокая активность (интенсивные упражнения 6-7 раз в неделю)
    - 1.9 - Экстремальная активность (очень тяжелая физическая работа или тренировки 2 раза в день)
    """
    try:
        # Деактуализируем предыдущие расчеты пользователя
        previous_calculations = await CalorieCalculationDAO.find_all(
            user_uuid=user.uuid,
            actual=True
        )
        for prev_calc in previous_calculations:
            await CalorieCalculationDAO.update(prev_calc.uuid, actual=False)
        
        # Выполняем расчеты
        results = CalorieCalculatorService.calculate_all(
            gender=data.gender,
            weight=data.weight,
            height=data.height,
            age=data.age,
            activity_coefficient=data.activity_coefficient,
            goal=data.goal
        )
        
        # Подготавливаем данные для сохранения
        db_data = {
            "user_id": user.id,
            "goal": data.goal.value,
            "gender": data.gender.value,
            "weight": data.weight,
            "height": data.height,
            "age": data.age,
            "activity_coefficient": data.activity_coefficient.value,
            "bmr": results["bmr"],
            "tdee": results["tdee"],
            "calories_for_weight_loss": json.dumps(results["calories_for_weight_loss"], ensure_ascii=False),
            "calories_for_gain": json.dumps(results["calories_for_gain"], ensure_ascii=False),
            "calories_for_maintenance": json.dumps(results["calories_for_maintenance"], ensure_ascii=False)
        }
        
        # Сохраняем в БД
        calculation_uuid = await CalorieCalculationDAO.add(**db_data)
        calculation = await CalorieCalculationDAO.find_full_data(calculation_uuid)
        
        return calculation.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при расчете калорий для пользователя {user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при расчете калорий: {str(e)}"
        )


@router.get("/last", response_model=SCalorieCalculation, summary="Получить последний актуальный расчет")
async def get_last_calculation(
    user: User = Depends(get_current_user_user)
):
    """Получить последний актуальный расчет калорий для пользователя"""
    try:
        calculation = await CalorieCalculationDAO.find_last_actual(user.id)
        
        if not calculation:
            raise HTTPException(
                status_code=404,
                detail="Актуальный расчет не найден. Сначала выполните расчет калорий."
            )
        
        return calculation.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении последнего расчета для пользователя {user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении последнего расчета"
        )


@router.get("/{calculation_uuid}", response_model=SCalorieCalculation, summary="Получить расчет по UUID")
async def get_calculation_by_uuid(
    calculation_uuid: UUID,
    user: User = Depends(get_current_user_user)
):
    """Получить расчет калорий по UUID"""
    try:
        calculation = await CalorieCalculationDAO.find_full_data(calculation_uuid)
        
        # Проверяем, что расчет принадлежит пользователю
        if calculation.user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="У вас нет доступа к этому расчету"
            )
        
        return calculation.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении расчета {calculation_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении расчета"
        )


@router.put("/{calculation_uuid}/deactivate", summary="Деактуализировать расчет")
async def deactivate_calculation(
    calculation_uuid: UUID,
    user: User = Depends(get_current_user_user)
):
    """Деактуализировать расчет (установить actual = False)"""
    try:
        calculation = await CalorieCalculationDAO.find_one_or_none(uuid=calculation_uuid)
        
        if not calculation:
            raise HTTPException(
                status_code=404,
                detail="Расчет не найден"
            )
        
        # Проверяем, что расчет принадлежит пользователю
        if calculation.user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="У вас нет доступа к этому расчету"
            )
        
        # Деактуализируем расчет
        await CalorieCalculationDAO.update(calculation_uuid, actual=False)
        
        return {"message": "Расчет деактуализирован", "uuid": str(calculation_uuid)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при деактуализации расчета {calculation_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при деактуализации расчета"
        )

