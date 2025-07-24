class RBProgram:
    def __init__(self, program_uuid: str | None = None,
                 actual: bool | None = None,
                 category_uuid: str | None = None,
                 program_type: str | None = None,
                 user_uuid: str | None = None,
                 caption: str | None = None,
                 description: str | None = None,
                 difficulty_level: int | None = None,
                 order: int | None = None):
        self.uuid = program_uuid
        self.actual = actual
        self.category_uuid = category_uuid
        self.program_type = program_type
        self.user_uuid = user_uuid
        self.caption = caption
        self.description = description
        self.difficulty_level = difficulty_level
        self.order = order

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'actual': self.actual,
            'category_uuid': self.category_uuid,
            'program_type': self.program_type,
            'user_uuid': self.user_uuid,
            'caption': self.caption,
            'description': self.description,
            'difficulty_level': self.difficulty_level,
            'order': self.order
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data
