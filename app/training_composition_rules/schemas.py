from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class STrainingCompositionRule(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    actual: bool = Field(..., description="Актуальная запись")
    training_type: Optional[str] = None
    program_goal: Optional[str] = None
    program_week_index: Optional[int] = None
    duration_target_minutes: Optional[int] = None
    location_scope: Optional[str] = None
    anchor_slots_count: Optional[int] = None
    main_slots_count: Optional[int] = None
    accessory_slots_count: Optional[int] = None
    core_slots_count: Optional[int] = None
    mobility_slots_count: Optional[int] = None
    allow_second_anchor: Optional[bool] = None
    anchor_sets: Optional[int] = None
    anchor_reps_min: Optional[int] = None
    anchor_reps_max: Optional[int] = None
    anchor_rest_seconds: Optional[int] = None
    main_sets: Optional[int] = None
    main_reps_min: Optional[int] = None
    main_reps_max: Optional[int] = None
    main_rest_seconds: Optional[int] = None
    accessory_sets: Optional[int] = None
    accessory_reps_min: Optional[int] = None
    accessory_reps_max: Optional[int] = None
    accessory_rest_seconds: Optional[int] = None
    core_sets: Optional[int] = None
    core_reps_min: Optional[int] = None
    core_reps_max: Optional[int] = None
    core_rest_seconds: Optional[int] = None
    mobility_sets: Optional[int] = None
    mobility_reps_min: Optional[int] = None
    mobility_reps_max: Optional[int] = None
    mobility_rest_seconds: Optional[int] = None
    notes_ru: Optional[str] = None


class STrainingCompositionRuleAdd(BaseModel):
    actual: bool = True
    training_type: Optional[str] = None
    program_goal: Optional[str] = None
    program_week_index: Optional[int] = None
    duration_target_minutes: Optional[int] = None
    location_scope: Optional[str] = None
    anchor_slots_count: Optional[int] = None
    main_slots_count: Optional[int] = None
    accessory_slots_count: Optional[int] = None
    core_slots_count: Optional[int] = None
    mobility_slots_count: Optional[int] = None
    allow_second_anchor: Optional[bool] = None
    anchor_sets: Optional[int] = None
    anchor_reps_min: Optional[int] = None
    anchor_reps_max: Optional[int] = None
    anchor_rest_seconds: Optional[int] = None
    main_sets: Optional[int] = None
    main_reps_min: Optional[int] = None
    main_reps_max: Optional[int] = None
    main_rest_seconds: Optional[int] = None
    accessory_sets: Optional[int] = None
    accessory_reps_min: Optional[int] = None
    accessory_reps_max: Optional[int] = None
    accessory_rest_seconds: Optional[int] = None
    core_sets: Optional[int] = None
    core_reps_min: Optional[int] = None
    core_reps_max: Optional[int] = None
    core_rest_seconds: Optional[int] = None
    mobility_sets: Optional[int] = None
    mobility_reps_min: Optional[int] = None
    mobility_reps_max: Optional[int] = None
    mobility_rest_seconds: Optional[int] = None
    notes_ru: Optional[str] = None


class STrainingCompositionRuleUpdate(BaseModel):
    actual: Optional[bool] = None
    training_type: Optional[str] = None
    program_goal: Optional[str] = None
    program_week_index: Optional[int] = None
    duration_target_minutes: Optional[int] = None
    location_scope: Optional[str] = None
    anchor_slots_count: Optional[int] = None
    main_slots_count: Optional[int] = None
    accessory_slots_count: Optional[int] = None
    core_slots_count: Optional[int] = None
    mobility_slots_count: Optional[int] = None
    allow_second_anchor: Optional[bool] = None
    anchor_sets: Optional[int] = None
    anchor_reps_min: Optional[int] = None
    anchor_reps_max: Optional[int] = None
    anchor_rest_seconds: Optional[int] = None
    main_sets: Optional[int] = None
    main_reps_min: Optional[int] = None
    main_reps_max: Optional[int] = None
    main_rest_seconds: Optional[int] = None
    accessory_sets: Optional[int] = None
    accessory_reps_min: Optional[int] = None
    accessory_reps_max: Optional[int] = None
    accessory_rest_seconds: Optional[int] = None
    core_sets: Optional[int] = None
    core_reps_min: Optional[int] = None
    core_reps_max: Optional[int] = None
    core_rest_seconds: Optional[int] = None
    mobility_sets: Optional[int] = None
    mobility_reps_min: Optional[int] = None
    mobility_reps_max: Optional[int] = None
    mobility_rest_seconds: Optional[int] = None
    notes_ru: Optional[str] = None
