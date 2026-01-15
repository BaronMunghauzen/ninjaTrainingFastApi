from typing import TYPE_CHECKING, Optional
import json
from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field
from datetime import datetime

if TYPE_CHECKING:
    from app.users.models import User
    from app.files.models import File
    from app.user_favorite_recipes.models import UserFavoriteRecipe


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    actual: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    
    # Связи
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)  # None для системных рецептов
    
    # Основные поля
    category: Mapped[Optional[str]] = mapped_column(nullable=True)  # Категория (например, "завтрак", "обед", "ужин", "супы")
    type: Mapped[Optional[str]] = mapped_column(nullable=True)  # Тип рецепта
    name: Mapped[Optional[str]] = mapped_column(nullable=True)  # Название рецепта
    ingredients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Словарь ключ-значение в формате JSON
    recipe: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Текст рецепта (до 2000 символов)
    
    # КБЖУ на 100г
    calories_per_100g: Mapped[Optional[float]] = mapped_column(nullable=True)
    proteins_per_100g: Mapped[Optional[float]] = mapped_column(nullable=True)
    fats_per_100g: Mapped[Optional[float]] = mapped_column(nullable=True)
    carbs_per_100g: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # КБЖУ на порцию
    calories_per_portion: Mapped[Optional[float]] = mapped_column(nullable=True)
    proteins_per_portion: Mapped[Optional[float]] = mapped_column(nullable=True)
    fats_per_portion: Mapped[Optional[float]] = mapped_column(nullable=True)
    carbs_per_portion: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Дополнительные поля
    portions_count: Mapped[Optional[int]] = mapped_column(nullable=True)  # Количество порций по умолчанию
    image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)
    cooking_time: Mapped[Optional[int]] = mapped_column(nullable=True)  # Время приготовления в минутах
    
    # Связи
    user: Mapped[Optional["User"]] = relationship("User")
    image: Mapped[Optional["File"]] = relationship("File")
    favorited_by_users: Mapped[list["UserFavoriteRecipe"]] = relationship("UserFavoriteRecipe", back_populates="recipe")
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, uuid={self.uuid}, name={self.name})"
    
    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "actual": self.actual,
            "user_uuid": str(self.user.uuid) if self.user else None,
            "category": self.category,
            "type": self.type,
            "name": self.name,
            "ingredients": json.loads(self.ingredients) if self.ingredients else None,
            "recipe": self.recipe,
            "calories_per_100g": self.calories_per_100g,
            "proteins_per_100g": self.proteins_per_100g,
            "fats_per_100g": self.fats_per_100g,
            "carbs_per_100g": self.carbs_per_100g,
            "calories_per_portion": self.calories_per_portion,
            "proteins_per_portion": self.proteins_per_portion,
            "fats_per_portion": self.fats_per_portion,
            "carbs_per_portion": self.carbs_per_portion,
            "portions_count": self.portions_count,
            "image_uuid": str(self.image.uuid) if self.image else None,
            "cooking_time": self.cooking_time
        }

