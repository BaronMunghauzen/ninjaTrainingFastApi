from fastapi import Query
from typing import Optional


class RBRecipe:
    def __init__(
        self,
        user_uuid: Optional[str] = Query(None, description="UUID пользователя (None для системных рецептов)"),
        category: Optional[str] = Query(None, description="Категория рецепта"),
        type: Optional[str] = Query(None, description="Тип рецепта"),
        name: Optional[str] = Query(None, description="Название рецепта"),
        actual: Optional[bool] = Query(None, description="Актуальность записи")
    ):
        self.user_uuid = user_uuid
        self.category = category
        self.type = type
        self.name = name
        self.actual = actual
    
    def to_dict(self) -> dict:
        data = {
            'user_uuid': self.user_uuid,
            'category': self.category,
            'type': self.type,
            'name': self.name,
            'actual': self.actual
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data

