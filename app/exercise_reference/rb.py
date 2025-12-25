from fastapi import Query

class RBExerciseReference:
    def __init__(self,
                 exercise_reference_uuid: str | None = Query(None, description="UUID справочника упражнения"),
                 exercise_type: str | None = Query(None, description="Тип упражнения"),
                 user_uuid: str | None = Query(None, description="UUID пользователя"),
                 description: str | None = Query(None, description="Описание упражнения"),
                 muscle_group: str | None = Query(None, description="Группа мышц"),
                 equipment_name: str | None = Query(None, description="Название необходимого оборудования"),
                 auxiliary_muscle_groups: str | None = Query(None, description="Вспомогательные группы мышц"),
                 is_favorite: bool | None = Query(None, description="Фильтр по избранным упражнениям (true - только избранные, false - только не избранные)")):
        self.uuid = exercise_reference_uuid
        self.exercise_type = exercise_type
        self.user_uuid = user_uuid
        self.description = description
        self.muscle_group = muscle_group
        self.equipment_name = equipment_name
        self.auxiliary_muscle_groups = auxiliary_muscle_groups
        self.is_favorite = is_favorite

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'exercise_type': self.exercise_type,
            'user_uuid': self.user_uuid,
            'description': self.description,
            'muscle_group': self.muscle_group,
            'equipment_name': self.equipment_name,
            'auxiliary_muscle_groups': self.auxiliary_muscle_groups,
            'is_favorite': self.is_favorite
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data 