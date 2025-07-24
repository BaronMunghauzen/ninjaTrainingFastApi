from fastapi import Query


class RBExercise:
    def __init__(self, 
                 exercise_uuid: str | None = Query(None, description="UUID упражнения"),
                 user_uuid: str | None = Query(None, description="UUID пользователя"),
                 exercise_type: str | None = Query(None, description="Тип упражнения"),
                 caption: str | None = Query(None, description="Название упражнения"),
                 description: str | None = Query(None, description="Описание упражнения"),
                 difficulty_level: int | None = Query(None, description="Уровень сложности"),
                 order: int | None = Query(None, description="Порядок для сортировки"),
                 muscle_group: str | None = Query(None, description="Группа мышц"),
                 sets_count: int | None = Query(None, description="Количество подходов"),
                 reps_count: int | None = Query(None, description="Количество повторений"),
                 rest_time: int | None = Query(None, description="Время отдыха (сек)"),
                 with_weight: bool | None = Query(None, description="С весом или без")):
        self.uuid = exercise_uuid
        self.user_uuid = user_uuid
        self.exercise_type = exercise_type
        self.caption = caption
        self.description = description
        self.difficulty_level = difficulty_level
        self.order = order
        self.muscle_group = muscle_group
        self.sets_count = sets_count
        self.reps_count = reps_count
        self.rest_time = rest_time
        self.with_weight = with_weight

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'user_uuid': self.user_uuid,
            'exercise_type': self.exercise_type,
            'caption': self.caption,
            'description': self.description,
            'difficulty_level': self.difficulty_level,
            'order': self.order,
            'muscle_group': self.muscle_group,
            'sets_count': self.sets_count,
            'reps_count': self.reps_count,
            'rest_time': self.rest_time,
            'with_weight': self.with_weight
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data
