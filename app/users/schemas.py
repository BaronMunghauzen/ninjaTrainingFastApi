from datetime import datetime, date
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
import re


class SUserRegister(BaseModel):
    login: str = Field(..., description="Логин (уникальный)")
    email: EmailStr = Field(..., description="Электронная почта")
    password: str = Field(..., min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")


class SUserAuth(BaseModel):
    user_identity: str = Field(..., description="Email, логин или телефон")
    password: str = Field(..., min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")


class SUserUpdate(BaseModel):
    login: Optional[str] = Field(None, description="Логин (уникальный)")
    middle_name: Optional[str] = Field(None, description="Отчество")
    gender: Optional[Literal["male", "female"]] = Field(None, description="Пол")
    description: Optional[str] = Field(None, description="Описание")
    subscription_status: Optional[Literal["pending", "active", "expired"]] = Field(None, description="Статус подписки (pending/active/expired)")
    subscription_until: Optional[str] = Field(None, description="Дата до которой активна подписка (YYYY-MM-DD)")
    theme: Optional[Literal["light", "dark"]] = Field(None, description="Тема оформления (по умолчанию 'dark')")
    email: Optional[EmailStr] = Field(None, description="Электронная почта")
    phone_number: Optional[str] = Field(None, description="Номер телефона в международном формате, начинающийся с '+'")
    first_name: Optional[str] = Field(None, min_length=3, max_length=50, description="Имя, от 3 до 50 символов")
    last_name: Optional[str] = Field(None, min_length=3, max_length=50, description="Фамилия, от 3 до 50 символов")
    is_user: Optional[bool] = Field(None, description="Пользователь")
    is_admin: Optional[bool] = Field(None, description="Пользователь")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if v is not None:
            if not re.match(r'^\+[1-9]\d{1,14}$', v):
                raise ValueError("Номер телефона должен быть в международном формате, начинающийся с '+'")
        return v


class SUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: str = Field(..., description="Уникальный идентификатор")
    email: str = Field(..., description="Email пользователя")
    login: str = Field(..., description="Логин пользователя")
    first_name: Optional[str] = Field(None, description="Имя пользователя")
    last_name: Optional[str] = Field(None, description="Фамилия пользователя")
    middle_name: Optional[str] = Field(None, description="Отчество пользователя")
    phone_number: Optional[str] = Field(None, description="Номер телефона")
    gender: Optional[str] = Field(None, description="Пол пользователя")
    description: Optional[str] = Field(None, description="Описание пользователя")
    subscription_status: str = Field(..., description="Статус подписки")
    subscription_until: Optional[date] = Field(None, description="Дата окончания подписки")
    theme: str = Field(..., description="Тема интерфейса")
    is_user: bool = Field(..., description="Является ли пользователем")
    is_admin: bool = Field(..., description="Является ли администратором")
    # Новые поля для email verification
    email_verified: bool = Field(..., description="Подтвержден ли email")
    email_verification_sent_at: Optional[datetime] = Field(None, description="Время отправки подтверждения email")
    avatar_uuid: Optional[str] = Field(None, description="UUID аватара")
    score: int = Field(..., description="Рейтинг пользователя")


class BroadcastEmailRequest(BaseModel):
    subject: str = Field(..., min_length=1, description="Тема письма")
    body: str = Field(..., min_length=1, description="Текст письма (может быть HTML)")