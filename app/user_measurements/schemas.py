from datetime import datetime, date
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


# Схемы для UserMeasurementType
class SUserMeasurementType(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    data_type: Literal["system", "custom"] = Field(..., description="Тип данных (system/custom)")
    user_uuid: Optional[UUID] = Field(None, description="UUID пользователя (null для системных)")
    caption: str = Field(..., description="Название типа измерения")
    actual: bool = Field(..., description="Актуальность записи")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")


class SUserMeasurementTypeAdd(BaseModel):
    data_type: Literal["system", "custom"] = Field(..., description="Тип данных (system/custom)")
    user_uuid: Optional[UUID] = Field(None, description="UUID пользователя (null для системных)")
    caption: str = Field(..., min_length=1, max_length=100, description="Название типа измерения")

    @field_validator("caption")
    @classmethod
    def validate_caption(cls, v):
        if not v or not v.strip():
            raise ValueError("Название типа измерения не может быть пустым")
        return v.strip()


class SUserMeasurementTypeUpdate(BaseModel):
    data_type: Optional[Literal["system", "custom"]] = Field(None, description="Тип данных (system/custom)")
    user_uuid: Optional[UUID] = Field(None, description="UUID пользователя (null для системных)")
    caption: Optional[str] = Field(None, min_length=1, max_length=100, description="Название типа измерения")

    @field_validator("caption")
    @classmethod
    def validate_caption(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("Название типа измерения не может быть пустым")
        return v.strip() if v else v


# Схемы для UserMeasurement
class SUserMeasurement(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    user_uuid: UUID = Field(..., description="UUID пользователя")
    measurement_type_uuid: UUID = Field(..., description="UUID типа измерения")
    measurement_date: date = Field(..., description="Дата замера")
    value: float = Field(..., description="Значение измерения")
    actual: bool = Field(..., description="Актуальность записи")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")


class SUserMeasurementAdd(BaseModel):
    user_uuid: UUID = Field(..., description="UUID пользователя")
    measurement_type_uuid: UUID = Field(..., description="UUID типа измерения")
    measurement_date: date = Field(..., description="Дата замера")
    value: float = Field(..., gt=0, description="Значение измерения (должно быть больше 0)")

    @field_validator("measurement_date")
    @classmethod
    def validate_measurement_date(cls, v):
        if v > date.today():
            raise ValueError("Дата замера не может быть в будущем")
        return v


class SUserMeasurementUpdate(BaseModel):
    measurement_type_uuid: Optional[UUID] = Field(None, description="UUID типа измерения")
    measurement_date: Optional[date] = Field(None, description="Дата замера")
    value: Optional[float] = Field(None, gt=0, description="Значение измерения (должно быть больше 0)")

    @field_validator("measurement_date")
    @classmethod
    def validate_measurement_date(cls, v):
        if v is not None and v > date.today():
            raise ValueError("Дата замера не может быть в будущем")
        return v


# Схемы для запросов с фильтрацией
class SUserMeasurementFilter(BaseModel):
    measurement_type_uuid: Optional[UUID] = Field(None, description="Фильтр по типу измерения")
    date_from: Optional[date] = Field(None, description="Дата начала периода")
    date_to: Optional[date] = Field(None, description="Дата окончания периода")
    page: int = Field(1, ge=1, description="Номер страницы")
    size: int = Field(10, ge=1, le=100, description="Размер страницы")

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_dates(cls, v):
        if v is not None and v > date.today():
            raise ValueError("Дата не может быть в будущем")
        return v

    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, v, info):
        if v is not None and "date_from" in info.data:
            date_from = info.data["date_from"]
            if date_from is not None and v < date_from:
                raise ValueError("Дата окончания не может быть раньше даты начала")
        return v


# Схемы для ответов с пагинацией
class SPaginationInfo(BaseModel):
    page: int = Field(..., description="Текущая страница")
    size: int = Field(..., description="Размер страницы")
    total_count: int = Field(..., description="Общее количество записей")
    total_pages: int = Field(..., description="Общее количество страниц")
    has_next: bool = Field(..., description="Есть ли следующая страница")
    has_prev: bool = Field(..., description="Есть ли предыдущая страница")


class SUserMeasurementListResponse(BaseModel):
    items: list[SUserMeasurement] = Field(..., description="Список измерений")
    pagination: SPaginationInfo = Field(..., description="Информация о пагинации")


class SUserMeasurementTypeListResponse(BaseModel):
    items: list[SUserMeasurementType] = Field(..., description="Список типов измерений")
    pagination: SPaginationInfo = Field(..., description="Информация о пагинации")


# Схемы для архивации/разархивации
class SArchiveRequest(BaseModel):
    uuid: UUID = Field(..., description="UUID записи для архивации/разархивации")


# Схемы для ответов
class SUserMeasurementTypeResponse(BaseModel):
    message: str = Field(..., description="Сообщение о результате операции")
    measurement_type: Optional[SUserMeasurementType] = Field(None, description="Данные типа измерения")


class SUserMeasurementResponse(BaseModel):
    message: str = Field(..., description="Сообщение о результате операции")
    measurement: Optional[SUserMeasurement] = Field(None, description="Данные измерения")
