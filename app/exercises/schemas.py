from datetime import datetime, date
from typing import Optional, List, Dict, Any
import re
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
from uuid import UUID


class SExercise(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    exercise_type: str = Field(..., description="Тип упражнения")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: str = Field(..., description="Название упражнения")
    description: Optional[str] = Field(None, description="Описание упражнения")
    difficulty_level: int = Field(..., description="Уровень сложности")
    order: int = Field(..., description="Порядок для сортировки")
    muscle_group: str = Field(..., description="Группа мышц")
    sets_count: Optional[int] = Field(None, description="Количество подходов")
    reps_count: Optional[int] = Field(None, description="Количество повторений")
    rest_time: Optional[int] = Field(None, description="Время отдыха (сек)")
    with_weight: Optional[bool] = Field(None, description="С весом или без")
    weight: Optional[float] = Field(None, description="Вес упражнения (кг)")
    image_uuid: Optional[str] = Field(None, description="UUID изображения")
    video_uuid: Optional[str] = Field(None, description="UUID видео")
    video_preview_uuid: Optional[str] = Field(None, description="UUID превью видео")
    exercise_reference_uuid: Optional[str] = Field(None, description="UUID справочника упражнения")


class SExerciseAdd(BaseModel):
    exercise_type: str = Field(..., min_length=1, max_length=50, description="Тип упражнения")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: str = Field(..., min_length=1, max_length=100, description="Название упражнения")
    description: Optional[str] = Field(None, max_length=500, description="Описание упражнения")
    difficulty_level: int = Field(1, ge=1, le=10, description="Уровень сложности (1-10)")
    order: int = Field(0, description="Порядок для сортировки")
    muscle_group: str = Field(..., min_length=1, max_length=50, description="Группа мышц")
    sets_count: Optional[int] = Field(None, description="Количество подходов")
    reps_count: Optional[int] = Field(None, description="Количество повторений")
    rest_time: Optional[int] = Field(None, description="Время отдыха (сек)")
    with_weight: Optional[bool] = Field(None, description="С весом или без")
    weight: Optional[float] = Field(None, description="Вес упражнения (кг)")
    image_uuid: Optional[str] = Field(None, description="UUID изображения")
    video_uuid: Optional[str] = Field(None, description="UUID видео")
    video_preview_uuid: Optional[str] = Field(None, description="UUID превью видео")
    exercise_reference_uuid: Optional[str] = Field(None, description="UUID справочника упражнения")


class SExerciseUpdate(BaseModel):
    exercise_type: Optional[str] = Field(None, min_length=1, max_length=50, description="Тип упражнения")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: Optional[str] = Field(None, min_length=1, max_length=100, description="Название упражнения")
    description: Optional[str] = Field(None, max_length=500, description="Описание упражнения")
    difficulty_level: Optional[int] = Field(None, ge=1, le=10, description="Уровень сложности (1-10)")
    order: Optional[int] = Field(None, description="Порядок для сортировки")
    muscle_group: Optional[str] = Field(None, min_length=1, max_length=50, description="Группа мышц")
    sets_count: Optional[int] = Field(None, description="Количество подходов")
    reps_count: Optional[int] = Field(None, description="Количество повторений")
    rest_time: Optional[int] = Field(None, description="Время отдыха (сек)")
    with_weight: Optional[bool] = Field(None, description="С весом или без")
    weight: Optional[float] = Field(None, description="Вес упражнения (кг)")
    image_uuid: Optional[str] = Field(None, description="UUID изображения")
    video_uuid: Optional[str] = Field(None, description="UUID видео")
    video_preview_uuid: Optional[str] = Field(None, description="UUID превью видео")
    exercise_reference_uuid: Optional[str] = Field(None, description="UUID справочника упражнения")
