"""
Модель промокодов
"""
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field, created_at, updated_at

if TYPE_CHECKING:
    from app.subscriptions.models import Payment
    from app.users.models import User


class PromoCode(Base):
    """Промокоды для скидок на подписки"""
    __tablename__ = "promo_codes"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    
    # Основная информация
    code: Mapped[str] = mapped_column(unique=True, nullable=False)  # Код промокода (уникальный)
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)  # ФИО (не обязательное)
    discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)  # Размер скидки в процентах
    
    # Стандартные поля
    actual: Mapped[bool] = mapped_column(default=True)  # Актуальность промокода
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    
    # Отношения
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="promo_code")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, code={self.code}, discount={self.discount_percent}%)"

