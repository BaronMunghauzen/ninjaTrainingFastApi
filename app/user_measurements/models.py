from typing import Optional, TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import ForeignKey, Text, Integer, Enum as SQLAlchemyEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, str_null_true, uuid_field
from enum import Enum

if TYPE_CHECKING:
    from app.users.models import User


class MeasurementTypeEnum(str, Enum):
    system = "system"
    custom = "custom"


class UserMeasurementType(Base):
    """Справочник типов измерений пользователя"""
    __tablename__ = "user_measurement_types"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    actual: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    # Тип данных (system - системный, custom - пользовательский)
    data_type: Mapped[MeasurementTypeEnum] = mapped_column(
        SQLAlchemyEnum(MeasurementTypeEnum), 
        nullable=False
    )
    
    # ID пользователя (null для системных типов)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("user.id"), 
        nullable=True
    )
    
    # Название типа измерения
    caption: Mapped[str] = mapped_column(nullable=False)
    
    # Определяем отношения с пользователем
    user: Mapped[Optional["User"]] = relationship("User")
    
    # Определяем отношения с измерениями
    measurements: Mapped[list["UserMeasurement"]] = relationship(
        "UserMeasurement", 
        back_populates="measurement_type"
    )
    
    # Уникальное ограничение: caption + user_id должны быть уникальными
    __table_args__ = (
        UniqueConstraint('caption', 'user_id', name='uq_measurement_type_caption_user'),
    )

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, caption={self.caption!r})"

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "data_type": self.data_type.value,
            "user_uuid": str(self.user.uuid) if self.user else None,
            "caption": self.caption,
            "actual": self.actual,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class UserMeasurement(Base):
    """Конкретные измерения пользователя"""
    __tablename__ = "user_measurements"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    actual: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    # ID пользователя
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    
    # ID типа измерения
    measurement_type_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("user_measurement_types.id"), 
        nullable=False
    )
    
    # Дата замера
    measurement_date: Mapped[date] = mapped_column(nullable=False)
    
    # Значение измерения (число)
    value: Mapped[float] = mapped_column(nullable=False)
    
    # Определяем отношения с пользователем
    user: Mapped["User"] = relationship("User")
    
    # Определяем отношения с типом измерения
    measurement_type: Mapped["UserMeasurementType"] = relationship(
        "UserMeasurementType", 
        back_populates="measurements"
    )
    
    # Уникальное ограничение: user_id + measurement_date + measurement_type_id должны быть уникальными
    __table_args__ = (
        UniqueConstraint('user_id', 'measurement_date', 'measurement_type_id', name='uq_measurement_user_date_type'),
    )

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, value={self.value})"

    def to_dict(self):
        # Если связанные объекты не загружены, загружаем их вручную
        user_uuid = None
        measurement_type_uuid = None
        
        if hasattr(self, 'user') and self.user:
            user_uuid = str(self.user.uuid)
        elif hasattr(self, 'user_id') and self.user_id:
            # Если user не загружен, но есть user_id, можем получить UUID из базы
            # Но для простоты пока оставим None
            user_uuid = None
            
        if hasattr(self, 'measurement_type') and self.measurement_type:
            measurement_type_uuid = str(self.measurement_type.uuid)
        elif hasattr(self, 'measurement_type_id') and self.measurement_type_id:
            # Если measurement_type не загружен, но есть measurement_type_id, можем получить UUID из базы
            # Но для простоты пока оставим None
            measurement_type_uuid = None
        
        return {
            "uuid": str(self.uuid),
            "user_uuid": user_uuid,
            "measurement_type_uuid": measurement_type_uuid,
            "measurement_date": self.measurement_date.isoformat(),
            "value": self.value,
            "actual": self.actual,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
