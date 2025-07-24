from datetime import datetime, date
from typing import Optional, List
import re
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
from uuid import UUID


class SProgram(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    actual: bool = Field(..., description="Актуальность программы")
    category_uuid: str = Field(..., description="UUID категории")
    program_type: str = Field(..., description="Тип программы")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: str = Field(..., description="Название программы")
    description: str = Field(..., description="Описание программы")
    difficulty_level: Optional[int] = Field(None, description="Уровень сложности")
    order: int = Field(..., description="Порядок для сортировки")
    schedule_type: str = Field(..., description="Тип расписания (weekly, custom)")
    training_days: Optional[str] = Field(None, description="Дни тренировок в формате JSON")
    image_uuid: Optional[str] = Field(None, description="UUID изображения")


class SProgramAdd(BaseModel):
    actual: bool = Field(True, description="Актуальность программы")
    category_uuid: str = Field(..., description="UUID категории")
    program_type: str = Field(..., min_length=1, max_length=50, description="Тип программы")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: str = Field(..., min_length=1, max_length=100, description="Название программы")
    description: str = Field(..., min_length=1, max_length=500, description="Описание программы")
    difficulty_level: Optional[int] = Field(None, ge=1, le=10, description="Уровень сложности (1-10)")
    order: int = Field(0, description="Порядок для сортировки")
    schedule_type: str = Field('weekly', description="Тип расписания (weekly, custom)")
    training_days: Optional[str] = Field(None, description="Дни тренировок в формате JSON [1,3,5]")
    image_uuid: Optional[str] = Field(None, description="UUID изображения")


class SProgramUpdate(BaseModel):
    actual: Optional[bool] = Field(None, description="Актуальность программы")
    category_uuid: Optional[str] = Field(None, description="UUID категории")
    program_type: Optional[str] = Field(None, min_length=1, max_length=50, description="Тип программы")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: Optional[str] = Field(None, min_length=1, max_length=100, description="Название программы")
    description: Optional[str] = Field(None, min_length=1, max_length=500, description="Описание программы")
    difficulty_level: Optional[int] = Field(None, ge=1, le=10, description="Уровень сложности (1-10)")
    order: Optional[int] = Field(None, description="Порядок для сортировки")
    schedule_type: Optional[str] = Field(None, description="Тип расписания (weekly, custom)")
    training_days: Optional[str] = Field(None, description="Дни тренировок в формате JSON [1,3,5]")
    image_uuid: Optional[str] = Field(None, description="UUID изображения")
