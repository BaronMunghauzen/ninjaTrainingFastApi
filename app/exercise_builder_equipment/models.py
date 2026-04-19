from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field

if TYPE_CHECKING:
    from app.exercise_builder_pool.models import ExerciseBuilderPool


class ExerciseBuilderEquipment(Base):
    __tablename__ = "exercise_builder_equipment"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    actual: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    exercise_builder_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exercise_builder_pool.id"), nullable=True
    )
    equipment_code: Mapped[Optional[str]] = mapped_column(nullable=True)
    exercise_caption: Mapped[Optional[str]] = mapped_column(nullable=True)

    exercise_builder_pool: Mapped[Optional["ExerciseBuilderPool"]] = relationship(
        "ExerciseBuilderPool", back_populates="equipment"
    )

    @property
    def exercise_builder_pool_uuid(self) -> Optional[str]:
        return str(self.exercise_builder_pool.uuid) if self.exercise_builder_pool else None

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, equipment_code={self.equipment_code!r})"
