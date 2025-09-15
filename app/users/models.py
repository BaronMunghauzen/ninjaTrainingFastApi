from typing import Optional, List, TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import ForeignKey, Text, text, Integer, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, str_null_true, str_null_true, uuid_field
from enum import Enum

if TYPE_CHECKING:
    from app.programs.models import Program
    from app.exercises.models import Exercise
    from app.trainings.models import Training
    from app.user_program.models import UserProgram
    from app.user_training.models import UserTraining
    from app.user_exercises.models import UserExercise
    from app.files.models import File
    from app.achievements.models import Achievement
    from app.password_reset.models import PasswordResetCode
    from app.user_measurements.models import UserMeasurementType, UserMeasurement


class GenderEnum(str, Enum):
    male = "male"
    female = "female"


class SubscriptionStatusEnum(str, Enum):
    pending = "pending"
    active = "active"
    expired = "expired"


class ThemeEnum(str, Enum):
    light = "light"
    dark = "dark"


class User(Base):
    __tablename__ = "user"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    phone_number: Mapped[str_uniq] = mapped_column(nullable=True)
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str_uniq]
    password: Mapped[str]
    login: Mapped[str_uniq]
    middle_name: Mapped[str | None] = mapped_column(nullable=True)
    gender: Mapped[GenderEnum] = mapped_column(SQLAlchemyEnum(GenderEnum), nullable=True)
    description: Mapped[str | None] = mapped_column(nullable=True)
    subscription_status: Mapped[SubscriptionStatusEnum] = mapped_column(SQLAlchemyEnum(SubscriptionStatusEnum), nullable=False, server_default=text("'pending'"))
    subscription_until: Mapped[date | None] = mapped_column(nullable=True)
    theme: Mapped[ThemeEnum] = mapped_column(SQLAlchemyEnum(ThemeEnum), nullable=False, server_default=text("'dark'"))

    is_user: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)

    avatar_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("files.id"), nullable=True)

    # Новые поля для подтверждения email (добавляем только их)
    email_verified: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)
    email_verification_sent_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Определяем отношения с упражнениями
    exercises: Mapped[list["Exercise"]] = relationship("Exercise", back_populates="user")

    # Определяем отношения: один пользователь может иметь несколько программ
    programs: Mapped[list["Program"]] = relationship("Program", back_populates="user")

    # Определяем отношения с тренировками
    trainings: Mapped[list["Training"]] = relationship("Training", back_populates="user")

    # Определяем отношения с пользовательскими программами
    user_programs: Mapped[list["UserProgram"]] = relationship("UserProgram", back_populates="user")

    # Определяем отношения с пользовательскими тренировками
    user_trainings: Mapped[list["UserTraining"]] = relationship("UserTraining", back_populates="user")

    # Определяем отношения с пользовательскими упражнениями
    user_exercises: Mapped[list["UserExercise"]] = relationship("UserExercise", back_populates="user")

    # Определяем отношения с достижениями
    achievements: Mapped[list["Achievement"]] = relationship("Achievement", back_populates="user")

    # Определяем отношения с файлами (аватар) - исправляем конфликт
    avatar: Mapped[Optional["File"]] = relationship("File")
    
    # Определяем отношения с кодами сброса пароля
    password_reset_codes: Mapped[list["PasswordResetCode"]] = relationship("PasswordResetCode", back_populates="user")
    
    # Определяем отношения с типами измерений
    measurement_types: Mapped[list["UserMeasurementType"]] = relationship("UserMeasurementType", back_populates="user")
    
    # Определяем отношения с измерениями
    measurements: Mapped[list["UserMeasurement"]] = relationship("UserMeasurement", back_populates="user")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"

    async def to_dict(self):
        # Получаем UUID аватара если есть avatar_id
        avatar_uuid = None
        if self.avatar_id:
            from app.files.dao import FilesDAO
            avatar_file = await FilesDAO.find_one_or_none_by_id(self.avatar_id)
            if avatar_file:
                avatar_uuid = avatar_file.uuid
        
        return {
            "uuid": str(self.uuid),
            "login": self.login,
            "phone_number": self.phone_number,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "gender": self.gender.value if self.gender else None,
            "description": self.description,
            "email": self.email,
            "password": self.password,
            "is_user": self.is_user,
            "is_admin": self.is_admin,
            "subscription_status": self.subscription_status.value,
            "subscription_until": str(self.subscription_until) if self.subscription_until else None,
            "theme": self.theme.value,
            "avatar_uuid": avatar_uuid,
            # Добавляем новые поля для email verification
            "email_verified": self.email_verified,
            "email_verification_sent_at": self.email_verification_sent_at.isoformat() if self.email_verification_sent_at else None,
        }
