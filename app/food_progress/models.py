from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field
from datetime import datetime, date

if TYPE_CHECKING:
    from app.users.models import User


class DailyTarget(Base):
    """Целевые уровни КБЖУ на день"""
    __tablename__ = "daily_targets"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    actual: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    
    # Связи
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Целевые уровни
    target_calories: Mapped[float] = mapped_column(nullable=False)
    target_proteins: Mapped[float] = mapped_column(nullable=False)
    target_fats: Mapped[float] = mapped_column(nullable=False)
    target_carbs: Mapped[float] = mapped_column(nullable=False)
    
    # Связи
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, uuid={self.uuid}, user_id={self.user_id})"
    
    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "actual": self.actual,
            "user_uuid": str(self.user.uuid) if self.user else None,
            "target_calories": self.target_calories,
            "target_proteins": self.target_proteins,
            "target_fats": self.target_fats,
            "target_carbs": self.target_carbs
        }


class Meal(Base):
    """Приемы пищи"""
    __tablename__ = "meals"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    actual: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    
    # Связи
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Основные данные
    meal_datetime: Mapped[datetime] = mapped_column(nullable=False)  # Дата и время приема пищи
    name: Mapped[Optional[str]] = mapped_column(nullable=True)  # Название приема пищи
    
    # КБЖУ в порции
    calories: Mapped[float] = mapped_column(nullable=False)
    proteins: Mapped[float] = mapped_column(nullable=False)
    fats: Mapped[float] = mapped_column(nullable=False)
    carbs: Mapped[float] = mapped_column(nullable=False)
    
    # Целевые уровни (берутся из последней актуальной записи DailyTarget)
    target_calories: Mapped[float] = mapped_column(nullable=False)
    target_proteins: Mapped[float] = mapped_column(nullable=False)
    target_fats: Mapped[float] = mapped_column(nullable=False)
    target_carbs: Mapped[float] = mapped_column(nullable=False)
    
    # Остатки / избытки (расчетные поля)
    remaining_calories: Mapped[float] = mapped_column(nullable=False)  # Остаток калорий или избыток (если отрицательный)
    remaining_proteins: Mapped[float] = mapped_column(nullable=False)
    remaining_fats: Mapped[float] = mapped_column(nullable=False)
    remaining_carbs: Mapped[float] = mapped_column(nullable=False)
    
    # Связи
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, uuid={self.uuid}, user_id={self.user_id}, meal_datetime={self.meal_datetime})"
    
    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "actual": self.actual,
            "user_uuid": str(self.user.uuid) if self.user else None,
            "meal_datetime": self.meal_datetime.isoformat() if self.meal_datetime else None,
            "name": self.name,
            "calories": self.calories,
            "proteins": self.proteins,
            "fats": self.fats,
            "carbs": self.carbs,
            "target_calories": self.target_calories,
            "target_proteins": self.target_proteins,
            "target_fats": self.target_fats,
            "target_carbs": self.target_carbs,
            "remaining_calories": self.remaining_calories,
            "remaining_proteins": self.remaining_proteins,
            "remaining_fats": self.remaining_fats,
            "remaining_carbs": self.remaining_carbs
        }

