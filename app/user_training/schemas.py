from datetime import datetime, date
from typing import Optional
import re
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
from uuid import UUID
from app.user_training.models import TrainingStatus


class SUserTraining(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    user_program_id: Optional[int] = Field(None, description="ID пользовательской программы")
    program_id: Optional[int] = Field(None, description="ID программы")
    training_id: Optional[int] = Field(None, description="ID тренировки")
    user_id: int = Field(..., description="ID пользователя")
    training_date: date = Field(..., description="Дата тренировки")
    status: TrainingStatus = Field(..., description="Статус тренировки")
    week: Optional[int] = Field(None, description="Номер недели (1-4)")
    weekday: Optional[int] = Field(None, description="День программы (1-7)")
    is_rest_day: Optional[bool] = Field(None, description="Является ли днем отдыха")


class SUserTrainingAdd(BaseModel):
    user_program_uuid: Optional[str] = Field(None, description="UUID пользовательской программы")
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    user_uuid: str = Field(..., description="UUID пользователя")
    training_date: date = Field(..., description="Дата тренировки")
    status: TrainingStatus = Field(TrainingStatus.ACTIVE, description="Статус тренировки")
    week: Optional[int] = Field(None, description="Номер недели (1-4)")
    weekday: Optional[int] = Field(None, description="День программы (1-7)")
    is_rest_day: Optional[bool] = Field(None, description="Является ли днем отдыха")


class SUserTrainingUpdate(BaseModel):
    user_program_uuid: Optional[str] = Field(None, description="UUID пользовательской программы")
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    training_date: Optional[date] = Field(None, description="Дата тренировки")
    status: Optional[TrainingStatus] = Field(None, description="Статус тренировки")
    week: Optional[int] = Field(None, description="Номер недели (1-4)")
    weekday: Optional[int] = Field(None, description="День программы (1-7)")
    is_rest_day: Optional[bool] = Field(None, description="Является ли днем отдыха")
