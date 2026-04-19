from app.dao.base import BaseDAO
from app.exercise_builder_pool.models import ExerciseBuilderPool
from app.exercise_reference.dao import ExerciseReferenceDAO


class ExerciseBuilderPoolDAO(BaseDAO):
    model = ExerciseBuilderPool
    uuid_fk_map = {
        "exercise_id": (ExerciseReferenceDAO, "exercise_reference_uuid"),
    }
