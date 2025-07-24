from enum import Enum
from typing import Optional, List

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, str_null_true, uuid_field
from datetime import date


class ExerciseStatus(str, Enum):
    PASSED = 'passed'
    SKIPPED = 'skipped'
    ACTIVE = 'active'
    BLOCKED_YET = 'blocked_yet'

# создаем модель таблицы тренировок
class UserExercise(Base):
    __tablename__ = "user_exercise"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    program_id: Mapped[Optional[int]] = mapped_column(ForeignKey("program.id"), nullable=True)
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id"))
    training_date: Mapped[date]
    status: Mapped[ExerciseStatus]
    set_number: Mapped[int] = mapped_column(default=1)  # Номер подхода
    weight: Mapped[Optional[float]] = mapped_column(nullable=True)  # Вес в кг
    reps: Mapped[int] = mapped_column(default=0)  # Количество повторений


    # Связи
    program: Mapped["Program"] = relationship("Program", back_populates="user_exercises")
    training: Mapped["Training"] = relationship("Training", back_populates="user_exercises")
    user: Mapped["User"] = relationship("User", back_populates="user_exercises")
    exercise: Mapped["Exercise"] = relationship("Exercise", back_populates="user_exercises")


    def __repr__(self):
        return (f"<UserExercise {self.id} (set={self.set_number}, "
                f"{self.weight}kg x{self.reps}, status={self.status})>")

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "program_id": self.program_id,
            "training_id": self.training_id,
            "user_id": self.user_id,
            "exercise_id": self.exercise_id,
            "training_date": self.training_date.isoformat(),
            "status": self.status.value,
            "set_number": self.set_number,
            "weight": self.weight,
            "reps": self.reps
        }