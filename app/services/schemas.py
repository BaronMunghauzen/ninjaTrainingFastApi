from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


class SupportRequestCreate(BaseModel):
    """Схема для создания обращения в службу поддержки"""
    request_type: str = Field(..., description="Тип обращения", min_length=1, max_length=100)
    message: str = Field(..., description="Сообщение", min_length=1, max_length=2000)
    user_uuid: UUID = Field(..., description="UUID пользователя")


class SupportRequestResponse(BaseModel):
    """Схема ответа для обращения в службу поддержки"""
    success: bool = Field(..., description="Статус отправки")
    message: str = Field(..., description="Сообщение о результате")

