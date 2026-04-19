from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field

if TYPE_CHECKING:
    from app.users.models import User
    from app.exercise_builder_pool.models import ExerciseBuilderPool
    from app.user_training.models import UserTraining


class UserProgramPlan(Base):
    """План программы тренировок пользователя (автоподбор)."""

    __tablename__ = "user_program_plan"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    actual: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    anonymous_session_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    train_at_gym: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    train_at_home: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    train_at_home_no_equipment: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    has_dumbbells: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    has_pullup_bar: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    has_bands: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))

    duration_target_minutes: Mapped[int] = mapped_column(nullable=False)
    difficulty_level: Mapped[str] = mapped_column(nullable=False)
    program_goal: Mapped[str] = mapped_column(nullable=False)  # fat_loss, mass_gain, maintenance
    start_date: Mapped[date] = mapped_column(nullable=False)
    training_days_per_week: Mapped[int] = mapped_column(nullable=False)
    current_week_index: Mapped[int] = mapped_column(nullable=False, default=1, server_default=text("1"))
    completed_heavy_training_count: Mapped[Optional[int]] = mapped_column(nullable=True, default=0, server_default=text("0"))
    recommended_next_training_date: Mapped[Optional[date]] = mapped_column(nullable=True)

    anchor1_for_pull_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exercise_builder_pool.id"), nullable=True
    )
    anchor2_for_pull_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exercise_builder_pool.id"), nullable=True
    )
    anchor1_for_push_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exercise_builder_pool.id"), nullable=True
    )
    anchor2_for_push_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exercise_builder_pool.id"), nullable=True
    )
    anchor1_for_legs_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exercise_builder_pool.id"), nullable=True
    )
    anchor2_for_legs_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exercise_builder_pool.id"), nullable=True
    )

    user: Mapped[Optional["User"]] = relationship("User")
    anchor1_for_pull: Mapped[Optional["ExerciseBuilderPool"]] = relationship(
        "ExerciseBuilderPool", foreign_keys=[anchor1_for_pull_id]
    )
    anchor2_for_pull: Mapped[Optional["ExerciseBuilderPool"]] = relationship(
        "ExerciseBuilderPool", foreign_keys=[anchor2_for_pull_id]
    )
    anchor1_for_push: Mapped[Optional["ExerciseBuilderPool"]] = relationship(
        "ExerciseBuilderPool", foreign_keys=[anchor1_for_push_id]
    )
    anchor2_for_push: Mapped[Optional["ExerciseBuilderPool"]] = relationship(
        "ExerciseBuilderPool", foreign_keys=[anchor2_for_push_id]
    )
    anchor1_for_legs: Mapped[Optional["ExerciseBuilderPool"]] = relationship(
        "ExerciseBuilderPool", foreign_keys=[anchor1_for_legs_id]
    )
    anchor2_for_legs: Mapped[Optional["ExerciseBuilderPool"]] = relationship(
        "ExerciseBuilderPool", foreign_keys=[anchor2_for_legs_id]
    )
    user_trainings: Mapped[list["UserTraining"]] = relationship(
        "UserTraining", back_populates="user_program_plan"
    )

    @property
    def user_uuid(self) -> Optional[str]:
        return str(self.user.uuid) if self.user else None

    @property
    def anchor1_for_pull_uuid(self) -> Optional[str]:
        return str(self.anchor1_for_pull.uuid) if self.anchor1_for_pull else None

    @property
    def anchor2_for_pull_uuid(self) -> Optional[str]:
        return str(self.anchor2_for_pull.uuid) if self.anchor2_for_pull else None

    @property
    def anchor1_for_push_uuid(self) -> Optional[str]:
        return str(self.anchor1_for_push.uuid) if self.anchor1_for_push else None

    @property
    def anchor2_for_push_uuid(self) -> Optional[str]:
        return str(self.anchor2_for_push.uuid) if self.anchor2_for_push else None

    @property
    def anchor1_for_legs_uuid(self) -> Optional[str]:
        return str(self.anchor1_for_legs.uuid) if self.anchor1_for_legs else None

    @property
    def anchor2_for_legs_uuid(self) -> Optional[str]:
        return str(self.anchor2_for_legs.uuid) if self.anchor2_for_legs else None

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, user_id={self.user_id})"
