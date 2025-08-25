from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, str_null_true, uuid_field
from datetime import date, datetime

if TYPE_CHECKING:
    from app.user_program.models import UserProgram
    from app.programs.models import Program
    from app.users.models import User
    from app.user_training.models import UserTraining


class AchievementType(Base):
    __tablename__ = 'achievement_types'

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    name: Mapped[str]
    description: Mapped[str]
    category: Mapped[str]
    subcategory: Mapped[Optional[str]] = mapped_column(nullable=True)
    requirements: Mapped[Optional[str]] = mapped_column(nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(nullable=True)
    points: Mapped[Optional[int]] = mapped_column(nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(nullable=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    achievements: Mapped[list["Achievement"]] = relationship("Achievement", back_populates="achievement_type")

    def __repr__(self):
        return f"<AchievementType {self.id} (name={self.name}, category={self.category})>"

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "requirements": self.requirements,
            "icon": self.icon,
            "points": self.points,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Achievement(Base):
    __tablename__ = 'achievements'

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    name: Mapped[str]  # Оставляем для обратной совместимости
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    status: Mapped[str]
    user_training_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user_training.id'), nullable=True)
    user_program_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user_program.id'), nullable=True)
    program_id: Mapped[Optional[int]] = mapped_column(ForeignKey('program.id'), nullable=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    
    # Новое поле для связи с типом достижения
    achievement_type_id: Mapped[Optional[int]] = mapped_column(ForeignKey('achievement_types.id'), nullable=True)

    # Отношения
    achievement_type: Mapped[Optional["AchievementType"]] = relationship("AchievementType", back_populates="achievements")
    user: Mapped["User"] = relationship("User", back_populates="achievements")
    user_training: Mapped[Optional["UserTraining"]] = relationship("UserTraining", back_populates="achievements")
    user_program: Mapped[Optional["UserProgram"]] = relationship("UserProgram", back_populates="achievements")
    program: Mapped[Optional["Program"]] = relationship("Program", back_populates="achievements")

    @property
    def training_date(self) -> Optional[date]:
        if self.user_training:
            return self.user_training.training_date
        return None

    @property
    def completed_at(self) -> Optional[datetime]:
        if self.user_training:
            return self.user_training.completed_at
        return None

    @property
    def display_name(self) -> str:
        """Возвращает название из типа достижения, если есть, иначе из поля name"""
        return self.achievement_type.name if self.achievement_type else self.name

    def __repr__(self):
        return f"<Achievement {self.id} (name={self.display_name}, user_id={self.user_id}, status={self.status})>"

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "name": self.display_name,
            "achievement_type_uuid": str(self.achievement_type.uuid) if self.achievement_type else None,
            "user_id": self.user_id,
            "status": self.status,
            "training_date": self.training_date.isoformat() if self.training_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "user_training_id": self.user_training_id,
            "user_program_id": self.user_program_id,
            "program_id": self.program_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }