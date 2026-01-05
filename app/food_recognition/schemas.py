from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime


class SFoodRecognition(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    actual: bool = Field(..., description="Актуальность записи")
    image_uuid: Optional[UUID] = Field(None, description="UUID изображения")
    user_uuid: Optional[UUID] = Field(None, description="UUID пользователя")
    comment: Optional[str] = Field(None, description="Комментарий")
    json_response: Optional[Dict[str, Any]] = Field(None, description="Полный ответ сервиса")
    name: Optional[str] = Field(None, description="Название распознанной еды")
    confidence: Optional[float] = Field(None, description="Уверенность распознавания")
    calories_per_100g: Optional[float] = Field(None, description="Калории на 100г")
    proteins_per_100g: Optional[float] = Field(None, description="Белки на 100г")
    fats_per_100g: Optional[float] = Field(None, description="Жиры на 100г")
    carbs_per_100g: Optional[float] = Field(None, description="Углеводы на 100г")
    weight_g: Optional[float] = Field(None, description="Вес в граммах")
    volume_ml: Optional[float] = Field(None, description="Объем в миллилитрах")
    estimated_portion_size: Optional[str] = Field(None, description="Размер порции")
    calories_total: Optional[float] = Field(None, description="Общие калории")
    proteins_total: Optional[float] = Field(None, description="Общие белки")
    fats_total: Optional[float] = Field(None, description="Общие жиры")
    carbs_total: Optional[float] = Field(None, description="Общие углеводы")
    ingredients: Optional[List[Dict[str, Any]]] = Field(None, description="Ингредиенты")
    recommendations_tip: Optional[List[Dict[str, Any]]] = Field(None, description="Рекомендации-советы")
    recommendations_alternative: Optional[List[Dict[str, Any]]] = Field(None, description="Рекомендации-альтернативы")
    micronutrients: Optional[List[Dict[str, Any]]] = Field(None, description="Микронутриенты")
    message: Optional[str] = Field(None, description="Сообщение от сервиса")
    processing_time_seconds: Optional[float] = Field(None, description="Время обработки в секундах")


class SFoodRecognitionAdd(BaseModel):
    image_uuid: Optional[UUID] = Field(None, description="UUID изображения")
    comment: Optional[str] = Field(None, description="Комментарий")


class SFoodRecognitionUpdate(BaseModel):
    image_uuid: Optional[UUID] = Field(None, description="UUID изображения")
    comment: Optional[str] = Field(None, description="Комментарий")
    actual: Optional[bool] = Field(None, description="Актуальность записи")


class SFoodRecognitionListResponse(BaseModel):
    items: List[SFoodRecognition]
    pagination: Dict[str, Any]

