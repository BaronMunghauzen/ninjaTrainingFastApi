from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime


class SRecipe(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID = Field(..., description="Уникальный идентификатор")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    actual: bool = Field(..., description="Актуальность записи")
    user_uuid: Optional[UUID] = Field(None, description="UUID пользователя")
    category: Optional[str] = Field(None, description="Категория рецепта")
    type: Optional[str] = Field(None, description="Тип рецепта")
    name: Optional[str] = Field(None, description="Название рецепта")
    ingredients: Optional[Dict[str, str]] = Field(None, description="Ингредиенты (словарь ключ-значение)")
    recipe: Optional[str] = Field(None, description="Текст рецепта (до 2000 символов)")
    calories_per_100g: Optional[float] = Field(None, description="Калории на 100г")
    proteins_per_100g: Optional[float] = Field(None, description="Белки на 100г")
    fats_per_100g: Optional[float] = Field(None, description="Жиры на 100г")
    carbs_per_100g: Optional[float] = Field(None, description="Углеводы на 100г")
    calories_per_portion: Optional[float] = Field(None, description="Калории на порцию")
    proteins_per_portion: Optional[float] = Field(None, description="Белки на порцию")
    fats_per_portion: Optional[float] = Field(None, description="Жиры на порцию")
    carbs_per_portion: Optional[float] = Field(None, description="Углеводы на порцию")
    portions_count: Optional[int] = Field(None, description="Количество порций по умолчанию")
    image_uuid: Optional[UUID] = Field(None, description="UUID изображения")
    cooking_time: Optional[int] = Field(None, description="Время приготовления в минутах")


class SRecipeAdd(BaseModel):
    user_uuid: Optional[UUID] = Field(None, description="UUID пользователя (None для системных рецептов)")
    category: Optional[str] = Field(None, description="Категория рецепта")
    type: Optional[str] = Field(None, description="Тип рецепта")
    name: Optional[str] = Field(None, description="Название рецепта")
    ingredients: Optional[Dict[str, str]] = Field(None, description="Ингредиенты (словарь ключ-значение)")
    recipe: Optional[str] = Field(None, max_length=2000, description="Текст рецепта (до 2000 символов)")
    calories_per_100g: Optional[float] = Field(None, description="Калории на 100г")
    proteins_per_100g: Optional[float] = Field(None, description="Белки на 100г")
    fats_per_100g: Optional[float] = Field(None, description="Жиры на 100г")
    carbs_per_100g: Optional[float] = Field(None, description="Углеводы на 100г")
    calories_per_portion: Optional[float] = Field(None, description="Калории на порцию")
    proteins_per_portion: Optional[float] = Field(None, description="Белки на порцию")
    fats_per_portion: Optional[float] = Field(None, description="Жиры на порцию")
    carbs_per_portion: Optional[float] = Field(None, description="Углеводы на порцию")
    portions_count: Optional[int] = Field(None, description="Количество порций по умолчанию")
    image_uuid: Optional[UUID] = Field(None, description="UUID изображения")
    cooking_time: Optional[int] = Field(None, description="Время приготовления в минутах")
    
    @field_validator('recipe')
    @classmethod
    def validate_recipe_length(cls, v):
        if v and len(v) > 2000:
            raise ValueError('Рецепт не может содержать более 2000 символов')
        return v


class SRecipeUpdate(BaseModel):
    category: Optional[str] = Field(None, description="Категория рецепта")
    type: Optional[str] = Field(None, description="Тип рецепта")
    name: Optional[str] = Field(None, description="Название рецепта")
    ingredients: Optional[Dict[str, str]] = Field(None, description="Ингредиенты (словарь ключ-значение)")
    recipe: Optional[str] = Field(None, max_length=2000, description="Текст рецепта (до 2000 символов)")
    calories_per_100g: Optional[float] = Field(None, description="Калории на 100г")
    proteins_per_100g: Optional[float] = Field(None, description="Белки на 100г")
    fats_per_100g: Optional[float] = Field(None, description="Жиры на 100г")
    carbs_per_100g: Optional[float] = Field(None, description="Углеводы на 100г")
    calories_per_portion: Optional[float] = Field(None, description="Калории на порцию")
    proteins_per_portion: Optional[float] = Field(None, description="Белки на порцию")
    fats_per_portion: Optional[float] = Field(None, description="Жиры на порцию")
    carbs_per_portion: Optional[float] = Field(None, description="Углеводы на порцию")
    portions_count: Optional[int] = Field(None, description="Количество порций по умолчанию")
    image_uuid: Optional[UUID] = Field(None, description="UUID изображения")
    cooking_time: Optional[int] = Field(None, description="Время приготовления в минутах")
    actual: Optional[bool] = Field(None, description="Актуальность записи")
    
    @field_validator('recipe')
    @classmethod
    def validate_recipe_length(cls, v):
        if v and len(v) > 2000:
            raise ValueError('Рецепт не может содержать более 2000 символов')
        return v

