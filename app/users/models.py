from sqlalchemy import text, Enum, Date, ForeignKey, Integer
from enum import Enum as PyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, uuid_field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.files.models import File


class GenderEnum(PyEnum):
    male = "male"
    female = "female"

class SubscriptionStatusEnum(PyEnum):
    pending = "pending"
    active = "active"
    expired = "expired"

class ThemeEnum(PyEnum):
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
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum), nullable=True)
    description: Mapped[str | None] = mapped_column(nullable=True)
    subscription_status: Mapped[SubscriptionStatusEnum] = mapped_column(Enum(SubscriptionStatusEnum), nullable=False, server_default=text("'pending'"))
    subscription_until: Mapped[Date | None] = mapped_column(Date, nullable=True)
    theme: Mapped[ThemeEnum] = mapped_column(Enum(ThemeEnum), nullable=False, server_default=text("'dark'"))

    is_user: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)

    avatar_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("files.id"), nullable=True)

    # Определяем отношения с упражнениями
    exercises: Mapped[list["Exercise"]] = relationship("Exercise", back_populates="user")

    # Определяем отношения: один пользователь может иметь несколько программ
    programs: Mapped[list["Program"]] = relationship("Program", back_populates="user")

    # Определяем отношения с тренировками
    trainings: Mapped[list["Training"]] = relationship("Training", back_populates="user")



    # Еще связь
    user_programs: Mapped[list["UserProgram"]] = relationship("UserProgram", back_populates="user")
    user_trainings: Mapped[list["UserTraining"]] = relationship("UserTraining", back_populates="user")
    user_exercises: Mapped[list["UserExercise"]] = relationship("UserExercise", back_populates="user")
    
    # Связь с аватаром (убираем для избежания конфликтов)
    # avatar: Mapped["File"] = relationship("File", back_populates="user", uselist=False, foreign_keys="User.avatar_id")

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
            "avatar_uuid": avatar_uuid
        }
