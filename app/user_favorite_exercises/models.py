from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field

if TYPE_CHECKING:
    from app.users.models import User
    from app.exercise_reference.models import ExerciseReference


class UserFavoriteExercise(Base):
    __tablename__ = "user_favorite_exercises"
    __table_args__ = (
        UniqueConstraint('user_id', 'exercise_reference_id', name='uq_user_favorite_exercise'),
    )

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    exercise_reference_id: Mapped[int] = mapped_column(ForeignKey("exercise_reference.id"), nullable=False)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="favorite_exercises")
    exercise_reference: Mapped["ExerciseReference"] = relationship("ExerciseReference", back_populates="favorited_by_users")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, user_id={self.user_id}, exercise_reference_id={self.exercise_reference_id})"

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "user_uuid": str(self.user.uuid) if self.user else None,
            "exercise_reference_uuid": str(self.exercise_reference.uuid) if self.exercise_reference else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


