from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SExerciseBuilderEquipment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    actual: bool = Field(..., description="Актуальная запись")
    exercise_builder_pool_uuid: Optional[str] = None
    equipment_code: Optional[str] = None
    exercise_caption: Optional[str] = None


class SExerciseBuilderEquipmentAdd(BaseModel):
    actual: bool = True
    exercise_builder_pool_uuid: Optional[str] = None
    equipment_code: Optional[str] = None
    exercise_caption: Optional[str] = None


class SExerciseBuilderEquipmentUpdate(BaseModel):
    actual: Optional[bool] = None
    exercise_builder_pool_uuid: Optional[str] = None
    equipment_code: Optional[str] = None
    exercise_caption: Optional[str] = None
