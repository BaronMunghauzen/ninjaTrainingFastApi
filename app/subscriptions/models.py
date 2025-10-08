from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey, Numeric, Text, Integer, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from app.database import Base, int_pk, uuid_field

if TYPE_CHECKING:
    from app.users.models import User


class SubscriptionPlanEnum(str, Enum):
    """Типы тарифных планов"""
    month_1 = "month_1"    # 1 месяц
    month_3 = "month_3"    # 3 месяца
    month_6 = "month_6"    # 6 месяцев
    month_12 = "month_12"  # 12 месяцев


class PaymentStatusEnum(str, Enum):
    """Статусы платежей"""
    pending = "pending"       # Ожидает оплаты (создан, но ссылка еще не получена)
    processing = "processing" # В процессе (ссылка создана, ждем оплаты)
    succeeded = "succeeded"   # Успешно оплачен
    failed = "failed"        # Ошибка платежа
    cancelled = "cancelled"   # Отменен
    refunded = "refunded"    # Возвращен


class SubscriptionPlan(Base):
    """Тарифные планы подписок"""
    __tablename__ = "subscription_plans"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    
    # Основная информация
    plan_type: Mapped[SubscriptionPlanEnum] = mapped_column(
        SQLAlchemyEnum(SubscriptionPlanEnum), nullable=False, unique=True
    )
    name: Mapped[str]  # "1 месяц", "3 месяца" и т.д.
    duration_months: Mapped[int]  # 1, 3, 6, 12
    
    # Цены
    price: Mapped[float] = mapped_column(Numeric(10, 2))  # Полная цена
    price_per_month: Mapped[float] = mapped_column(Numeric(10, 2))  # Цена за месяц (для отображения выгоды)
    
    # Дополнительная информация
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"


class Payment(Base):
    """История платежей пользователей"""
    __tablename__ = "payments"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    
    # Связи
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id"))
    
    # Данные платежа
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[PaymentStatusEnum] = mapped_column(
        SQLAlchemyEnum(PaymentStatusEnum), default=PaymentStatusEnum.pending
    )
    
    # ID от платежной системы Точка
    payment_id: Mapped[str | None] = mapped_column(nullable=True)  # paymentLinkId от Точки
    operation_id: Mapped[str | None] = mapped_column(nullable=True)  # operationId от Точки (UUID операции)
    payment_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # URL для оплаты (paymentLink)
    
    # Дополнительная информация
    receipt_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # URL чека
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON с дополнительными данными
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Отношения
    user: Mapped["User"] = relationship("User", back_populates="payments")
    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, user_id={self.user_id}, status={self.status})"


class Subscription(Base):
    """Активные подписки пользователей"""
    __tablename__ = "subscriptions"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    
    # Связи
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("subscription_plans.id"), nullable=True)  # Для триала может быть NULL
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id"), nullable=True)  # Для триала может быть NULL
    
    # Даты подписки
    started_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    
    # Флаги
    is_trial: Mapped[bool] = mapped_column(default=False)  # Триальная подписка
    auto_renew: Mapped[bool] = mapped_column(default=False)  # Автопродление (для будущего функционала)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")
    payment: Mapped["Payment"] = relationship("Payment")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})"
