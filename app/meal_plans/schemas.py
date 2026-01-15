from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime


class STargetNutrition(BaseModel):
    """Целевые уровни КБЖУ"""
    calories: float = Field(..., ge=0, description="Целевой уровень калорий")
    proteins: float = Field(..., ge=0, description="Целевой уровень белков")
    fats: float = Field(..., ge=0, description="Целевой уровень жиров")
    carbs: float = Field(..., ge=0, description="Целевой уровень углеводов")


class SMealPlan(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    actual: bool = Field(..., description="Актуальность записи")
    user_uuid: Optional[UUID] = Field(None, description="UUID пользователя")
    meals_per_day: int = Field(..., description="Количество приемов пищи в день")
    days_count: int = Field(..., description="Количество дней программы")
    allowed_recipe_uuids: Optional[List[UUID]] = Field(None, description="Список разрешенных рецептов (None = все)")
    use_all_recipes: bool = Field(..., description="Использовать все доступные рецепты")
    target_nutrition: Optional[STargetNutrition] = Field(None, description="Целевые уровни КБЖУ")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Полный ответ от внешнего сервиса")


class SMealPlanAdd(BaseModel):
    """
    Создание программы питания
    
    Система автоматически определяет количество приёмов пищи:
    - Обязательные: breakfast, lunch, dinner (всегда создаются)
    - Опциональные: snack1, snack2, snack3 (добавляются при необходимости)
    - Максимум 6 приёмов пищи в день
    """
    days_count: int = Field(..., ge=1, le=90, description="Количество дней на которые составляется программа (1-90)")
    allowed_recipe_uuids: Optional[List[UUID]] = Field(None, description="Список UUID рецептов из которых выбирать (используется если use_all_recipes=False)")
    use_all_recipes: bool = Field(False, description="Использовать все доступные рецепты пользователя (системные и пользовательские)")
    target_nutrition: STargetNutrition = Field(..., description="Целевые уровни КБЖУ")


class SMealPlanUpdate(BaseModel):
    actual: Optional[bool] = Field(None, description="Актуальность записи")


class SMealPlanGenerationResult(BaseModel):
    """Результат генерации программы питания"""
    plan_uuid: UUID = Field(..., description="UUID созданной программы")
    message: str = Field(..., description="Сообщение о результате")

