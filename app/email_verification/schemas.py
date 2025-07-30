from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class SEmailVerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email для отправки подтверждения")


class SEmailVerificationResponse(BaseModel):
    message: str = Field(..., description="Сообщение о результате операции")


class SEmailVerificationVerify(BaseModel):
    token: str = Field(..., description="Токен подтверждения из email") 