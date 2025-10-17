from datetime import datetime, date
from typing import Optional, List
import re
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
from uuid import UUID
from app.user_exercises.models import ExerciseStatus


class SUserExercise(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    program_id: Optional[int] = Field(None, description="ID программы")
    training_id: int = Field(..., description="ID тренировки")
    user_id: int = Field(..., description="ID пользователя")
    exercise_id: int = Field(..., description="ID упражнения")
    training_date: date = Field(..., description="Дата тренировки")
    status: ExerciseStatus = Field(..., description="Статус упражнения")
    set_number: int = Field(..., description="Номер подхода")
    weight: Optional[float] = Field(None, description="Вес в кг")
    reps: int = Field(..., description="Количество повторений")


class SUserExerciseAdd(BaseModel):
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_uuid: str = Field(..., description="UUID тренировки")
    user_uuid: str = Field(..., description="UUID пользователя")
    exercise_uuid: str = Field(..., description="UUID упражнения")
    training_date: date = Field(..., description="Дата тренировки")
    status: ExerciseStatus = Field(ExerciseStatus.ACTIVE, description="Статус упражнения")
    set_number: int = Field(1, ge=1, description="Номер подхода")
    weight: Optional[float] = Field(None, ge=0, description="Вес в кг")
    reps: int = Field(0, ge=0, description="Количество повторений")


class SUserExerciseUpdate(BaseModel):
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    exercise_uuid: Optional[str] = Field(None, description="UUID упражнения")
    training_date: Optional[date] = Field(None, description="Дата тренировки")
    status: Optional[ExerciseStatus] = Field(None, description="Статус упражнения")
    set_number: Optional[int] = Field(None, ge=1, description="Номер подхода")
    weight: Optional[float] = Field(None, ge=0, description="Вес в кг")
    reps: Optional[int] = Field(None, ge=0, description="Количество повторений")


class SBatchSetPassedRequest(BaseModel):
    """Схема для batch установки статуса PASSED"""
    user_exercise_uuids: List[UUID] = Field(
        ..., 
        min_items=1, 
        max_items=100,  # Ограничиваем размер batch для производительности
        description="Список UUID пользовательских упражнений для установки статуса PASSED"
    )
    
    @field_validator('user_exercise_uuids')
    @classmethod
    def validate_uuids(cls, v):
        if not v:
            raise ValueError('Список UUID не может быть пустым')
        if len(set(v)) != len(v):
            raise ValueError('UUID не должны повторяться')
        return v


class SBatchSetPassedResponse(BaseModel):
    """Схема ответа для batch установки статуса PASSED"""
    success_count: int = Field(..., description="Количество успешно обновленных упражнений")
    failed_count: int = Field(..., description="Количество неудачных обновлений")
    total_count: int = Field(..., description="Общее количество переданных UUID")
    success_uuids: List[UUID] = Field(..., description="Список успешно обновленных UUID")
    failed_uuids: List[UUID] = Field(..., description="Список неудачных UUID")
    errors: List[str] = Field(default_factory=list, description="Список ошибок")