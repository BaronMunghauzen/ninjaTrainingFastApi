from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SUserSelectedTraining(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(..., description="UUID записи")
    actual: bool = Field(..., description="Показывать тренировку на фронте")
    user_uuid: UUID = Field(..., description="UUID пользователя")
    training_uuid: UUID = Field(..., description="UUID тренировки")
    caption: Optional[str] = Field(None, description="Заголовок тренировки")
    image_uuid: Optional[UUID] = Field(None, description="UUID изображения тренировки")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")


class SUserSelectedTrainingAdd(BaseModel):
    training_uuid: UUID = Field(..., description="UUID тренировки")
    actual: bool = Field(True, description="Показывать тренировку на фронте")


class SUserSelectedTrainingUpdate(BaseModel):
    actual: Optional[bool] = Field(None, description="Показывать тренировку на фронте")
