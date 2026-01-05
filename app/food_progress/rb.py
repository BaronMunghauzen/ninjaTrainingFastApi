from fastapi import Query
from typing import Optional
from datetime import date
from uuid import UUID


class RBDailyTarget:
    def __init__(
        self,
        user_uuid: Optional[str] = Query(None, description="UUID пользователя"),
        actual: Optional[bool] = Query(None, description="Актуальность записи")
    ):
        self.user_uuid = user_uuid
        self.actual = actual
    
    def to_dict(self) -> dict:
        data = {
            'user_uuid': self.user_uuid,
            'actual': self.actual
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data


class RBMeal:
    def __init__(
        self,
        user_uuid: Optional[str] = Query(None, description="UUID пользователя"),
        actual: Optional[bool] = Query(None, description="Актуальность записи"),
        date_from: Optional[date] = Query(None, description="Дата приема пищи (от)"),
        date_to: Optional[date] = Query(None, description="Дата приема пищи (до)")
    ):
        self.user_uuid = user_uuid
        self.actual = actual
        self.date_from = date_from
        self.date_to = date_to
    
    def to_dict(self) -> dict:
        data = {
            'user_uuid': self.user_uuid,
            'actual': self.actual
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data

