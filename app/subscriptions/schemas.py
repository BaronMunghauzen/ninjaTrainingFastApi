"""
Pydantic схемы для валидации данных подписок
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID


class SSubscriptionPlanResponse(BaseModel):
    """Схема ответа с информацией о тарифном плане"""
    model_config = ConfigDict(from_attributes=True)
    
    uuid: UUID = Field(..., description="UUID плана")
    plan_type: str = Field(..., description="Тип плана (month_1, month_3, etc.)")
    name: str = Field(..., description="Название плана")
    duration_months: int = Field(..., description="Длительность в месяцах")
    price: float = Field(..., description="Полная цена")
    price_per_month: float = Field(..., description="Цена за месяц")
    description: Optional[str] = Field(None, description="Описание плана")
    is_active: bool = Field(..., description="Активен ли план")


class SPaymentInitiate(BaseModel):
    """Схема для инициации платежа"""
    plan_uuid: UUID = Field(..., description="UUID тарифного плана")
    return_url: Optional[str] = Field(
        None,
        description="URL для возврата после оплаты (по умолчанию deep link)"
    )
    payment_mode: Optional[list[str]] = Field(
        None,
        description="Способы оплаты: sbp, card, tinkoff, dolyame (по умолчанию card и sbp)"
    )


class SPaymentResponse(BaseModel):
    """Схема ответа при создании платежа"""
    payment_uuid: UUID = Field(..., description="UUID платежа в системе")
    payment_url: str = Field(..., description="URL для оплаты в Точке")
    payment_link_id: str = Field(..., description="ID платёжной ссылки от Точки")
    operation_id: Optional[str] = Field(None, description="ID операции от Точки (UUID)")


class SPaymentStatus(BaseModel):
    """Схема статуса платежа"""
    status: str = Field(..., description="Статус платежа (pending/processing/succeeded/failed/cancelled)")
    amount: float = Field(..., description="Сумма платежа")
    created_at: datetime = Field(..., description="Дата создания платежа")
    paid_at: Optional[datetime] = Field(None, description="Дата оплаты")
    receipt_url: Optional[str] = Field(None, description="URL чека")


class SSubscriptionStatus(BaseModel):
    """Схема статуса подписки пользователя"""
    subscription_status: str = Field(..., description="Статус подписки (pending/active/expired)")
    subscription_until: Optional[date] = Field(None, description="Дата окончания подписки")
    is_trial: bool = Field(..., description="Триальная ли подписка")
    trial_used: bool = Field(..., description="Использован ли триальный период")
    days_remaining: Optional[int] = Field(None, description="Дней до окончания подписки")


class SSubscriptionResponse(BaseModel):
    """Схема ответа с информацией о подписке"""
    model_config = ConfigDict(from_attributes=True)
    
    uuid: UUID = Field(..., description="UUID подписки")
    user_id: int = Field(..., description="ID пользователя")
    started_at: datetime = Field(..., description="Дата начала подписки")
    expires_at: datetime = Field(..., description="Дата окончания подписки")
    is_trial: bool = Field(..., description="Триальная ли подписка")
    plan_name: Optional[str] = Field(None, description="Название плана")


class STrialActivation(BaseModel):
    """Схема ответа при активации триала"""
    message: str = Field(..., description="Сообщение")
    subscription_uuid: UUID = Field(..., description="UUID подписки")
    expires_at: datetime = Field(..., description="Дата окончания триала")
    is_trial: bool = Field(True, description="Триальная подписка")
