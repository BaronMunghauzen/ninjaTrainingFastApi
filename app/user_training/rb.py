from app.user_training.models import TrainingStatus

class RBUserTraining:
    def __init__(self, user_training_uuid: str | None = None,
                 user_program_uuid: str | None = None,
                 program_uuid: str | None = None,
                 training_uuid: str | None = None,
                 user_uuid: str | None = None,
                 training_date: str | None = None,
                 status: TrainingStatus | None = None):
        self.uuid = user_training_uuid
        self.user_program_uuid = user_program_uuid
        self.program_uuid = program_uuid
        self.training_uuid = training_uuid
        self.user_uuid = user_uuid
        self.training_date = training_date
        self.status = status

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'user_program_uuid': self.user_program_uuid,
            'program_uuid': self.program_uuid,
            'training_uuid': self.training_uuid,
            'user_uuid': self.user_uuid,
            'training_date': self.training_date,
            'status': self.status
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data
