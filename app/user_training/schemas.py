from datetime import datetime, date
from typing import Optional, Literal, Union
import re
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
from uuid import UUID
from app.user_training.models import TrainingStatus

# Определяем Literal тип для правильного отображения в Swagger
TrainingStatusLiteral = Literal["PASSED", "SKIPPED", "ACTIVE", "BLOCKED_YET"]
# Поддерживаем также нижний регистр для совместимости с клиентом
TrainingStatusLiteralLower = Literal["passed", "skipped", "active", "blocked_yet"]
TrainingStatusAny = Union[TrainingStatusLiteral, TrainingStatusLiteralLower]


class SUserTraining(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    user_program_id: Optional[int] = Field(None, description="ID пользовательской программы")
    program_id: Optional[int] = Field(None, description="ID программы")
    training_id: Optional[int] = Field(None, description="ID тренировки")
    user_id: int = Field(..., description="ID пользователя")
    training_date: date = Field(..., description="Дата тренировки")
    status: TrainingStatusLiteral = Field(..., description="Статус тренировки")
    duration: Optional[int] = Field(None, description="Длительность тренировки в минутах")
    week: Optional[int] = Field(None, description="Номер недели (1-4)")
    weekday: Optional[int] = Field(None, description="День программы (1-7)")
    is_rest_day: Optional[bool] = Field(None, description="Является ли днем отдыха")


class SUserTrainingAdd(BaseModel):
    user_program_uuid: Optional[str] = Field(None, description="UUID пользовательской программы")
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    user_uuid: str = Field(..., description="UUID пользователя")
    training_date: date = Field(..., description="Дата тренировки")
    status: TrainingStatusAny = Field("ACTIVE", description="Статус тренировки")
    week: Optional[int] = Field(None, description="Номер недели (1-4)")
    weekday: Optional[int] = Field(None, description="День программы (1-7)")
    is_rest_day: Optional[bool] = Field(None, description="Является ли днем отдыха")
    
    @field_validator('status')
    @classmethod
    def normalize_status(cls, v):
        """Нормализует статус к верхнему регистру"""
        if v is None:
            return None
        
        status_mapping = {
            "passed": "PASSED",
            "skipped": "SKIPPED", 
            "active": "ACTIVE",
            "blocked_yet": "BLOCKED_YET"
        }
        
        # Если уже в верхнем регистре, возвращаем как есть
        if v in ["PASSED", "SKIPPED", "ACTIVE", "BLOCKED_YET"]:
            return v
        
        # Если в нижнем регистре, преобразуем
        return status_mapping.get(v.lower(), v)


class SUserTrainingUpdate(BaseModel):
    user_program_uuid: Optional[str] = Field(None, description="UUID пользовательской программы")
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    training_date: Optional[date] = Field(None, description="Дата тренировки")
    status: Optional[TrainingStatusAny] = Field(None, description="Статус тренировки")
    week: Optional[int] = Field(None, description="Номер недели (1-4)")
    weekday: Optional[int] = Field(None, description="День программы (1-7)")
    is_rest_day: Optional[bool] = Field(None, description="Является ли днем отдыха")
    
    @field_validator('status')
    @classmethod
    def normalize_status(cls, v):
        """Нормализует статус к верхнему регистру"""
        if v is None:
            return None
        
        status_mapping = {
            "passed": "PASSED",
            "skipped": "SKIPPED", 
            "active": "ACTIVE",
            "blocked_yet": "BLOCKED_YET"
        }
        
        # Если уже в верхнем регистре, возвращаем как есть
        if v in ["PASSED", "SKIPPED", "ACTIVE", "BLOCKED_YET"]:
            return v
        
        # Если в нижнем регистре, преобразуем
        return status_mapping.get(v.lower(), v)
