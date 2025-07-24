from fastapi import Query

class RBExerciseReference:
    def __init__(self,
                 exercise_reference_uuid: str | None = Query(None, description="UUID справочника упражнения"),
                 exercise_type: str | None = Query(None, description="Тип упражнения"),
                 user_uuid: str | None = Query(None, description="UUID пользователя"),
                 description: str | None = Query(None, description="Описание упражнения"),
                 muscle_group: str | None = Query(None, description="Группа мышц")):
        self.uuid = exercise_reference_uuid
        self.exercise_type = exercise_type
        self.user_uuid = user_uuid
        self.description = description
        self.muscle_group = muscle_group

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'exercise_type': self.exercise_type,
            'user_uuid': self.user_uuid,
            'description': self.description,
            'muscle_group': self.muscle_group
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data 