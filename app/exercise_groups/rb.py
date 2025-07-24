class RBExerciseGroup:
    def __init__(self, exercise_group_uuid: str | None = None,
                 training_uuid: str | None = None,
                 caption: str | None = None,
                 description: str | None = None,
                 difficulty_level: int | None = None,
                 order: int | None = None,
                 muscle_group: str | None = None,
                 stage: int | None = None):
        self.uuid = exercise_group_uuid
        self.training_uuid = training_uuid
        self.caption = caption
        self.description = description
        self.difficulty_level = difficulty_level
        self.order = order
        self.muscle_group = muscle_group
        self.stage = stage

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'training_uuid': self.training_uuid,
            'caption': self.caption,
            'description': self.description,
            'difficulty_level': self.difficulty_level,
            'order': self.order,
            'muscle_group': self.muscle_group,
            'stage': self.stage
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data 