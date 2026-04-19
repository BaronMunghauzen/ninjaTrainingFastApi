from uuid import UUID
from typing import Optional, List

from pydantic import BaseModel, Field


class SAnonymousSessionCreateResponse(BaseModel):
    anonymous_session_id: UUID


class SPublicTrainingCreateRequest(BaseModel):
    """Запрос на создание анонимной pull‑тренировки."""

    anonymous_session_id: UUID = Field(..., description="Клиентский UUID анонимной сессии")

    difficulty_level: str = Field(..., description="beginner / intermediate / advanced")
    program_goal: str = Field(..., description="fat_loss / mass_gain / maintenance")

    train_at_gym: bool = False
    train_at_home: bool = True
    train_at_home_no_equipment: bool = False
    has_dumbbells: bool = False
    has_pullup_bar: bool = False
    has_bands: bool = False

    duration_target_minutes: int = 45
    training_days_per_week: int = 3


class SPublicExercise(BaseModel):
    exercise_uuid: str
    caption: str
    muscle_group: Optional[str] = None
    sets_count: Optional[int] = None
    reps_count: Optional[int] = None
    rest_time: Optional[int] = None


class SPublicTrainingWithExercises(BaseModel):
    """Расширенная информация о тренировке и её упражнениях для анонимной сессии."""

    training_uuid: str
    training_type: str
    caption: str
    description: Optional[str] = None
    difficulty_level: int
    duration: Optional[int] = None
    muscle_group: str
    stage: Optional[int] = None
    actual: Optional[bool] = None
    user_program_plan_uuid: Optional[str] = None
    anonymous_session_id: Optional[str] = None
    exercises: list[SPublicExercise]


class SPublicUserTrainingCreateRequest(BaseModel):
    """Создание анонимного user_training (факт тренировки)."""

    anonymous_session_id: UUID
    training_uuid: str
    training_date: Optional[str] = None  # ISO date, по умолчанию today на бэке
    status: str = "ACTIVE"
    training_type: Optional[str] = None


class SPublicUserExerciseCreateRequest(BaseModel):
    """Создание анонимного user_exercise (подхода)."""

    anonymous_session_id: UUID
    training_uuid: str
    exercise_uuid: str
    program_uuid: Optional[str] = None
    training_date: Optional[str] = None  # ISO date, по умолчанию today
    status: str = "active"
    set_number: int = 1
    weight: Optional[float] = None
    reps: int = 0
    duration_seconds: Optional[int] = Field(None, ge=0, description="Длительность подхода (сек)")


class SPublicTrainingCreateResponse(BaseModel):
    anonymous_session_id: UUID
    training_type: str
    training_uuid: str
    exercises: List[SPublicExercise]


class SPublicTrainingExerciseSummary(BaseModel):
    exercise_uuid: str
    caption: Optional[str] = None
    sets_count: int
    total_reps: int
    tonnage: float


class SPublicUserTrainingSummaryResponse(BaseModel):
    user_training_uuid: str
    training_uuid: Optional[str] = None
    training_duration_seconds: Optional[int] = None
    training_duration_minutes: Optional[float] = None
    completed_exercises_count: int
    total_sets: int
    total_reps: int
    total_tonnage: float
    exercises: list[SPublicTrainingExerciseSummary]

