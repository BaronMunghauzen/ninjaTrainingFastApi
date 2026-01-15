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
    
    # Список UUID рецептов, из которых можно выбирать (JSON массив, None = все рецепты)
    allowed_recipe_uuids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Использовать все доступные рецепты
    use_all_recipes: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)
    
    # Целевые уровни КБЖУ (JSON объект с полями calories, proteins, fats, carbs)
    target_nutrition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON объект
    
    # Полный ответ от внешнего сервиса (сохраняется целиком)
    response_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON структура
    
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
            "allowed_recipe_uuids": json.loads(self.allowed_recipe_uuids) if self.allowed_recipe_uuids else None,
            "use_all_recipes": self.use_all_recipes,
            "target_nutrition": json.loads(self.target_nutrition) if self.target_nutrition else None,
            "response_data": json.loads(self.response_data) if self.response_data else None
        }

