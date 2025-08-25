from typing import Optional, List, TYPE_CHECKING
import json

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, str_null_true, uuid_field
from datetime import date, datetime

if TYPE_CHECKING:
    from app.achievements.models import Achievement


# создаем модель таблицы тренировок
class UserProgram(Base):
    __tablename__ = "user_program"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    program_id: Mapped[Optional[int]] = mapped_column(ForeignKey("program.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=True)
    caption: Mapped[str]
    status: Mapped[str] = mapped_column(default='not_active')
    stopped_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    stage: Mapped[int]
    schedule_type: Mapped[str] = mapped_column(default='weekly')  # weekly, custom
    training_days: Mapped[Optional[str]] = mapped_column(nullable=True)  # JSON: [1,3,5] - дни недели (1=понедельник)
    start_date: Mapped[Optional[date]] = mapped_column(nullable=True)

    # Связи
    program: Mapped["Program"] = relationship("Program", back_populates="user_programs")
    user: Mapped["User"] = relationship("User", back_populates="user_programs")
    user_trainings: Mapped[list["UserTraining"]] = relationship("UserTraining", back_populates="user_program")
    achievements: Mapped[list["Achievement"]] = relationship("Achievement", back_populates="user_program")


    def __repr__(self):
        return f"{self.__class__.__name__}(uuid={self.uuid}, caption={self.caption!r})"

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "program_id": self.program_id,
            "user_id": self.user_id,
            "caption": self.caption,
            "status": self.status,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "stage": self.stage,
            "schedule_type": self.schedule_type,
            "training_days": self.training_days,
            "start_date": self.start_date.isoformat() if self.start_date else None
        }

    def get_training_days_list(self) -> List[int]:
        """Получить список дней тренировок"""
        if self.training_days:
            return json.loads(self.training_days)
        return [1, 3, 5]  # По умолчанию: пн, ср, пт