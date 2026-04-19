# app/models/__init__.py — все модели для разрешения relationship() при запуске скриптов/миграций
from .database import Base
from .categories.models import Category
from .programs.models import Program
from .trainings.models import Training
from .exercise_groups.models import ExerciseGroup
from .exercises.models import Exercise
from .files.models import File
from .password_reset.models import PasswordResetCode
from .user_measurements.models import UserMeasurementType, UserMeasurement
from .promo_codes.models import PromoCode
from .subscriptions.models import Payment, SubscriptionPlan, Subscription
from .last_values.models import LastValue
from .achievements.models import AchievementType, Achievement
from .recipes.models import Recipe
from .user_favorite_recipes.models import UserFavoriteRecipe
from .user_favorite_exercises.models import UserFavoriteExercise
from .exercise_reference.models import ExerciseReference
from .email_verification.models import EmailVerification
from .user_program_plan.models import UserProgramPlan
from .exercise_builder_pool.models import ExerciseBuilderPool
from .exercise_builder_equipment.models import ExerciseBuilderEquipment
from .training_composition_rules.models import TrainingCompositionRule
from .user_exercise_stats.models import UserExerciseStats
from .anonymous_session.models import AnonymousSession
from .user_selected_trainings.models import UserSelectedTraining
from .users.models import User
from .user_program.models import UserProgram
from .user_exercises.models import UserExercise
from .user_training.models import UserTraining
from .food_recognition.models import FoodRecognition
from .meal_plans.models import MealPlan
from .calorie_calculator.models import CalorieCalculation
from .food_progress.models import DailyTarget, Meal

__all__ = [
    'Base',
    'Category',
    'Program',
    'Training',
    'ExerciseGroup',
    'Exercise',
    'File',
    'PasswordResetCode',
    'UserMeasurementType',
    'UserMeasurement',
    'PromoCode',
    'Payment',
    'SubscriptionPlan',
    'Subscription',
    'LastValue',
    'AchievementType',
    'Achievement',
    'Recipe',
    'UserFavoriteRecipe',
    'UserFavoriteExercise',
    'ExerciseReference',
    'EmailVerification',
    'UserProgramPlan',
    'ExerciseBuilderPool',
    'ExerciseBuilderEquipment',
    'TrainingCompositionRule',
    'UserExerciseStats',
    'AnonymousSession',
    'UserSelectedTraining',
    'User',
    'UserProgram',
    'UserExercise',
    'UserTraining',
    'FoodRecognition',
    'MealPlan',
    'CalorieCalculation',
    'DailyTarget',
    'Meal',
]