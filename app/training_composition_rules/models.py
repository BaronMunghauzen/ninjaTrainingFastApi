from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base, int_pk, uuid_field

if TYPE_CHECKING:
    pass


class TrainingCompositionRule(Base):
    __tablename__ = "training_composition_rules"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    actual: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    training_type: Mapped[Optional[str]] = mapped_column(nullable=True)
    program_goal: Mapped[Optional[str]] = mapped_column(nullable=True)
    program_week_index: Mapped[Optional[int]] = mapped_column(nullable=True)
    duration_target_minutes: Mapped[Optional[int]] = mapped_column(nullable=True)
    location_scope: Mapped[Optional[str]] = mapped_column(nullable=True)
    anchor_slots_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    main_slots_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    accessory_slots_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    core_slots_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    mobility_slots_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    allow_second_anchor: Mapped[Optional[bool]] = mapped_column(nullable=True)
    anchor_sets: Mapped[Optional[int]] = mapped_column(nullable=True)
    anchor_reps_min: Mapped[Optional[int]] = mapped_column(nullable=True)
    anchor_reps_max: Mapped[Optional[int]] = mapped_column(nullable=True)
    anchor_rest_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    main_sets: Mapped[Optional[int]] = mapped_column(nullable=True)
    main_reps_min: Mapped[Optional[int]] = mapped_column(nullable=True)
    main_reps_max: Mapped[Optional[int]] = mapped_column(nullable=True)
    main_rest_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    accessory_sets: Mapped[Optional[int]] = mapped_column(nullable=True)
    accessory_reps_min: Mapped[Optional[int]] = mapped_column(nullable=True)
    accessory_reps_max: Mapped[Optional[int]] = mapped_column(nullable=True)
    accessory_rest_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    core_sets: Mapped[Optional[int]] = mapped_column(nullable=True)
    core_reps_min: Mapped[Optional[int]] = mapped_column(nullable=True)
    core_reps_max: Mapped[Optional[int]] = mapped_column(nullable=True)
    core_rest_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    mobility_sets: Mapped[Optional[int]] = mapped_column(nullable=True)
    mobility_reps_min: Mapped[Optional[int]] = mapped_column(nullable=True)
    mobility_reps_max: Mapped[Optional[int]] = mapped_column(nullable=True)
    mobility_rest_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    notes_ru: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, training_type={self.training_type!r})"
