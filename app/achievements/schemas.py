from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID


class AchievementTypeBase(BaseModel):
    name: str = Field(..., description="Название типа достижения")
    description: str = Field(..., description="Описание типа достижения")
    category: str = Field(..., description="Категория достижения")
    subcategory: Optional[str] = Field(None, description="Подкатегория достижения")
    requirements: Optional[str] = Field(None, description="Требования для получения")
    icon: Optional[str] = Field(None, description="Иконка достижения")
    points: Optional[int] = Field(None, description="Количество очков за достижение")
    is_active: Optional[bool] = Field(True, description="Активно ли достижение")
    image_uuid: Optional[UUID] = Field(None, description="UUID изображения из таблицы files")


class AchievementTypeCreate(BaseModel):
    name: str = Field(..., description="Название типа достижения")
    description: str = Field(..., description="Описание типа достижения")
    category: str = Field(..., description="Категория достижения")
    subcategory: Optional[str] = Field(None, description="Подкатегория достижения")
    requirements: Optional[str] = Field(None, description="Требования для получения")
    icon: Optional[str] = Field(None, description="Иконка достижения")
    points: Optional[int] = Field(None, description="Количество очков за достижение")
    is_active: Optional[bool] = Field(True, description="Активно ли достижение")
    image_id: Optional[int] = Field(None, description="ID изображения из таблицы files (для создания)")


class AchievementTypeUpdate(AchievementTypeBase):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class AchievementTypeDisplay(AchievementTypeBase):
    uuid: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AchievementBase(BaseModel):
    achievement_type_id: int = Field(..., description="ID типа достижения")
    user_id: int = Field(..., description="ID пользователя")
    status: str = Field("active", description="Статус достижения")
    user_training_id: Optional[int] = Field(None, description="ID тренировки пользователя")
    user_program_id: Optional[int] = Field(None, description="ID программы пользователя")
    program_id: Optional[int] = Field(None, description="ID программы")


class AchievementCreate(AchievementBase):
    pass


class AchievementUpdate(BaseModel):
    status: Optional[str] = None
    user_training_id: Optional[int] = None
    user_program_id: Optional[int] = None
    program_id: Optional[int] = None


class AchievementDisplay(BaseModel):
    uuid: UUID
    achievement_type: AchievementTypeDisplay
    user_uuid: UUID
    status: str
    user_training_uuid: Optional[UUID] = None
    user_program_uuid: Optional[UUID] = None
    program_uuid: Optional[UUID] = None
    training_date: Optional[date]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    name: str

    class Config:
        from_attributes = True


class AchievementWithType(BaseModel):
    achievement_type: AchievementTypeDisplay
    created_at: datetime
    status: str
    training_date: Optional[date]
    completed_at: Optional[datetime]


class AchievementTypeWithStatus(BaseModel):
    """Тип достижения с информацией о статусе для пользователя"""
    uuid: UUID
    name: str
    description: str
    category: str
    subcategory: Optional[str]
    requirements: Optional[str]
    icon: Optional[str]
    points: Optional[int]
    is_active: Optional[bool]
    image_uuid: Optional[UUID] = None
    status: str = Field(description="Статус: 'earned' если достижение получено, 'not_earned' если не получено")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserAchievementsResponse(BaseModel):
    user_uuid: UUID
    achievements: List[AchievementWithType]
    total_count: int


class UserAchievementTypesResponse(BaseModel):
    """Ответ со всеми типами достижений и их статусом для пользователя"""
    achievement_types: List[AchievementTypeWithStatus]
    total_count: int


class AchievementCheckResponse(BaseModel):
    success: bool
    message: str
    achievement: Optional[AchievementDisplay] = None
    already_earned: bool = False
