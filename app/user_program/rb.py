class RBUserProgram:
    def __init__(self, user_program_uuid: str | None = None,
                 program_uuid: str | None = None,
                 user_uuid: str | None = None,
                 caption: str | None = None,
                 status: str | None = None,
                 stopped_at: str | None = None,
                 stage: int | None = None):
        self.uuid = user_program_uuid
        self.program_uuid = program_uuid
        self.user_uuid = user_uuid
        self.caption = caption
        self.status = status
        self.stopped_at = stopped_at
        self.stage = stage

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'program_uuid': self.program_uuid,
            'user_uuid': self.user_uuid,
            'caption': self.caption,
            'status': self.status,
            'stopped_at': self.stopped_at,
            'stage': self.stage
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data
