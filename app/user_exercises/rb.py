from app.user_exercises.models import ExerciseStatus
from datetime import date

class RBUserExercise:
    def __init__(self, user_exercise_uuid: str | None = None,
                 program_uuid: str | None = None,
                 training_uuid: str | None = None,
                 user_uuid: str | None = None,
                 exercise_uuid: str | None = None,
                 training_date: str | None = None,
                 status: ExerciseStatus | None = None,
                 set_number: int | None = None,
                 weight: float | None = None,
                 reps: int | None = None):
        self.uuid = user_exercise_uuid
        self.program_uuid = program_uuid
        self.training_uuid = training_uuid
        self.user_uuid = user_uuid
        self.exercise_uuid = exercise_uuid
        if training_date is not None:
            try:
                self.training_date = date.fromisoformat(training_date)
            except ValueError:
                self.training_date = training_date  # Оставляем как есть, если формат неверный
        else:
            self.training_date = None
        self.status = status
        self.set_number = set_number
        self.weight = weight
        self.reps = reps

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'program_uuid': self.program_uuid,
            'training_uuid': self.training_uuid,
            'user_uuid': self.user_uuid,
            'exercise_uuid': self.exercise_uuid,
            'training_date': self.training_date,
            'status': self.status,
            'set_number': self.set_number,
            'weight': self.weight,
            'reps': self.reps
        }
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data
