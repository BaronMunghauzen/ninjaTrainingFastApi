from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator
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
    def validate_phone_number(cls, value: str) -> str:
        if value is None:
            return value
        if not re.match(r'^\+\d{5,15}$', value):
            raise ValueError('Номер телефона должен начинаться с "+" и содержать от 5 до 15 цифр')
        return value