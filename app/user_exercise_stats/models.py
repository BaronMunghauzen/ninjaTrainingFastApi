from datetime import date, datetime
from typing import Optional, TYPE_CHECKING

from uuid import UUID
from sqlalchemy import ForeignKey, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base, int_pk, uuid_field

if TYPE_CHECKING:
    from app.users.models import User
    from app.exercise_reference.models import ExerciseReference


class UserExerciseStats(Base):
    """Агрегированная статистика по упражнению для пользователя (для быстрых рекомендаций)."""

    __tablename__ = "user_exercise_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "exercise_reference_id", name="uq_user_exercise_stats_user_exercise"),
    )

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    actual: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    exercise_reference_id: Mapped[int] = mapped_column(ForeignKey("exercise_reference.id"), nullable=False)

    last_used_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    total_usage_count: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    last_workout_uuid: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    last_training_type: Mapped[Optional[str]] = mapped_column(nullable=True)
    last_role: Mapped[Optional[str]] = mapped_column(nullable=True)
    last_sets_summary_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    best_weight_value: Mapped[Optional[float]] = mapped_column(nullable=True)
    best_reps_value: Mapped[Optional[int]] = mapped_column(nullable=True)
    best_duration_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    best_volume_value: Mapped[Optional[float]] = mapped_column(nullable=True)

    usage_ring_last_shift_date: Mapped[date] = mapped_column(nullable=False, default=date.today, server_default=text("CURRENT_DATE"))
    usage_day_0: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_1: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_2: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_3: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_4: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_5: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_6: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_7: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_8: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_9: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_10: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_11: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_12: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_13: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_14: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_15: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_16: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_17: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_18: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_19: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_20: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_21: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_22: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_23: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_24: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_25: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_26: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))
    usage_day_27: Mapped[int] = mapped_column(nullable=False, default=0, server_default=text("0"))

    def __repr__(self):
        return f"{self.__class__.__name__}(user_id={self.user_id}, exercise_reference_id={self.exercise_reference_id})"
