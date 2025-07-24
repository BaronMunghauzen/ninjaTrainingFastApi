from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, str_null_true, uuid_field
from datetime import date
from app.exercise_reference.models import ExerciseReference

if TYPE_CHECKING:
    from app.users.models import User
    from app.user_exercises.models import UserExercise
    from app.files.models import File


# создаем модель таблицы тренировок
class Exercise(Base):
    __tablename__ = 'exercise'

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    exercise_type: Mapped[str]
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"),
                                                   nullable=True)  # Необязательное, только для пользовательских упражнений
    caption: Mapped[str]  # Название
    description: Mapped[str] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[int] = mapped_column(default=1, server_default=text('1'))
    order: Mapped[int] = mapped_column(default=0, server_default=text('0'))
    muscle_group: Mapped[str]
    sets_count: Mapped[Optional[int]] = mapped_column(nullable=True)  # Количество подходов
    reps_count: Mapped[Optional[int]] = mapped_column(nullable=True)  # Количество повторений
    rest_time: Mapped[Optional[int]] = mapped_column(nullable=True)  # Время отдыха (секунды)
    with_weight: Mapped[Optional[bool]] = mapped_column(nullable=True)  # С весом или без
    weight: Mapped[Optional[float]] = mapped_column(nullable=True)  # Вес упражнения (необязательное)
    image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)
    video_preview_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)
    exercise_reference_id: Mapped[Optional[int]] = mapped_column(ForeignKey("exercise_reference.id"), nullable=True)

    # Связь с пользователем (только для пользовательских упражнений)
    user: Mapped[Optional["User"]] = relationship("User", back_populates="exercises")
    user_exercises: Mapped[list["UserExercise"]] = relationship("UserExercise", back_populates="exercise")

    # Связи с файлами
    image: Mapped[Optional["File"]] = relationship("File", foreign_keys=[image_id])
    video: Mapped[Optional["File"]] = relationship("File", foreign_keys=[video_id])
    video_preview: Mapped[Optional["File"]] = relationship("File", foreign_keys=[video_preview_id])
    exercise_reference: Mapped[Optional["ExerciseReference"]] = relationship("ExerciseReference")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, caption={self.caption!r}, type={self.exercise_type!r})"

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "exercise_type": self.exercise_type,
            "user_id": self.user_id,
            "caption": self.caption,
            "description": self.description,
            "difficulty_level": self.difficulty_level,
            "order": self.order,
            "muscle_group": self.muscle_group,
            "sets_count": self.sets_count,
            "reps_count": self.reps_count,
            "rest_time": self.rest_time,
            "with_weight": self.with_weight,
            "weight": self.weight,
            "image_uuid": str(self.image.uuid) if hasattr(self, 'image') and self.image else None,
            "video_uuid": str(self.video.uuid) if self.video else None,
            "video_preview_uuid": str(self.video_preview.uuid) if self.video_preview else None,
            "exercise_reference_uuid": str(self.exercise_reference.uuid) if self.exercise_reference else None
        }