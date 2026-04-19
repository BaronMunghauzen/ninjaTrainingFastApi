from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SExerciseBuilderPool(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    actual: bool = Field(..., description="Актуальная запись")
    exercise_reference_uuid: Optional[str] = None
    exercise_caption: Optional[str] = None
    difficulty_level: Optional[str] = None
    primary_muscle_group: Optional[str] = None
    auxiliary_muscle_groups: Optional[str] = None
    preferred_role: Optional[str] = None
    is_anchor_candidate: Optional[bool] = None
    anchor_priority_tier: Optional[str] = None
    uses_external_load: Optional[bool] = None
    default_min_reps: Optional[int] = None
    default_max_reps: Optional[int] = None
    default_min_sets: Optional[int] = None
    default_max_sets: Optional[int] = None
    default_rest_seconds: Optional[int] = None
    is_time_based: Optional[bool] = None
    default_duration_seconds_min: Optional[int] = None
    default_duration_seconds_max: Optional[int] = None
    estimated_time_per_set_seconds: Optional[int] = None
    variation_group_code: Optional[str] = None
    base_priority: Optional[int] = None
    goal_fat_loss_weight: Optional[int] = None
    goal_mass_gain_weight: Optional[int] = None
    goal_maintenance_weight: Optional[int] = None
    week1_weight: Optional[int] = None
    week2_weight: Optional[int] = None
    week3_weight: Optional[int] = None
    week4_weight: Optional[int] = None
    max_usage_per_28d: Optional[int] = None
    can_use_in_heavy_push: Optional[bool] = None
    can_use_in_heavy_pull: Optional[bool] = None
    can_use_in_heavy_legs: Optional[bool] = None
    can_use_in_light_recovery: Optional[bool] = None
    can_use_in_light_pump: Optional[bool] = None
    can_use_in_light_core: Optional[bool] = None
    can_be_secondary_in_heavy_push: Optional[bool] = None
    can_be_secondary_in_heavy_pull: Optional[bool] = None
    can_be_secondary_in_heavy_legs: Optional[bool] = None
    anchor_order_push: Optional[int] = None
    anchor_order_pull: Optional[int] = None
    anchor_order_legs: Optional[int] = None
    is_unilateral: Optional[bool] = None
    is_active: Optional[bool] = None
    anchor_priority_tier_push: Optional[str] = None
    anchor_priority_tier_pull: Optional[str] = None
    anchor_priority_tier_legs: Optional[str] = None
    slot_family: Optional[str] = None
    fatigue_cost: Optional[int] = None
    role_rank_in_slot: Optional[int] = None


class SExerciseBuilderPoolAdd(BaseModel):
    actual: bool = True
    exercise_reference_uuid: Optional[str] = None
    exercise_caption: Optional[str] = None
    difficulty_level: Optional[str] = None
    primary_muscle_group: Optional[str] = None
    auxiliary_muscle_groups: Optional[str] = None
    preferred_role: Optional[str] = None
    is_anchor_candidate: Optional[bool] = None
    anchor_priority_tier: Optional[str] = None
    uses_external_load: Optional[bool] = None
    default_min_reps: Optional[int] = None
    default_max_reps: Optional[int] = None
    default_min_sets: Optional[int] = None
    default_max_sets: Optional[int] = None
    default_rest_seconds: Optional[int] = None
    is_time_based: Optional[bool] = None
    default_duration_seconds_min: Optional[int] = None
    default_duration_seconds_max: Optional[int] = None
    estimated_time_per_set_seconds: Optional[int] = None
    variation_group_code: Optional[str] = None
    base_priority: Optional[int] = None
    goal_fat_loss_weight: Optional[int] = None
    goal_mass_gain_weight: Optional[int] = None
    goal_maintenance_weight: Optional[int] = None
    week1_weight: Optional[int] = None
    week2_weight: Optional[int] = None
    week3_weight: Optional[int] = None
    week4_weight: Optional[int] = None
    max_usage_per_28d: Optional[int] = None
    can_use_in_heavy_push: Optional[bool] = None
    can_use_in_heavy_pull: Optional[bool] = None
    can_use_in_heavy_legs: Optional[bool] = None
    can_use_in_light_recovery: Optional[bool] = None
    can_use_in_light_pump: Optional[bool] = None
    can_use_in_light_core: Optional[bool] = None
    can_be_secondary_in_heavy_push: Optional[bool] = None
    can_be_secondary_in_heavy_pull: Optional[bool] = None
    can_be_secondary_in_heavy_legs: Optional[bool] = None
    anchor_order_push: Optional[int] = None
    anchor_order_pull: Optional[int] = None
    anchor_order_legs: Optional[int] = None
    is_unilateral: Optional[bool] = None
    is_active: Optional[bool] = None
    anchor_priority_tier_push: Optional[str] = None
    anchor_priority_tier_pull: Optional[str] = None
    anchor_priority_tier_legs: Optional[str] = None
    slot_family: Optional[str] = None
    fatigue_cost: Optional[int] = None
    role_rank_in_slot: Optional[int] = None


class SExerciseBuilderPoolUpdate(BaseModel):
    actual: Optional[bool] = None
    exercise_reference_uuid: Optional[str] = None
    exercise_caption: Optional[str] = None
    difficulty_level: Optional[str] = None
    primary_muscle_group: Optional[str] = None
    preferred_role: Optional[str] = None
    is_anchor_candidate: Optional[bool] = None
    is_active: Optional[bool] = None
    base_priority: Optional[int] = None
    default_min_reps: Optional[int] = None
    default_max_reps: Optional[int] = None
    default_min_sets: Optional[int] = None
    default_max_sets: Optional[int] = None
    default_rest_seconds: Optional[int] = None
    estimated_time_per_set_seconds: Optional[int] = None
    variation_group_code: Optional[str] = None
    slot_family: Optional[str] = None
    fatigue_cost: Optional[int] = None
    role_rank_in_slot: Optional[int] = None
