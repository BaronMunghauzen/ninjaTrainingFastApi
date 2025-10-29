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
    original_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    technique_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    muscle_group: Mapped[str]
    equipment_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    auxiliary_muscle_groups: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)
    gif_id: Mapped[Optional[int]] = mapped_column(ForeignKey("files.id"), nullable=True)

    image: Mapped[Optional["File"]] = relationship("File", foreign_keys=[image_id])
    video: Mapped[Optional["File"]] = relationship("File", foreign_keys=[video_id])
    gif: Mapped[Optional["File"]] = relationship("File", foreign_keys=[gif_id])
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
            "technique_description": self.technique_description,
            "muscle_group": self.muscle_group,
            "equipment_name": self.equipment_name,
            "auxiliary_muscle_groups": self.auxiliary_muscle_groups,
            "image_uuid": str(self.image.uuid) if self.image else None,
            "video_uuid": str(self.video.uuid) if self.video else None,
            "gif_uuid": str(self.gif.uuid) if self.gif else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 