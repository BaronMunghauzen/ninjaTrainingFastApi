from typing import Optional
from sqlalchemy import Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field

class ExerciseReference(Base):
    __tablename__ = 'exercise_reference'

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    exercise_type: Mapped[Optional[str]] = mapped_column(nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    caption: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    muscle_group: Mapped[str]
    image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)

    image: Mapped[Optional["File"]] = relationship("File")
    user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, caption={self.caption!r})"

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "exercise_type": self.exercise_type,
            "user_uuid": str(self.user.uuid) if self.user else None,
            "caption": self.caption,
            "description": self.description,
            "muscle_group": self.muscle_group,
            "image_uuid": str(self.image.uuid) if self.image else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 