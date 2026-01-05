from typing import TYPE_CHECKING, Optional
import json
from sqlalchemy import ForeignKey, Text, text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from app.users.models import User


class GoalEnum(str, Enum):
    """Цели пользователя"""
    weight_loss = "weight_loss"  # Похудение
    muscle_gain = "muscle_gain"  # Набор мышц
    maintenance = "maintenance"  # Поддержание формы


class GenderEnum(str, Enum):
    """Пол пользователя"""
    male = "male"  # Мужской
    female = "female"  # Женский


class ActivityCoefficientEnum(str, Enum):
    """Коэффициенты активности"""
    sedentary = "1.2"  # Сидячий образ жизни
    light = "1.375"  # Слабая активность
    moderate = "1.55"  # Средняя активность
    high = "1.725"  # Высокая активность
    extreme = "1.9"  # Экстремальная активность


class CalorieCalculation(Base):
    __tablename__ = "calorie_calculations"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    actual: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    
    # Связи
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Параметры запроса
    goal: Mapped[GoalEnum] = mapped_column(SQLAlchemyEnum(GoalEnum), nullable=False)
    gender: Mapped[GenderEnum] = mapped_column(SQLAlchemyEnum(GenderEnum), nullable=False)
    weight: Mapped[float] = mapped_column(nullable=False)  # Вес в кг
    height: Mapped[float] = mapped_column(nullable=False)  # Рост в см
    age: Mapped[int] = mapped_column(nullable=False)  # Возраст
    activity_coefficient: Mapped[str] = mapped_column(nullable=False)  # Коэффициент активности как строка
    
    # Результаты расчетов
    bmr: Mapped[float] = mapped_column(nullable=False)  # Базовый метаболизм
    tdee: Mapped[float] = mapped_column(nullable=False)  # Суточная норма калорий
    
    # КБЖУ для разных целей (в формате JSON)
    calories_for_weight_loss: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON с калориями, белками, жирами, углеводами
    calories_for_gain: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON для набора мышц
    calories_for_maintenance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON для поддержания
    
    # Связи
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, uuid={self.uuid}, user_id={self.user_id}, goal={self.goal.value})"
    
    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "actual": self.actual,
            "user_uuid": str(self.user.uuid) if self.user else None,
            "goal": self.goal.value,
            "gender": self.gender.value,
            "weight": self.weight,
            "height": self.height,
            "age": self.age,
            "activity_coefficient": self.activity_coefficient,
            "bmr": self.bmr,
            "tdee": self.tdee,
            "calories_for_weight_loss": json.loads(self.calories_for_weight_loss) if self.calories_for_weight_loss else None,
            "calories_for_gain": json.loads(self.calories_for_gain) if self.calories_for_gain else None,
            "calories_for_maintenance": json.loads(self.calories_for_maintenance) if self.calories_for_maintenance else None
        }

