from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, str_null_true, uuid_field
from datetime import date, datetime

if TYPE_CHECKING:
    from app.user_program.models import UserProgram
    from app.programs.models import Program
    from app.trainings.models import Training
    from app.users.models import User


class TrainingStatus(str, Enum):
    PASSED = 'passed'
    SKIPPED = 'skipped'
    ACTIVE = 'active'
    BLOCKED_YET = 'blocked_yet'

# создаем модель таблицы тренировок
class UserTraining(Base):
    __tablename__ = 'user_training'

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    user_program_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_program.id"), nullable=True)
    program_id: Mapped[Optional[int]] = mapped_column(ForeignKey("program.id"), nullable=True)
    training_id: Mapped[Optional[int]] = mapped_column(ForeignKey("training.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    training_date: Mapped[date]
    status: Mapped[TrainingStatus]
    stage: Mapped[Optional[int]] = mapped_column(nullable=True, default=1)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    skipped_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    week: Mapped[Optional[int]] = mapped_column(nullable=True)  # Номер недели (1-4)
    weekday: Mapped[Optional[int]] = mapped_column(nullable=True)  # День программы (1-7)
    is_rest_day: Mapped[Optional[bool]] = mapped_column(nullable=True)  # Является ли днем отдыха

    # Связи
    user_program: Mapped["UserProgram"] = relationship("UserProgram",
                                                       back_populates="user_trainings")
    program: Mapped["Program"] = relationship("Program", back_populates="user_trainings")
    training: Mapped["Training"] = relationship("Training", back_populates="user_trainings")
    user: Mapped["User"] = relationship("User", back_populates="user_trainings")


    def __repr__(self):
        return (f"<UserTraining {self.id} (user={self.user_id}, "
                f"training={self.training_id}, status={self.status})>")

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "user_program_id": self.user_program_id,
            "program_id": self.program_id,
            "training_id": self.training_id,
            "user_id": self.user_id,
            "training_date": self.training_date.isoformat(),
            "status": self.status.value,
            "stage": self.stage or 1,  # Возвращаем 1 как значение по умолчанию
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "skipped_at": self.skipped_at.isoformat() if self.skipped_at else None,
            "week": self.week,
            "weekday": self.weekday,
            "is_rest_day": self.is_rest_day
        }