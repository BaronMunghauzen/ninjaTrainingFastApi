from app.dao.base import BaseDAO
from app.exercise_builder_equipment.models import ExerciseBuilderEquipment
from app.exercise_builder_pool.dao import ExerciseBuilderPoolDAO


class ExerciseBuilderEquipmentDAO(BaseDAO):
    model = ExerciseBuilderEquipment
    uuid_fk_map = {
        "exercise_builder_id": (ExerciseBuilderPoolDAO, "exercise_builder_pool_uuid"),
    }
