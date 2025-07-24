from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, str_null_true, uuid_field
from datetime import date

if TYPE_CHECKING:
    from app.programs.models import Program
    from app.users.models import User
    from app.files.models import File
    from app.exercise_groups.models import ExerciseGroup
    from app.user_training.models import UserTraining
    from app.user_exercises.models import UserExercise
    from app.exercise_reference.models import ExerciseReference


# создаем модель таблицы тренировок
class Training(Base):
    __tablename__ = "training"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    program_id: Mapped[Optional[int]] = mapped_column(ForeignKey("program.id"), nullable=True)
    training_type: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=True)
    caption: Mapped[str]
    description: Mapped[str] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[int] = mapped_column(default=1, server_default=text('1'))
    duration: Mapped[int]  # Продолжительность в минутах
    order: Mapped[int] = mapped_column(default=0, server_default=text('0'))
    muscle_group: Mapped[str]  # Группа мышц
    stage: Mapped[Optional[int]] = mapped_column(nullable=True)
    image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)
    actual: Mapped[Optional[bool]] = mapped_column(default=False, server_default=text('false'), nullable=True)

    # Связь с программой тренировок
    program: Mapped[Optional["Program"]] = relationship("Program", back_populates="trainings")

    # Связь с пользователем
    user: Mapped[Optional["User"]] = relationship("User", back_populates="trainings")

    # Связь с файлом изображения
    image: Mapped[Optional["File"]] = relationship("File")

    #Связь с группой тренировок
    exercise_groups: Mapped[List["ExerciseGroup"]] = relationship("ExerciseGroup", back_populates="training")

    user_trainings: Mapped[list["UserTraining"]] = relationship("UserTraining", back_populates="training")

    user_exercises: Mapped[list["UserExercise"]] = relationship("UserExercise", back_populates="training")


    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, caption={self.caption!r})"

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "training_type": self.training_type,
            "caption": self.caption,
            "description": self.description,
            "difficulty_level": self.difficulty_level,
            "duration": self.duration,
            "order": self.order,
            "muscle_group": self.muscle_group,
            "stage": self.stage,
            "image_uuid": str(self.image.uuid) if hasattr(self, 'image') and self.image else None,
            "actual": self.actual
        }