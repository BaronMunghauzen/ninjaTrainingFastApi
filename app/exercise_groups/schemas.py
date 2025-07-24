from datetime import datetime, date
from typing import Optional, List, Dict, Any
import re
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
from uuid import UUID


class SExerciseGroup(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    caption: str = Field(..., description="Название группы упражнений")
    description: Optional[str] = Field(None, description="Описание группы упражнений")
    exercises: Optional[List[str]] = Field(None, description="Список UUID упражнений")
    difficulty_level: int = Field(..., description="Уровень сложности")
    order: int = Field(..., description="Порядок для сортировки")
    muscle_group: Optional[str] = Field(None, description="Группа мышц")
    stage: Optional[int] = Field(None, description="Этап")
    image_uuid: Optional[str] = Field(None, description="UUID изображения")


class SExerciseGroupAdd(BaseModel):
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    caption: str = Field(..., min_length=1, max_length=100, description="Название группы упражнений")
    description: Optional[str] = Field(None, max_length=500, description="Описание группы упражнений")
    exercises: Optional[List[str]] = Field(None, description="Список UUID упражнений")
    difficulty_level: int = Field(1, ge=1, le=10, description="Уровень сложности (1-10)")
    order: int = Field(0, description="Порядок для сортировки")
    muscle_group: Optional[str] = Field(None, min_length=1, max_length=50, description="Группа мышц")
    stage: Optional[int] = Field(None, ge=1, description="Этап группы упражнений")
    image_uuid: Optional[str] = Field(None, description="UUID изображения")


class SExerciseGroupUpdate(BaseModel):
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    caption: Optional[str] = Field(None, min_length=1, max_length=100, description="Название группы упражнений")
    description: Optional[str] = Field(None, max_length=500, description="Описание группы упражнений")
    exercises: Optional[List[str]] = Field(None, description="Список UUID упражнений")
    difficulty_level: Optional[int] = Field(None, ge=1, le=10, description="Уровень сложности (1-10)")
    order: Optional[int] = Field(None, description="Порядок для сортировки")
    muscle_group: Optional[str] = Field(None, min_length=1, max_length=50, description="Группа мышц")
    stage: Optional[int] = Field(None, ge=1, description="Этап группы упражнений")
    image_uuid: Optional[str] = Field(None, description="UUID изображения") 