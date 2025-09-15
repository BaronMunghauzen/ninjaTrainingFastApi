from typing import Optional
from datetime import date


class RBUserMeasurementType:
    def __init__(
        self,
        measurement_type_uuid: str | None = None,
        data_type: str | None = None,
        user_id: int | None = None,
        caption: str | None = None,
        actual: bool | None = None
    ):
        self.uuid = measurement_type_uuid
        self.data_type = data_type
        self.user_id = user_id
        self.caption = caption
        self.actual = actual

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'data_type': self.data_type,
            'user_id': self.user_id,
            'caption': self.caption,
            'actual': self.actual
        }
        # Создаем копию словаря, чтобы избежать изменения словаря во время итерации
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data


class RBUserMeasurement:
    def __init__(
        self,
        measurement_uuid: str | None = None,
        user_id: int | None = None,
        measurement_type_id: int | None = None,
        measurement_date: date | None = None,
        value: float | None = None,
        actual: bool | None = None
    ):
        self.uuid = measurement_uuid
        self.user_id = user_id
        self.measurement_type_id = measurement_type_id
        self.measurement_date = measurement_date
        self.value = value
        self.actual = actual

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'user_id': self.user_id,
            'measurement_type_id': self.measurement_type_id,
            'measurement_date': self.measurement_date,
            'value': self.value,
            'actual': self.actual
        }
        # Создаем копию словаря, чтобы избежать изменения словаря во время итерации
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data
