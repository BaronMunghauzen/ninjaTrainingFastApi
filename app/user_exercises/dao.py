from app.dao.base import BaseDAO
from app.user_exercises.models import UserExercise
from app.programs.dao import ProgramDAO
from app.trainings.dao import TrainingDAO
from app.users.dao import UsersDAO
from app.exercises.dao import ExerciseDAO


class UserExerciseDAO(BaseDAO):
    model = UserExercise
    uuid_fk_map = {
        'program_id': (ProgramDAO, 'program_uuid'),
        'training_id': (TrainingDAO, 'training_uuid'),
        'user_id': (UsersDAO, 'user_uuid'),
        'exercise_id': (ExerciseDAO, 'exercise_uuid')
    }
