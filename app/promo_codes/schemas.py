"""
Pydantic схемы для валидации данных промокодов
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class SPromoCodeResponse(BaseModel):
    """Схема ответа с информацией о промокоде"""
    model_config = ConfigDict(from_attributes=True)
    
    uuid: UUID = Field(..., description="UUID промокода")
    code: str = Field(..., description="Код промокода")
    full_name: Optional[str] = Field(None, description="ФИО")
    discount_percent: float = Field(..., description="Размер скидки в процентах")
    actual: bool = Field(..., description="Актуален ли промокод")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")


class SPromoCodeAdd(BaseModel):
    """Схема для создания промокода"""
    code: str = Field(..., description="Код промокода (уникальный)", min_length=1, max_length=100)
    full_name: Optional[str] = Field(None, description="ФИО")
    discount_percent: float = Field(..., description="Размер скидки в процентах", ge=0, le=100)
    actual: bool = Field(True, description="Актуален ли промокод")


class SPromoCodeUpdate(BaseModel):
    """Схема для обновления промокода"""
    code: Optional[str] = Field(None, description="Код промокода (уникальный)", min_length=1, max_length=100)
    full_name: Optional[str] = Field(None, description="ФИО")
    discount_percent: Optional[float] = Field(None, description="Размер скидки в процентах", ge=0, le=100)
    actual: Optional[bool] = Field(None, description="Актуален ли промокод")

