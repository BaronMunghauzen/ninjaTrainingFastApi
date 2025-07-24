from datetime import datetime, date
from typing import Optional
import re
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
from uuid import UUID



class SCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    caption: str = Field(..., description="Название категории")
    description: str = Field(..., description="Описание категории")
    order: int = Field(..., description="Порядок для сортировки")


class SCategoryAdd(BaseModel):
    caption: str = Field(..., min_length=1, max_length=50, description="Название категории")
    description: str = Field(..., min_length=1, max_length=200, description="Описание категории")
    order: int = Field(..., description="Порядок для сортировки")


class SCategoryUpdate(BaseModel):
    caption: Optional[str] = Field(None, min_length=1, max_length=50, description="Название категории")
    description: Optional[str] = Field(None, min_length=1, max_length=200, description="Описание категории")
    order: Optional[int] = Field(None, description="Порядок для сортировки")
