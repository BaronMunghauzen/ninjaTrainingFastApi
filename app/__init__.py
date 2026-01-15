# app/models/__init__.py
from .database import Base
from .categories.models import Category
from .programs.models import Program
from .trainings.models import Training
from .exercise_groups.models import ExerciseGroup
from .exercises.models import Exercise
from .users.models import User
from .user_program.models import UserProgram
from .user_exercises.models import UserExercise
from .user_training.models import UserTraining
from .files.models import File
# Import UserFavoriteExercise BEFORE ExerciseReference to ensure it's registered with SQLAlchemy first
from .user_favorite_exercises.models import UserFavoriteExercise
from .exercise_reference.models import ExerciseReference
from .email_verification.models import EmailVerification

__all__ = [
    'Base',
    'Category',
    'User',
    'Program',
    'Training',
    'ExerciseGroup',
    'Exercises',
    'UserProgram',
    'UserTraining',
    'UserExercise',
    'File',
    'UserFavoriteExercise',
    'ExerciseReference',
    'EmailVerification'
]