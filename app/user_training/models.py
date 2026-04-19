from enum import Enum
from typing import Optional, List, TYPE_CHECKING, Literal

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.exc import DetachedInstanceError
from app.database import Base, str_uniq, int_pk, str_null_true, uuid_field
from uuid import UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import date, datetime, timezone

if TYPE_CHECKING:
    from app.user_program.models import UserProgram
    from app.user_program_plan.models import UserProgramPlan
    from app.programs.models import Program
    from app.trainings.models import Training
    from app.users.models import User
    from app.achievements.models import Achievement


class TrainingStatus(str, Enum):
    PASSED = 'PASSED'
    SKIPPED = 'SKIPPED'
    ACTIVE = 'ACTIVE'
    BLOCKED_YET = 'BLOCKED_YET'
    
    def __str__(self):
        return self.value

# создаем модель таблицы тренировок
class UserTraining(Base):
    __tablename__ = 'user_training'

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    user_program_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_program.id"), nullable=True)
    program_id: Mapped[Optional[int]] = mapped_column(ForeignKey("program.id"), nullable=True)
    training_id: Mapped[Optional[int]] = mapped_column(ForeignKey("training.id"), nullable=True)
    user_program_plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_program_plan.id"), nullable=True)
    training_type: Mapped[Optional[str]] = mapped_column(nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    training_date: Mapped[date]
    status: Mapped[TrainingStatus]
    stage: Mapped[Optional[int]] = mapped_column(nullable=True, default=1)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    skipped_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(nullable=True)  # Длительность тренировки в минутах
    week: Mapped[Optional[int]] = mapped_column(nullable=True)  # Номер недели (1-4)
    weekday: Mapped[Optional[int]] = mapped_column(nullable=True)  # День программы (1-7)
    is_rest_day: Mapped[Optional[bool]] = mapped_column(nullable=True)  # Является ли днем отдыха
    anonymous_session_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Связи
    user_program: Mapped["UserProgram"] = relationship("UserProgram",
                                                       back_populates="user_trainings")
    program: Mapped["Program"] = relationship("Program", back_populates="user_trainings")
    training: Mapped["Training"] = relationship("Training", back_populates="user_trainings")
    user_program_plan: Mapped[Optional["UserProgramPlan"]] = relationship(
        "UserProgramPlan", back_populates="user_trainings"
    )
    user: Mapped["User"] = relationship("User", back_populates="user_trainings")
    achievements: Mapped[list["Achievement"]] = relationship("Achievement", back_populates="user_training")


    @property
    def user_program_uuid(self) -> Optional[str]:
        return str(self.user_program.uuid) if self.user_program else None

    @property
    def program_uuid(self) -> Optional[str]:
        return str(self.program.uuid) if self.program else None

    @property
    def training_uuid(self) -> Optional[str]:
        return str(self.training.uuid) if self.training else None

    @property
    def user_program_plan_uuid(self) -> Optional[str]:
        return str(self.user_program_plan.uuid) if self.user_program_plan else None

    @property
    def user_uuid(self) -> Optional[str]:
        return str(self.user.uuid) if self.user else None

    def __repr__(self):
        return (f"<UserTraining {self.id} (user={self.user_id}, "
                f"training={self.training_id}, status={self.status})>")

    def to_dict(self):
        # Преобразуем created_at в timezone-aware datetime (UTC)
        created_at_with_tz = None
        if self.created_at:
            # Если created_at naive (без часового пояса), добавляем UTC
            if self.created_at.tzinfo is None:
                created_at_with_tz = self.created_at.replace(tzinfo=timezone.utc)
            else:
                created_at_with_tz = self.created_at
            created_at_with_tz = created_at_with_tz.isoformat()
        
        return {
            "uuid": str(self.uuid),
            "user_program_id": self.user_program_id,
            "program_id": self.program_id,
            "training_id": self.training_id,
            "user_program_plan_id": self.user_program_plan_id,
            # Не трогаем lazy-отношение при detached-объектах (например, в публичных endpoint'ах по anonymous_session_id)
            # Иначе получаем: "lazy load operation ... cannot proceed".
            "user_program_plan_uuid": (
                self._safe_user_program_plan_uuid()
            ),
            "training_type": self.training_type,
            "user_id": self.user_id,
            "training_date": self.training_date.isoformat(),
            "status": self.status.value,
            "stage": self.stage or 1,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "skipped_at": self.skipped_at.isoformat() if self.skipped_at else None,
            "duration": self.duration,
            "week": self.week,
            "weekday": self.weekday,
            "is_rest_day": self.is_rest_day,
            "created_at": created_at_with_tz
        }

    def _safe_user_program_plan_uuid(self) -> Optional[str]:
        try:
            if getattr(self, "user_program_plan", None) is None:
                return None
            return str(self.user_program_plan.uuid) if self.user_program_plan else None
        except DetachedInstanceError:
            return None