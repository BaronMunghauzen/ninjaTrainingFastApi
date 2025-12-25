from typing import TYPE_CHECKING
from sqlalchemy import Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import text
from app.database import Base, int_pk, uuid_field, str_uniq

if TYPE_CHECKING:
    from app.users.models import User


class LastValue(Base):
    __tablename__ = "last_values"
    __table_args__ = (
        UniqueConstraint('user_id', 'code', name='uq_last_values_user_code'),
    )

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    actual: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)

    # Связь с пользователем
    user: Mapped["User"] = relationship("User", back_populates="last_values")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, uuid={self.uuid}, code={self.code}, user_id={self.user_id})"

    def to_dict(self):
        # Получаем UUID пользователя из предзагруженного связанного объекта
        user_uuid = None
        if hasattr(self, 'user') and self.user is not None:
            # Связь должна быть предзагружена через joinedload в DAO
            user_uuid = str(self.user.uuid)
        elif self.user_id:
            # Fallback: если связь не загружена (не должно происходить при правильном использовании)
            # В этом случае нужно будет делать запрос, но это не рекомендуется
            # Лучше всегда использовать методы DAO с joinedload
            pass
        
        return {
            "uuid": str(self.uuid),
            "user_uuid": user_uuid,
            "name": self.name,
            "code": self.code,
            "value": self.value,
            "actual": self.actual,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

