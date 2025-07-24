from datetime import datetime, date
from typing import Optional, List
import re
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
from uuid import UUID


class SUserProgram(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    program_id: int = Field(..., description="ID программы")
    user_id: Optional[int] = Field(None, description="ID пользователя")
    caption: str = Field(..., description="Название пользовательской программы")
    status: str = Field(..., description="Статус программы")
    stopped_at: Optional[date] = Field(..., description="Дата остановки")
    stage: int = Field(..., description="Этап программы")
    schedule_type: str = Field(..., description="Тип расписания")
    training_days: Optional[str] = Field(None, description="Дни тренировок (JSON)")
    start_date: Optional[date] = Field(None, description="Дата начала")


class SUserProgramAdd(BaseModel):
    program_uuid: str = Field(..., description="UUID программы")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: str = Field(..., min_length=1, max_length=100, description="Название пользовательской программы")
    status: str = Field("active", description="Статус программы")
    stage: int = Field(1, ge=1, description="Этап программы")


class SUserProgramUpdate(BaseModel):
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: Optional[str] = Field(None, min_length=1, max_length=100, description="Название пользовательской программы")
    status: Optional[str] = Field(None, description="Статус программы")
    stopped_at: Optional[date] = Field(None, description="Дата остановки", examples=["2025-08-10"])
    stage: Optional[int] = Field(None, ge=1, description="Этап программы")
    schedule_type: Optional[str] = Field(None, description="Тип расписания")
    training_days: Optional[List[int]] = Field(None, description="Дни недели для тренировок")
