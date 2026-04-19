from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field

if TYPE_CHECKING:
    from app.exercise_reference.models import ExerciseReference
    from app.exercise_builder_equipment.models import ExerciseBuilderEquipment


class ExerciseBuilderPool(Base):
    __tablename__ = "exercise_builder_pool"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    actual: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    exercise_id: Mapped[Optional[int]] = mapped_column(ForeignKey("exercise_reference.id"), nullable=True)
    exercise_caption: Mapped[Optional[str]] = mapped_column(nullable=True)
    difficulty_level: Mapped[Optional[str]] = mapped_column(nullable=True)
    primary_muscle_group: Mapped[Optional[str]] = mapped_column(nullable=True)
    auxiliary_muscle_groups: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_role: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_anchor_candidate: Mapped[Optional[bool]] = mapped_column(nullable=True)
    anchor_priority_tier: Mapped[Optional[str]] = mapped_column(nullable=True)
    uses_external_load: Mapped[Optional[bool]] = mapped_column(nullable=True)
    default_min_reps: Mapped[Optional[int]] = mapped_column(nullable=True)
    default_max_reps: Mapped[Optional[int]] = mapped_column(nullable=True)
    default_min_sets: Mapped[Optional[int]] = mapped_column(nullable=True)
    default_max_sets: Mapped[Optional[int]] = mapped_column(nullable=True)
    default_rest_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    is_time_based: Mapped[Optional[bool]] = mapped_column(nullable=True)
    default_duration_seconds_min: Mapped[Optional[int]] = mapped_column(nullable=True)
    default_duration_seconds_max: Mapped[Optional[int]] = mapped_column(nullable=True)
    estimated_time_per_set_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    variation_group_code: Mapped[Optional[str]] = mapped_column(nullable=True)
    base_priority: Mapped[Optional[int]] = mapped_column(nullable=True)
    goal_fat_loss_weight: Mapped[Optional[int]] = mapped_column(nullable=True)
    goal_mass_gain_weight: Mapped[Optional[int]] = mapped_column(nullable=True)
    goal_maintenance_weight: Mapped[Optional[int]] = mapped_column(nullable=True)
    week1_weight: Mapped[Optional[int]] = mapped_column(nullable=True)
    week2_weight: Mapped[Optional[int]] = mapped_column(nullable=True)
    week3_weight: Mapped[Optional[int]] = mapped_column(nullable=True)
    week4_weight: Mapped[Optional[int]] = mapped_column(nullable=True)
    cooldown_sessions: Mapped[Optional[str]] = mapped_column(nullable=True)
    max_usage_per_28d: Mapped[Optional[int]] = mapped_column(nullable=True)
    can_use_in_heavy_push: Mapped[Optional[bool]] = mapped_column(nullable=True)
    can_use_in_heavy_pull: Mapped[Optional[bool]] = mapped_column(nullable=True)
    can_use_in_heavy_legs: Mapped[Optional[bool]] = mapped_column(nullable=True)
    can_use_in_light_recovery: Mapped[Optional[bool]] = mapped_column(nullable=True)
    can_use_in_light_pump: Mapped[Optional[bool]] = mapped_column(nullable=True)
    can_use_in_light_core: Mapped[Optional[bool]] = mapped_column(nullable=True)
    can_be_secondary_in_heavy_push: Mapped[Optional[bool]] = mapped_column(nullable=True)
    can_be_secondary_in_heavy_pull: Mapped[Optional[bool]] = mapped_column(nullable=True)
    can_be_secondary_in_heavy_legs: Mapped[Optional[bool]] = mapped_column(nullable=True)
    anchor_order_push: Mapped[Optional[int]] = mapped_column(nullable=True)
    anchor_order_pull: Mapped[Optional[int]] = mapped_column(nullable=True)
    anchor_order_legs: Mapped[Optional[int]] = mapped_column(nullable=True)
    is_unilateral: Mapped[Optional[bool]] = mapped_column(nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(nullable=True)
    source_analysis_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    anchor_priority_tier_push: Mapped[Optional[str]] = mapped_column(nullable=True)
    anchor_cycle_lock_recommended_push: Mapped[Optional[bool]] = mapped_column(nullable=True)
    anchor_priority_tier_pull: Mapped[Optional[str]] = mapped_column(nullable=True)
    anchor_cycle_lock_recommended_pull: Mapped[Optional[bool]] = mapped_column(nullable=True)
    anchor_priority_tier_legs: Mapped[Optional[str]] = mapped_column(nullable=True)
    anchor_cycle_lock_recommended_legs: Mapped[Optional[bool]] = mapped_column(nullable=True)
    slot_family: Mapped[Optional[str]] = mapped_column(nullable=True)
    fatigue_cost: Mapped[Optional[int]] = mapped_column(nullable=True)
    role_rank_in_slot: Mapped[Optional[int]] = mapped_column(nullable=True)

    exercise_reference: Mapped[Optional["ExerciseReference"]] = relationship("ExerciseReference")
    equipment: Mapped[list["ExerciseBuilderEquipment"]] = relationship(
        "ExerciseBuilderEquipment", back_populates="exercise_builder_pool"
    )

    @property
    def exercise_reference_uuid(self) -> Optional[str]:
        return str(self.exercise_reference.uuid) if self.exercise_reference else None

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, exercise_caption={self.exercise_caption!r})"
