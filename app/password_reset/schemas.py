from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email для сброса пароля")


class PasswordResetVerify(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    code: str = Field(..., min_length=6, max_length=6, description="6-значный код подтверждения")


class PasswordResetConfirm(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    code: str = Field(..., min_length=6, max_length=6, description="6-значный код подтверждения")
    new_password: str = Field(..., min_length=5, max_length=50, description="Новый пароль")


class PasswordResetResponse(BaseModel):
    message: str = Field(..., description="Сообщение о результате операции")


class PasswordResetTokenResponse(BaseModel):
    message: str = Field(..., description="Сообщение о результате операции")
    expires_at: datetime = Field(..., description="Время истечения токена")
