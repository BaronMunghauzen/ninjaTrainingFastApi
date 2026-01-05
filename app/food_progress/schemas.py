from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime, date


class SDailyTarget(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    actual: bool = Field(..., description="Актуальность записи")
    user_uuid: Optional[UUID] = Field(None, description="UUID пользователя")
    target_calories: float = Field(..., description="Целевой уровень калорий")
    target_proteins: float = Field(..., description="Целевой уровень белков")
    target_fats: float = Field(..., description="Целевой уровень жиров")
    target_carbs: float = Field(..., description="Целевой уровень углеводов")


class SDailyTargetAdd(BaseModel):
    target_calories: float = Field(..., gt=0, description="Целевой уровень калорий")
    target_proteins: float = Field(..., gt=0, description="Целевой уровень белков")
    target_fats: float = Field(..., gt=0, description="Целевой уровень жиров")
    target_carbs: float = Field(..., gt=0, description="Целевой уровень углеводов")


class SDailyTargetUpdate(BaseModel):
    target_calories: Optional[float] = Field(None, gt=0, description="Целевой уровень калорий")
    target_proteins: Optional[float] = Field(None, gt=0, description="Целевой уровень белков")
    target_fats: Optional[float] = Field(None, gt=0, description="Целевой уровень жиров")
    target_carbs: Optional[float] = Field(None, gt=0, description="Целевой уровень углеводов")
    actual: Optional[bool] = Field(None, description="Актуальность записи")


class SMeal(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    actual: bool = Field(..., description="Актуальность записи")
    user_uuid: Optional[UUID] = Field(None, description="UUID пользователя")
    meal_datetime: datetime = Field(..., description="Дата и время приема пищи")
    calories: float = Field(..., description="Количество калорий в порции")
    proteins: float = Field(..., description="Количество белков в порции")
    fats: float = Field(..., description="Количество жиров в порции")
    carbs: float = Field(..., description="Количество углеводов в порции")
    target_calories: float = Field(..., description="Целевой уровень калорий")
    target_proteins: float = Field(..., description="Целевой уровень белков")
    target_fats: float = Field(..., description="Целевой уровень жиров")
    target_carbs: float = Field(..., description="Целевой уровень углеводов")
    remaining_calories: float = Field(..., description="Остаток калорий (или избыток если отрицательный)")
    remaining_proteins: float = Field(..., description="Остаток белков (или избыток если отрицательный)")
    remaining_fats: float = Field(..., description="Остаток жиров (или избыток если отрицательный)")
    remaining_carbs: float = Field(..., description="Остаток углеводов (или избыток если отрицательный)")


class SMealAdd(BaseModel):
    meal_datetime: datetime = Field(..., description="Дата и время приема пищи")
    calories: float = Field(..., ge=0, description="Количество калорий в порции")
    proteins: float = Field(..., ge=0, description="Количество белков в порции")
    fats: float = Field(..., ge=0, description="Количество жиров в порции")
    carbs: float = Field(..., ge=0, description="Количество углеводов в порции")


class SMealUpdate(BaseModel):
    meal_datetime: Optional[datetime] = Field(None, description="Дата и время приема пищи")
    calories: Optional[float] = Field(None, ge=0, description="Количество калорий в порции")
    proteins: Optional[float] = Field(None, ge=0, description="Количество белков в порции")
    fats: Optional[float] = Field(None, ge=0, description="Количество жиров в порции")
    carbs: Optional[float] = Field(None, ge=0, description="Количество углеводов в порции")
    actual: Optional[bool] = Field(None, description="Актуальность записи")


class SDailyProgress(BaseModel):
    """Прогресс за день"""
    progress_date: date = Field(..., alias="date", description="Дата", populate_by_name=True)
    eaten_calories: float = Field(..., description="Съедено калорий")
    eaten_proteins: float = Field(..., description="Съедено белков")
    eaten_fats: float = Field(..., description="Съедено жиров")
    eaten_carbs: float = Field(..., description="Съедено углеводов")
    target_calories: float = Field(..., description="Целевой уровень калорий")
    target_proteins: float = Field(..., description="Целевой уровень белков")
    target_fats: float = Field(..., description="Целевой уровень жиров")
    target_carbs: float = Field(..., description="Целевой уровень углеводов")
    remaining_calories: float = Field(..., description="Остаток калорий (или избыток если отрицательный)")
    remaining_proteins: float = Field(..., description="Остаток белков (или избыток если отрицательный)")
    remaining_fats: float = Field(..., description="Остаток жиров (или избыток если отрицательный)")
    remaining_carbs: float = Field(..., description="Остаток углеводов (или избыток если отрицательный)")

