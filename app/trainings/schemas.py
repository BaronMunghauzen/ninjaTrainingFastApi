from datetime import datetime, date
from typing import Optional
import re
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
from uuid import UUID


class STraining(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_type: str = Field(..., description="Тип тренировки")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: str = Field(..., description="Название тренировки")
    description: Optional[str] = Field(None, description="Описание тренировки")
    difficulty_level: int = Field(..., description="Уровень сложности")
    duration: int = Field(..., description="Продолжительность в минутах")
    order: int = Field(..., description="Порядок для сортировки")
    muscle_group: str = Field(..., description="Группа мышц")
    stage: Optional[int] = Field(None, description="Этап тренировки")
    image_uuid: Optional[str] = Field(None, description="UUID изображения")
    actual: Optional[bool] = Field(False, description="Актуальная тренировка")


class STrainingAdd(BaseModel):
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_type: str = Field(..., min_length=1, max_length=50, description="Тип тренировки")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: str = Field(..., min_length=1, max_length=100, description="Название тренировки")
    description: Optional[str] = Field(None, max_length=500, description="Описание тренировки")
    difficulty_level: int = Field(1, ge=1, le=10, description="Уровень сложности (1-10)")
    duration: Optional[int] = Field(None, gt=0, description="Продолжительность в минутах")
    order: int = Field(0, description="Порядок для сортировки")
    muscle_group: str = Field(..., min_length=1, max_length=50, description="Группа мышц")
    stage: Optional[int] = Field(None, description="Этап тренировки")
    image_uuid: Optional[str] = Field(None, description="UUID изображения")
    actual: Optional[bool] = Field(False, description="Актуальная тренировка")


class STrainingUpdate(BaseModel):
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_type: Optional[str] = Field(None, min_length=1, max_length=50, description="Тип тренировки")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: Optional[str] = Field(None, min_length=1, max_length=100, description="Название тренировки")
    description: Optional[str] = Field(None, max_length=500, description="Описание тренировки")
    difficulty_level: Optional[int] = Field(None, ge=1, le=10, description="Уровень сложности (1-10)")
    duration: Optional[int] = Field(None, gt=0, description="Продолжительность в минутах")
    order: Optional[int] = Field(None, description="Порядок для сортировки")
    muscle_group: Optional[str] = Field(None, min_length=1, max_length=50, description="Группа мышц")
    stage: Optional[int] = Field(None, ge=1, description="Этап тренировки")
    image_uuid: Optional[str] = Field(None, description="UUID изображения")
    actual: Optional[bool] = Field(False, description="Актуальная тренировка")


class STrainingArchiveResponse(BaseModel):
    message: str = Field(..., description="Сообщение о результате операции")
    training_uuid: str = Field(..., description="UUID тренировки")
    actual: bool = Field(..., description="Статус актуальности тренировки")


class STrainingRestoreResponse(BaseModel):
    message: str = Field(..., description="Сообщение о результате операции")
    training_uuid: str = Field(..., description="UUID тренировки")
    actual: bool = Field(..., description="Статус актуальности тренировки")
