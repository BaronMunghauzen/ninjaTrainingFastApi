from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, int_pk, uuid_field

if TYPE_CHECKING:
    from app.users.models import User
    from app.trainings.models import Training


class UserSelectedTraining(Base):
    __tablename__ = "user_selected_trainings"
    __table_args__ = (
        UniqueConstraint("user_id", "training_id", name="uq_user_selected_training"),
    )

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    actual: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="selected_trainings")
    training: Mapped["Training"] = relationship("Training", back_populates="selected_by_users")

    @property
    def user_uuid(self) -> Optional[UUID]:
        return self.user.uuid if self.user is not None else None

    @property
    def training_uuid(self) -> Optional[UUID]:
        return self.training.uuid if self.training is not None else None

    @property
    def caption(self) -> Optional[str]:
        return self.training.caption if self.training is not None else None

    @property
    def image_uuid(self) -> Optional[UUID]:
        img = self.training.image if self.training is not None else None
        return img.uuid if img is not None else None

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, user_id={self.user_id}, training_id={self.training_id})"
