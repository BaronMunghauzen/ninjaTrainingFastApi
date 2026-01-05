from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime
from enum import Enum


class GoalEnum(str, Enum):
    """Цели пользователя"""
    weight_loss = "weight_loss"  # Похудение
    muscle_gain = "muscle_gain"  # Набор мышц
    maintenance = "maintenance"  # Поддержание формы


class GenderEnum(str, Enum):
    """Пол пользователя"""
    male = "male"  # Мужской
    female = "female"  # Женский


class ActivityCoefficientEnum(str, Enum):
    """Коэффициенты активности"""
    sedentary = "1.2"  # Сидячий образ жизни
    light = "1.375"  # Слабая активность (легкие упражнения 1-3 раза в неделю)
    moderate = "1.55"  # Средняя активность (умеренные упражнения 3-5 раз в неделю)
    high = "1.725"  # Высокая активность (интенсивные упражнения 6-7 раз в неделю)
    extreme = "1.9"  # Экстремальная активность (очень тяжелая физическая работа или тренировки 2 раза в день)


class SCalorieCalculation(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    actual: bool = Field(..., description="Актуальность записи")
    user_uuid: Optional[UUID] = Field(None, description="UUID пользователя")
    goal: str = Field(..., description="Цель (weight_loss, muscle_gain, maintenance)")
    gender: str = Field(..., description="Пол (male, female)")
    weight: float = Field(..., description="Вес в кг")
    height: float = Field(..., description="Рост в см")
    age: int = Field(..., description="Возраст")
    activity_coefficient: str = Field(..., description="Коэффициент активности")
    bmr: float = Field(..., description="Базовый метаболизм (BMR)")
    tdee: float = Field(..., description="Суточная норма калорий (TDEE)")
    calories_for_weight_loss: Optional[Dict[str, Any]] = Field(None, description="КБЖУ для похудения")
    calories_for_gain: Optional[Dict[str, Any]] = Field(None, description="КБЖУ для набора мышц")
    calories_for_maintenance: Optional[Dict[str, Any]] = Field(None, description="КБЖУ для поддержания формы")


class SCalorieCalculationAdd(BaseModel):
    goal: GoalEnum = Field(..., description="Цель: weight_loss (похудение), muscle_gain (набор мышц), maintenance (поддержание формы)")
    gender: GenderEnum = Field(..., description="Пол: male (мужской), female (женский)")
    weight: float = Field(..., gt=0, description="Вес в кг")
    height: float = Field(..., gt=0, description="Рост в см")
    age: int = Field(..., gt=0, le=150, description="Возраст")
    activity_coefficient: ActivityCoefficientEnum = Field(
        ...,
        description="Коэффициент активности: 1.2 (сидячий), 1.375 (слабая), 1.55 (средняя), 1.725 (высокая), 1.9 (экстремальная)"
    )


class SCalorieCalculationUpdate(BaseModel):
    goal: Optional[GoalEnum] = Field(None, description="Цель")
    gender: Optional[GenderEnum] = Field(None, description="Пол")
    weight: Optional[float] = Field(None, gt=0, description="Вес в кг")
    height: Optional[float] = Field(None, gt=0, description="Рост в см")
    age: Optional[int] = Field(None, gt=0, le=150, description="Возраст")
    activity_coefficient: Optional[ActivityCoefficientEnum] = Field(None, description="Коэффициент активности")
    actual: Optional[bool] = Field(None, description="Актуальность записи")

