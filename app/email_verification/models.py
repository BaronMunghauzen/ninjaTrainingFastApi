from typing import Optional
from datetime import datetime
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field

from app.users.models import User


class EmailVerification(Base):
    __tablename__ = "email_verification"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    token: Mapped[str] = mapped_column(unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    used: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, server_default=text('now()'), nullable=False)

    # Связь с пользователем
    user: Mapped["User"] = relationship("User")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, user_id={self.user_id}, used={self.used})"

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "user_id": self.user_id,
            "token": self.token,
            "expires_at": self.expires_at.isoformat(),
            "used": self.used,
            "created_at": self.created_at.isoformat()
        } 