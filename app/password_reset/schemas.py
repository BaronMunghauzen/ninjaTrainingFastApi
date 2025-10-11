from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email для сброса пароля")


class PasswordResetVerify(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    code: str = Field(..., min_length=4, max_length=6, description="Код подтверждения (4-6 цифр)")


class PasswordResetConfirm(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    code: str = Field(..., min_length=4, max_length=6, description="Код подтверждения (4-6 цифр)")
    new_password: str = Field(..., min_length=5, max_length=50, description="Новый пароль")


class PasswordResetResponse(BaseModel):
    message: str = Field(..., description="Сообщение о результате операции")


class PasswordResetTokenResponse(BaseModel):
    message: str = Field(..., description="Сообщение о результате операции")
    expires_at: datetime = Field(..., description="Время истечения токена")
