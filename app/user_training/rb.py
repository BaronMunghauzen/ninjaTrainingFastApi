from app.user_training.models import TrainingStatus
from typing import Literal, Union

# Определяем Literal тип для правильного отображения в Swagger
TrainingStatusLiteral = Literal["PASSED", "SKIPPED", "ACTIVE", "BLOCKED_YET"]
# Поддерживаем также нижний регистр для совместимости с клиентом
TrainingStatusLiteralLower = Literal["passed", "skipped", "active", "blocked_yet"]
TrainingStatusAny = Union[TrainingStatusLiteral, TrainingStatusLiteralLower]

class RBUserTraining:
    def __init__(self, user_training_uuid: str | None = None,
                 user_program_uuid: str | None = None,
                 program_uuid: str | None = None,
                 training_uuid: str | None = None,
                 user_uuid: str | None = None,
                 training_date: str | None = None,
                 status: TrainingStatusAny | None = None,
                 is_rest_day: bool | None = None):
        self.uuid = user_training_uuid
        self.user_program_uuid = user_program_uuid
        self.program_uuid = program_uuid
        self.training_uuid = training_uuid
        self.user_uuid = user_uuid
        self.training_date = training_date
        # Нормализуем статус к верхнему регистру
        self.status = self._normalize_status(status)
        self.is_rest_day = is_rest_day
    
    def _normalize_status(self, status: TrainingStatusAny | None) -> str | None:
        """Нормализует статус к верхнему регистру"""
        if status is None:
            return None
        
        status_mapping = {
            "passed": "PASSED",
            "skipped": "SKIPPED", 
            "active": "ACTIVE",
            "blocked_yet": "BLOCKED_YET"
        }
        
        # Если уже в верхнем регистре, возвращаем как есть
        if status in ["PASSED", "SKIPPED", "ACTIVE", "BLOCKED_YET"]:
            return status
        
        # Если в нижнем регистре, преобразуем
        return status_mapping.get(status.lower(), status)

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'user_program_uuid': self.user_program_uuid,
            'program_uuid': self.program_uuid,
            'training_uuid': self.training_uuid,
            'user_uuid': self.user_uuid,
            'training_date': self.training_date,
            'status': self.status,
            'is_rest_day': self.is_rest_day
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data
