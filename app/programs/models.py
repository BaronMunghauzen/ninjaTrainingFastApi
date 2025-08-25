from typing import TYPE_CHECKING, Optional, List
import json

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, str_null_true, uuid_field
from datetime import date

if TYPE_CHECKING:
    from app.categories.models import Category
    from app.users.models import User
    from app.files.models import File
    from app.user_program.models import UserProgram
    from app.trainings.models import Training
    from app.user_training.models import UserTraining
    from app.user_exercises.models import UserExercise


# создаем модель таблицы программы тренировок
class Program(Base):
    __tablename__ = "program"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    actual: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    program_type: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=True)
    caption: Mapped[str]
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty_level: Mapped[Optional[int]] = mapped_column(default=1, server_default=text('1'), nullable=True)
    order: Mapped[int] = mapped_column(default=0, server_default=text('0'))
    schedule_type: Mapped[str] = mapped_column(default='weekly')  # weekly, custom
    training_days: Mapped[Optional[str]] = mapped_column(nullable=True)  # JSON: [1,3,5] - дни недели (1=понедельник)
    image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)

    # Определяем отношения: программа принадлежит одной категории
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="programs"
    )

    # Определяем отношения: программа принадлежит одному пользователю
    user: Mapped["User"] = relationship("User", back_populates="programs")

    # Связь с файлом изображения
    image: Mapped[Optional["File"]] = relationship("File")

    # Еще связь
    user_programs: Mapped[list["UserProgram"]] = relationship("UserProgram", back_populates="program")

    # Определяем отношения с тренировками
    trainings: Mapped[list["Training"]] = relationship("Training", back_populates="program")
    user_trainings: Mapped[list["UserTraining"]] = relationship("UserTraining", back_populates="program")

    user_exercises: Mapped[list["UserExercise"]] = relationship("UserExercise", back_populates="program")

    def __str__(self):
        return (f"{self.__class__.__name__}(id={self.id}, "
                f"uuid={self.uuid!r},"
                f"caption={self.caption!r},"
                f"program_type={self.program_type!r})")

    def __repr__(self):
        return str(self)

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "actual": self.actual,
            "category_uuid": str(self.category.uuid) if hasattr(self, 'category') and self.category and hasattr(self.category, 'uuid') else None,
            "program_type": self.program_type,
            "caption": self.caption,
            "description": self.description,
            "difficulty_level": self.difficulty_level,
            "order": self.order,
            "schedule_type": self.schedule_type,
            "training_days": self.training_days,
            "image_uuid": str(self.image.uuid) if hasattr(self, 'image') and self.image and hasattr(self.image, 'uuid') else None
        }

    def to_dict_safe(self):
        """
        Безопасная версия to_dict для использования без загрузки связанных объектов
        """
        return {
            "uuid": str(self.uuid),
            "actual": self.actual,
            "category_uuid": None,  # Не загружаем category в оптимизированных запросах
            "program_type": self.program_type,
            "caption": self.caption,
            "description": self.description,
            "difficulty_level": self.difficulty_level,
            "order": self.order,
            "schedule_type": self.schedule_type,
            "training_days": self.training_days,
            "image_uuid": str(self.image.uuid) if hasattr(self, 'image') and self.image and hasattr(self.image, 'uuid') else None,
            "category_id": self.category_id,
            "user_id": self.user_id
        }

    def get_training_days_list(self) -> List[int]:
        """Получить список дней тренировок"""
        if self.training_days:
            return json.loads(self.training_days)
        return [1, 3, 5]  # По умолчанию: пн, ср, пт