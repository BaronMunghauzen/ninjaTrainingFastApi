from typing import Optional, List, Dict, Any, TYPE_CHECKING
import json

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, str_null_true, uuid_field
from datetime import date

if TYPE_CHECKING:
    from app.trainings.models import Training
    from app.files.models import File


# создаем модель таблицы групп тренировок (включает в себя несколько упражнений)
class ExerciseGroup(Base):
    __tablename__ = "exercise_group"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id"),
                                             nullable=True)  # Связь с тренировкой (необязательная)
    caption: Mapped[str]
    description: Mapped[str] = mapped_column(Text, nullable=True)
    exercises: Mapped[str] = mapped_column(Text, default="[]",
                                           server_default=text("'[]'"))  # Набор упражнений (JSON-строка)
    difficulty_level: Mapped[int] = mapped_column(default=1, server_default=text('1'))
    order: Mapped[int] = mapped_column(default=0, server_default=text('0'))
    muscle_group: Mapped[Optional[str]] = mapped_column(nullable=True)
    stage: Mapped[Optional[int]] = mapped_column(nullable=True)
    image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)

    # Связь с тренировкой (опциональная, так как training_id nullable)
    training: Mapped[Optional["Training"]] = relationship("Training", back_populates="exercise_groups")

    # Связь с файлом изображения
    image: Mapped[Optional["File"]] = relationship("File")


    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, caption={self.caption!r})"

    def get_exercises(self) -> List[str]:
        """Возвращает набор упражнений в виде списка UUID строк"""
        return json.loads(self.exercises)

    def set_exercises(self, exercises_list: List[str]) -> None:
        """Устанавливает набор упражнений из списка UUID строк"""
        self.exercises = json.dumps(exercises_list)

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "caption": self.caption,
            "description": self.description,
            "exercises": self.get_exercises(),
            "difficulty_level": self.difficulty_level,
            "order": self.order,
            "muscle_group": self.muscle_group,
            "stage": self.stage,
            "image_uuid": str(self.image.uuid) if hasattr(self, 'image') and self.image else None
        }