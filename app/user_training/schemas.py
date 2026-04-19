from datetime import datetime, date
from typing import Optional, Literal, Union
import re
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
from uuid import UUID
from app.user_training.models import TrainingStatus

# Определяем Literal тип для правильного отображения в Swagger
TrainingStatusLiteral = Literal["PASSED", "SKIPPED", "ACTIVE", "BLOCKED_YET"]
# Поддерживаем также нижний регистр для совместимости с клиентом
TrainingStatusLiteralLower = Literal["passed", "skipped", "active", "blocked_yet"]
TrainingStatusAny = Union[TrainingStatusLiteral, TrainingStatusLiteralLower]


class SUserTraining(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    user_program_uuid: Optional[str] = Field(None, description="UUID пользовательской программы")
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    user_program_plan_uuid: Optional[str] = Field(None, description="UUID плана программы пользователя")
    training_type: Optional[str] = Field(None, description="Тип тренировки (heavy_push, light_recovery и т.д.)")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    training_date: date = Field(..., description="Дата тренировки")
    status: TrainingStatusLiteral = Field(..., description="Статус тренировки")
    duration: Optional[int] = Field(None, description="Длительность тренировки в минутах")
    week: Optional[int] = Field(None, description="Номер недели (1-4)")
    weekday: Optional[int] = Field(None, description="День программы (1-7)")
    is_rest_day: Optional[bool] = Field(None, description="Является ли днем отдыха")


class SUserTrainingAdd(BaseModel):
    user_program_uuid: Optional[str] = Field(None, description="UUID пользовательской программы")
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    user_program_plan_uuid: Optional[str] = Field(None, description="UUID плана программы пользователя")
    training_type: Optional[str] = Field(None, description="Тип тренировки (heavy_push, light_recovery и т.д.)")
    user_uuid: str = Field(..., description="UUID пользователя")
    training_date: date = Field(..., description="Дата тренировки")
    status: TrainingStatusAny = Field("ACTIVE", description="Статус тренировки")
    week: Optional[int] = Field(None, description="Номер недели (1-4)")
    weekday: Optional[int] = Field(None, description="День программы (1-7)")
    is_rest_day: Optional[bool] = Field(None, description="Является ли днем отдыха")
    
    @field_validator('status')
    @classmethod
    def normalize_status(cls, v):
        """Нормализует статус к верхнему регистру"""
        if v is None:
            return None
        
        status_mapping = {
            "passed": "PASSED",
            "skipped": "SKIPPED", 
            "active": "ACTIVE",
            "blocked_yet": "BLOCKED_YET"
        }
        
        # Если уже в верхнем регистре, возвращаем как есть
        if v in ["PASSED", "SKIPPED", "ACTIVE", "BLOCKED_YET"]:
            return v
        
        # Если в нижнем регистре, преобразуем
        return status_mapping.get(v.lower(), v)


class SUserTrainingUpdate(BaseModel):
    user_program_uuid: Optional[str] = Field(None, description="UUID пользовательской программы")
    program_uuid: Optional[str] = Field(None, description="UUID программы")
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    user_program_plan_uuid: Optional[str] = Field(None, description="UUID плана программы пользователя")
    training_type: Optional[str] = Field(None, description="Тип тренировки")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    training_date: Optional[date] = Field(None, description="Дата тренировки")
    status: Optional[TrainingStatusAny] = Field(None, description="Статус тренировки")
    week: Optional[int] = Field(None, description="Номер недели (1-4)")
    weekday: Optional[int] = Field(None, description="День программы (1-7)")
    is_rest_day: Optional[bool] = Field(None, description="Является ли днем отдыха")
    
    @field_validator('status')
    @classmethod
    def normalize_status(cls, v):
        """Нормализует статус к верхнему регистру"""
        if v is None:
            return None
        
        status_mapping = {
            "passed": "PASSED",
            "skipped": "SKIPPED", 
            "active": "ACTIVE",
            "blocked_yet": "BLOCKED_YET"
        }
        
        # Если уже в верхнем регистре, возвращаем как есть
        if v in ["PASSED", "SKIPPED", "ACTIVE", "BLOCKED_YET"]:
            return v
        
        # Если в нижнем регистре, преобразуем
        return status_mapping.get(v.lower(), v)


class SUserTrainingExerciseSummary(BaseModel):
    exercise_uuid: str
    caption: Optional[str] = None
    sets_count: int
    total_reps: int
    tonnage: float


class SMetricTriple(BaseModel):
    """Текущее / прошлое / индекс сравнения (% изменения к прошлой тренировке)."""

    current: Optional[float | int] = None
    previous: Optional[float | int] = None
    index: Optional[float] = Field(
        None,
        description="Процент изменения относительно previous; null если нет прошлой сессии или деление не определено",
    )


class SSessionLoadIndex(BaseModel):
    current: Optional[float] = Field(
        None, description="Сводный индекс нагрузки (~100 = как в прошлый раз)"
    )
    previous: Optional[float] = Field(None, description="База для сравнения, обычно 100")
    index: Optional[float] = Field(
        None, description="Отклонение от базы в пунктах (current − previous)"
    )
    note: Optional[str] = Field(None, description="Как читать индекс")
    formula: Optional[str] = Field(None, description="Формула расчёта session_load_index")


class SSummaryCompareMeta(BaseModel):
    has_previous: bool
    previous_user_training_uuid: Optional[str] = None
    previous_training_date: Optional[str] = None
    match_mode: Optional[str] = Field(
        None, description="training_type | training_id — критерий поиска прошлой тренировки"
    )


class STopTonnageMove(BaseModel):
    exercise_reference_id: int
    tonnage: SMetricTriple


class SExerciseTonnageOutcomes(BaseModel):
    shared_exercise_references_count: int
    improved: int
    regressed: int
    unchanged: int
    net_balance: int = Field(..., description="improved − regressed по тоннажу")


class SSummaryCompareExtra(BaseModel):
    reps_per_set: SMetricTriple
    tonnage_per_completed_exercise: SMetricTriple
    tonnage_per_minute: SMetricTriple
    weighted_sets_share_pct: SMetricTriple = Field(
        ...,
        description="Доля подходов в упражнениях с весом, % от всех подходов",
    )
    weighted_tonnage_share_pct: SMetricTriple = Field(
        ...,
        description="Доля тоннажа с упражнений with_weight, % от общего тоннажа",
    )
    exercise_tonnage_outcomes: Optional[SExerciseTonnageOutcomes] = Field(
        None,
        description="Заполняется, если есть прошлая тренировка и общие exercise_reference",
    )
    top_exercise_tonnage_moves: Optional[list[STopTonnageMove]] = Field(
        None,
        description="До 8 упражнений с наибольшим изменением тоннажа (по |index|)",
    )


class SExerciseProgressRow(BaseModel):
    exercise_uuid: str
    exercise_id: int
    exercise_reference_id: Optional[int] = None
    caption: Optional[str] = None
    match_basis: str = Field(
        ...,
        description="exercise_reference_id — сквозное сравнение движения; exercise_id — только тот же ряд exercise",
    )
    note: str
    history_training_date: Optional[str] = None
    history_training_uuid: Optional[str] = None
    sets_count: SMetricTriple
    total_reps: SMetricTriple
    tonnage: SMetricTriple


class SUserTrainingSummaryWithComparisonResponse(BaseModel):
    user_training_uuid: str
    training_uuid: Optional[str] = None
    meta: SSummaryCompareMeta
    training_duration_seconds: SMetricTriple
    training_duration_minutes: SMetricTriple
    completed_exercises_count: SMetricTriple
    total_sets: SMetricTriple
    total_reps: SMetricTriple
    total_tonnage: SMetricTriple
    avg_tonnage_per_weighted_set: SMetricTriple = Field(
        ...,
        description=(
            "Средний тоннаж на подход: сначала по упражнениям with_weight=true; "
            "если таких подходов в сессии нет — по всей тренировке (total_tonnage/total_sets)"
        ),
    )
    reps_per_minute: SMetricTriple
    session_load_index: SSessionLoadIndex
    exercises: list[SUserTrainingExerciseSummary]
    exercise_progress: list[SExerciseProgressRow] = Field(
        ...,
        description="Прогресс по каждому упражнению vs последний раз это же движение в истории (не только прошлая тренировка целиком)",
    )
    extra: SSummaryCompareExtra
