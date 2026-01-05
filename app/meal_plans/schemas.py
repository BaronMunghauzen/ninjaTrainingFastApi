from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime


class SMealPlan(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    actual: bool = Field(..., description="Актуальность записи")
    user_uuid: Optional[UUID] = Field(None, description="UUID пользователя")
    meals_per_day: int = Field(..., description="Количество приемов пищи в день")
    days_count: int = Field(..., description="Количество дней программы")
    max_repeats_per_week: Optional[int] = Field(None, description="Максимальное количество повторов блюда в неделю")
    allowed_recipe_uuids: Optional[List[UUID]] = Field(None, description="Список разрешенных рецептов (None = все)")
    include_soup_in_lunch: Optional[bool] = Field(None, description="Включать ли суп в обед")
    target_calories: float = Field(..., description="Целевой уровень калорий")
    target_proteins: float = Field(..., description="Целевой уровень белков")
    target_fats: float = Field(..., description="Целевой уровень жиров")
    target_carbs: float = Field(..., description="Целевой уровень углеводов")
    plan_data: Dict[str, Any] = Field(..., description="Сгенерированная программа питания")
    recommendations: Optional[List[str]] = Field(None, description="Рекомендации и правила")


class SMealPlanAdd(BaseModel):
    meals_per_day: int = Field(..., ge=3, description="Количество приемов пищи в день (минимум 3: завтрак, обед, ужин)")
    days_count: int = Field(..., ge=1, le=90, description="Количество дней на которые составляется программа (1-90)")
    max_repeats_per_week: Optional[int] = Field(2, ge=1, description="Максимальное количество повторов одного блюда в неделю на один прием пищи")
    allowed_recipe_uuids: Optional[List[UUID]] = Field(None, description="Список UUID рецептов из которых выбирать (None = все доступные рецепты)")
    include_soup_in_lunch: bool = Field(True, description="Включать ли суп в обед (если True - обед будет состоять из супа + второго блюда, если False - только второе блюдо)")


class SMealPlanUpdate(BaseModel):
    actual: Optional[bool] = Field(None, description="Актуальность записи")


class SMealPlanGenerationResult(BaseModel):
    """Результат генерации программы питания"""
    plan_uuid: UUID = Field(..., description="UUID созданной программы")
    message: str = Field(..., description="Сообщение о результате")

