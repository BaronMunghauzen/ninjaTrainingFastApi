from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

class SExerciseReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="UUID справочника упражнения")
    exercise_type: Optional[str] = Field(None, description="Тип упражнения")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: str = Field(..., description="Название упражнения")
    description: Optional[str] = Field(None, description="Описание упражнения")
    technique_description: Optional[str] = Field(None, description="Техника выполнения упражнения")
    muscle_group: str = Field(..., description="Группа мышц")
    equipment_name: Optional[str] = Field(None, description="Название необходимого оборудования")
    auxiliary_muscle_groups: Optional[str] = Field(None, description="Вспомогательные группы мышц")
    image_uuid: Optional[str] = Field(None, description="UUID изображения (files)")
    video_uuid: Optional[str] = Field(None, description="UUID видео (files)")
    gif_uuid: Optional[str] = Field(None, description="UUID гифки (files)")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")

class SExerciseReferenceAdd(BaseModel):
    exercise_type: Optional[str] = Field(None, description="Тип упражнения")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: str = Field(..., min_length=1, max_length=100, description="Название упражнения")
    description: Optional[str] = Field(None, max_length=500, description="Описание упражнения")
    technique_description: Optional[str] = Field(None, max_length=1000, description="Техника выполнения упражнения")
    muscle_group: str = Field(..., min_length=1, max_length=50, description="Группа мышц")
    equipment_name: Optional[str] = Field(None, max_length=400, description="Название необходимого оборудования")
    auxiliary_muscle_groups: Optional[str] = Field(None, max_length=500, description="Вспомогательные группы мышц")
    image_uuid: Optional[str] = Field(None, description="UUID изображения (files)")
    video_uuid: Optional[str] = Field(None, description="UUID видео (files)")
    gif_uuid: Optional[str] = Field(None, description="UUID гифки (files)")

class SExerciseReferenceUpdate(BaseModel):
    exercise_type: Optional[str] = Field(None, description="Тип упражнения")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: Optional[str] = Field(None, min_length=1, max_length=100, description="Название упражнения")
    description: Optional[str] = Field(None, max_length=500, description="Описание упражнения")
    technique_description: Optional[str] = Field(None, max_length=1000, description="Техника выполнения упражнения")
    muscle_group: Optional[str] = Field(None, min_length=1, max_length=50, description="Группа мышц")
    equipment_name: Optional[str] = Field(None, max_length=400, description="Название необходимого оборудования")
    auxiliary_muscle_groups: Optional[str] = Field(None, max_length=500, description="Вспомогательные группы мышц")
    image_uuid: Optional[str] = Field(None, description="UUID изображения (files)")
    video_uuid: Optional[str] = Field(None, description="UUID видео (files)")
    gif_uuid: Optional[str] = Field(None, description="UUID гифки (files)")

class SPaginationResponse(BaseModel):
    items: list[dict] = Field(..., description="Список упражнений")
    total: int = Field(..., description="Общее количество упражнений")
    page: int = Field(..., description="Номер текущей страницы")
    size: int = Field(..., description="Размер страницы")
    pages: int = Field(..., description="Общее количество страниц")

class SExerciseSet(BaseModel):
    set_number: int = Field(..., description="Номер подхода")
    reps: int = Field(..., description="Количество повторений")
    weight: Optional[float] = Field(None, description="Вес")
    training_uuid: Optional[str] = Field(None, description="UUID тренировки")
    exercise_uuid: Optional[str] = Field(None, description="UUID упражнения")

class SExerciseHistory(BaseModel):
    training_date: str = Field(..., description="Дата тренировки")
    sets: list[SExerciseSet] = Field(..., description="Список подходов")

class SExerciseStatistics(BaseModel):
    exercise_reference_uuid: str = Field(..., description="UUID справочника упражнения")
    user_uuid: str = Field(..., description="UUID пользователя")
    max_sets_per_day: int = Field(..., description="Максимальное количество подходов в одном дне")
    total_training_days: int = Field(..., description="Общее количество дней тренировок по этому упражнению")
    history: list[SExerciseHistory] = Field(..., description="История выполнения упражнения")


class SExerciseFilters(BaseModel):
    """Схема для ответа с фильтрами упражнений"""
    muscle_groups: list[str] = Field(..., description="Список уникальных групп мышц")
    equipment_names: list[str] = Field(..., description="Список уникальных названий оборудования") 