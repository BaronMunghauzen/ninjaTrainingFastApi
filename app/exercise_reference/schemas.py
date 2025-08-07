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
    muscle_group: str = Field(..., description="Группа мышц")
    image_uuid: Optional[str] = Field(None, description="UUID изображения (files)")
    video_uuid: Optional[str] = Field(None, description="UUID видео (files)")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")

class SExerciseReferenceAdd(BaseModel):
    exercise_type: Optional[str] = Field(None, description="Тип упражнения")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: str = Field(..., min_length=1, max_length=100, description="Название упражнения")
    description: Optional[str] = Field(None, max_length=500, description="Описание упражнения")
    muscle_group: str = Field(..., min_length=1, max_length=50, description="Группа мышц")
    image_uuid: Optional[str] = Field(None, description="UUID изображения (files)")
    video_uuid: Optional[str] = Field(None, description="UUID видео (files)")

class SExerciseReferenceUpdate(BaseModel):
    exercise_type: Optional[str] = Field(None, description="Тип упражнения")
    user_uuid: Optional[str] = Field(None, description="UUID пользователя")
    caption: Optional[str] = Field(None, min_length=1, max_length=100, description="Название упражнения")
    description: Optional[str] = Field(None, max_length=500, description="Описание упражнения")
    muscle_group: Optional[str] = Field(None, min_length=1, max_length=50, description="Группа мышц")
    image_uuid: Optional[str] = Field(None, description="UUID изображения (files)")
    video_uuid: Optional[str] = Field(None, description="UUID видео (files)") 