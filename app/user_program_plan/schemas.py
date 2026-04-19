from datetime import date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SUserProgramPlan(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    actual: bool = Field(..., description="Актуальная запись")
    user_uuid: Optional[str] = None
    anonymous_session_id: Optional[UUID] = Field(
        None, description="Анонимная сессия до привязки к пользователю"
    )
    train_at_gym: bool = False
    train_at_home: bool = False
    train_at_home_no_equipment: bool = False
    has_dumbbells: bool = False
    has_pullup_bar: bool = False
    has_bands: bool = False
    duration_target_minutes: int = Field(..., description="Целевая длительность тренировки (мин)")
    difficulty_level: str = Field(..., description="Уровень подготовки")
    program_goal: str = Field(..., description="Цель: fat_loss, mass_gain, maintenance")
    start_date: date = Field(..., description="Дата старта программы")
    training_days_per_week: int = Field(..., description="Тренировок в неделю")
    current_week_index: int = 1
    completed_heavy_training_count: Optional[int] = None
    recommended_next_training_date: Optional[date] = None
    anchor1_for_pull_uuid: Optional[str] = None
    anchor2_for_pull_uuid: Optional[str] = None
    anchor1_for_push_uuid: Optional[str] = None
    anchor2_for_push_uuid: Optional[str] = None
    anchor1_for_legs_uuid: Optional[str] = None
    anchor2_for_legs_uuid: Optional[str] = None


class SUserProgramPlanAdd(BaseModel):
    actual: bool = True
    user_uuid: Optional[str] = None
    train_at_gym: bool = False
    train_at_home: bool = False
    train_at_home_no_equipment: bool = False
    has_dumbbells: bool = False
    has_pullup_bar: bool = False
    has_bands: bool = False
    duration_target_minutes: int = Field(..., gt=0)
    difficulty_level: str = Field(..., min_length=1)
    program_goal: str = Field(..., min_length=1)
    start_date: date = Field(..., description="Дата старта программы")
    training_days_per_week: int = Field(..., ge=1, le=7)
    current_week_index: int = 1
    completed_heavy_training_count: Optional[int] = 0
    recommended_next_training_date: Optional[date] = None
    anchor1_for_pull_uuid: Optional[str] = None
    anchor2_for_pull_uuid: Optional[str] = None
    anchor1_for_push_uuid: Optional[str] = None
    anchor2_for_push_uuid: Optional[str] = None
    anchor1_for_legs_uuid: Optional[str] = None
    anchor2_for_legs_uuid: Optional[str] = None
    anonymous_session_id: Optional[UUID] = Field(
        None,
        description="Сохраняется в плане; у user_training и training с этим anonymous_session_id проставится user_program_plan_id созданного плана",
    )


class SUserProgramPlanUpdate(BaseModel):
    actual: Optional[bool] = None
    user_uuid: Optional[str] = None
    train_at_gym: Optional[bool] = None
    train_at_home: Optional[bool] = None
    train_at_home_no_equipment: Optional[bool] = None
    has_dumbbells: Optional[bool] = None
    has_pullup_bar: Optional[bool] = None
    has_bands: Optional[bool] = None
    duration_target_minutes: Optional[int] = None
    difficulty_level: Optional[str] = None
    program_goal: Optional[str] = None
    start_date: Optional[date] = None
    training_days_per_week: Optional[int] = None
    current_week_index: Optional[int] = None
    completed_heavy_training_count: Optional[int] = None
    recommended_next_training_date: Optional[date] = None
    anchor1_for_pull_uuid: Optional[str] = None
    anchor2_for_pull_uuid: Optional[str] = None
    anchor1_for_push_uuid: Optional[str] = None
    anchor2_for_push_uuid: Optional[str] = None
    anchor1_for_legs_uuid: Optional[str] = None
    anchor2_for_legs_uuid: Optional[str] = None
    anonymous_session_id: Optional[UUID] = None
