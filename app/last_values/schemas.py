from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime


class SLastValue(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    user_uuid: UUID = Field(..., description="UUID пользователя")
    name: str = Field(..., description="Название")
    code: str = Field(..., description="Код")
    value: str = Field(..., description="Значение")
    actual: bool = Field(..., description="Актуальность записи")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")


class SLastValueAdd(BaseModel):
    user_uuid: UUID = Field(..., description="UUID пользователя")
    name: str = Field(..., min_length=1, max_length=200, description="Название")
    code: str = Field(..., min_length=1, max_length=100, description="Код (уникальный для пользователя)")
    value: str = Field(..., description="Значение")


class SLastValueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Название")
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="Код")
    value: Optional[str] = Field(None, description="Значение")

