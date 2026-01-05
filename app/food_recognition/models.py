from typing import TYPE_CHECKING, Optional
import json
from sqlalchemy import ForeignKey, Text, text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field
from datetime import datetime

if TYPE_CHECKING:
    from app.users.models import User
    from app.files.models import File


class FoodRecognition(Base):
    __tablename__ = "food_recognition"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    actual: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    
    # Связи
    image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Основные данные
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    json_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Полный ответ сервиса в JSON
    
    # Поля из recognized_foods[0]
    name: Mapped[Optional[str]] = mapped_column(nullable=True)  # recognized_foods[0].name
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)  # recognized_foods[0].confidence
    
    # nutrition_per_100g
    calories_per_100g: Mapped[Optional[float]] = mapped_column(nullable=True)
    proteins_per_100g: Mapped[Optional[float]] = mapped_column(nullable=True)
    fats_per_100g: Mapped[Optional[float]] = mapped_column(nullable=True)
    carbs_per_100g: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # portion_estimate
    weight_g: Mapped[Optional[float]] = mapped_column(nullable=True)
    volume_ml: Mapped[Optional[float]] = mapped_column(nullable=True)
    estimated_portion_size: Mapped[Optional[str]] = mapped_column(nullable=True)
    
    # total_nutrition
    calories_total: Mapped[Optional[float]] = mapped_column(nullable=True)
    proteins_total: Mapped[Optional[float]] = mapped_column(nullable=True)
    fats_total: Mapped[Optional[float]] = mapped_column(nullable=True)
    carbs_total: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Списки в JSON формате
    ingredients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON список
    recommendations_tip: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON список с type=tip
    recommendations_alternative: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON список с type=alternative
    micronutrients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON список
    
    # Остальные поля из корневого уровня ответа
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Связи
    user: Mapped["User"] = relationship("User")
    image: Mapped[Optional["File"]] = relationship("File")
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, uuid={self.uuid}, user_id={self.user_id})"
    
    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "actual": self.actual,
            "image_uuid": str(self.image.uuid) if self.image else None,
            "user_uuid": str(self.user.uuid) if self.user else None,
            "comment": self.comment,
            "json_response": json.loads(self.json_response) if self.json_response else None,
            "name": self.name,
            "confidence": self.confidence,
            "calories_per_100g": self.calories_per_100g,
            "proteins_per_100g": self.proteins_per_100g,
            "fats_per_100g": self.fats_per_100g,
            "carbs_per_100g": self.carbs_per_100g,
            "weight_g": self.weight_g,
            "volume_ml": self.volume_ml,
            "estimated_portion_size": self.estimated_portion_size,
            "calories_total": self.calories_total,
            "proteins_total": self.proteins_total,
            "fats_total": self.fats_total,
            "carbs_total": self.carbs_total,
            "ingredients": json.loads(self.ingredients) if self.ingredients else None,
            "recommendations_tip": json.loads(self.recommendations_tip) if self.recommendations_tip else None,
            "recommendations_alternative": json.loads(self.recommendations_alternative) if self.recommendations_alternative else None,
            "micronutrients": json.loads(self.micronutrients) if self.micronutrients else None,
            "message": self.message,
            "processing_time_seconds": self.processing_time_seconds
        }

