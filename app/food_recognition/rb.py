from fastapi import Query
from datetime import date
from typing import Optional


class RBFoodRecognition:
    def __init__(
        self,
        user_uuid: Optional[str] = Query(None, description="UUID пользователя"),
        image_uuid: Optional[str] = Query(None, description="UUID изображения"),
        created_from: Optional[date] = Query(None, description="Дата создания (от)"),
        created_to: Optional[date] = Query(None, description="Дата создания (до)"),
        actual: Optional[bool] = Query(None, description="Актуальность записи"),
        name: Optional[str] = Query(None, description="Поиск по названию еды (вхождение без учета регистра)")
    ):
        self.user_uuid = user_uuid
        self.image_uuid = image_uuid
        self.created_from = created_from
        self.created_to = created_to
        self.actual = actual
        self.name = name
    
    def to_dict(self) -> dict:
        data = {
            'user_uuid': self.user_uuid,
            'image_uuid': self.image_uuid,
            'actual': self.actual
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data

