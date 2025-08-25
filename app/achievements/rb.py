from datetime import date, datetime
from typing import Optional


class RBAchievement:
    def __init__(self, achievement_uuid: str | None = None,
                 user_program_uuid: str | None = None,
                 program_uuid: str | None = None,
                 training_date: str | None = None,
                 completed_at: str | None = None):
        self.uuid = achievement_uuid
        self.user_program_uuid = user_program_uuid
        self.program_uuid = program_uuid
        self.training_date = training_date
        self.completed_at = completed_at

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'user_program_uuid': self.user_program_uuid,
            'program_uuid': self.program_uuid,
            'training_date': self.training_date,
            'completed_at': self.completed_at
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data
