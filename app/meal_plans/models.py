from typing import TYPE_CHECKING, Optional
import json
from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field
from datetime import datetime, date

if TYPE_CHECKING:
    from app.users.models import User


class MealPlan(Base):
    """Программы питания"""
    __tablename__ = "meal_plans"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    actual: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    
    # Связи
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Параметры создания программы
    meals_per_day: Mapped[int] = mapped_column(nullable=False)  # Количество приемов пищи в день (минимум 3)
    days_count: Mapped[int] = mapped_column(nullable=False)  # Количество дней программы
    max_repeats_per_week: Mapped[int] = mapped_column(nullable=True, default=2)  # Максимальное количество повторов блюда в неделю на один прием пищи
    
    # Список UUID рецептов, из которых можно выбирать (JSON массив, None = все рецепты)
    allowed_recipe_uuids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Включать ли суп в обед
    include_soup_in_lunch: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    
    # Целевые уровни КБЖУ (из последнего актуального расчета или целевого уровня)
    target_calories: Mapped[float] = mapped_column(nullable=False)
    target_proteins: Mapped[float] = mapped_column(nullable=False)
    target_fats: Mapped[float] = mapped_column(nullable=False)
    target_carbs: Mapped[float] = mapped_column(nullable=False)
    
    # Сгенерированная программа (JSON структура с днями и приемами пищи)
    plan_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON структура
    
    # Дополнительные правила и рекомендации
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON список правил
    
    # Связи
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, uuid={self.uuid}, user_id={self.user_id}, days={self.days_count})"
    
    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "actual": self.actual,
            "user_uuid": str(self.user.uuid) if self.user else None,
            "meals_per_day": self.meals_per_day,
            "days_count": self.days_count,
            "max_repeats_per_week": self.max_repeats_per_week,
            "allowed_recipe_uuids": json.loads(self.allowed_recipe_uuids) if self.allowed_recipe_uuids else None,
            "include_soup_in_lunch": self.include_soup_in_lunch,
            "target_calories": self.target_calories,
            "target_proteins": self.target_proteins,
            "target_fats": self.target_fats,
            "target_carbs": self.target_carbs,
            "plan_data": json.loads(self.plan_data) if self.plan_data else None,
            "recommendations": json.loads(self.recommendations) if self.recommendations else None
        }

