from app.dao.base import BaseDAO
from app.training_composition_rules.models import TrainingCompositionRule


class TrainingCompositionRuleDAO(BaseDAO):
    model = TrainingCompositionRule
    uuid_fk_map = {}
