from fastapi import Query

class RBTraining:
    def __init__(self,
                 training_uuid: str | None = Query(None, description="UUID тренировки"),
                 program_uuid: str | None = Query(None, description="UUID программы"),
                 training_type: str | None = Query(None, description="Тип тренировки"),
                 user_uuid: str | None = Query(None, description="UUID пользователя"),
                 caption: str | None = Query(None, description="Название тренировки"),
                 description: str | None = Query(None, description="Описание тренировки"),
                 difficulty_level: int | None = Query(None, description="Уровень сложности"),
                 order: int | None = Query(None, description="Порядок для сортировки"),
                 muscle_group: str | None = Query(None, description="Группа мышц"),
                 stage: int | None = Query(None, description="Этап тренировки"),
                 actual: bool | None = Query(None, description="Актуальная тренировка")):
        self.uuid = training_uuid
        self.program_uuid = program_uuid
        self.training_type = training_type
        self.user_uuid = user_uuid
        self.caption = caption
        self.description = description
        self.difficulty_level = difficulty_level
        self.order = order
        self.muscle_group = muscle_group
        self.stage = stage
        self.actual = actual

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'program_uuid': self.program_uuid,
            'training_type': self.training_type,
            'user_uuid': self.user_uuid,
            'caption': self.caption,
            'description': self.description,
            'difficulty_level': self.difficulty_level,
            'order': self.order,
            'muscle_group': self.muscle_group,
            'stage': self.stage,
            'actual': self.actual
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data
