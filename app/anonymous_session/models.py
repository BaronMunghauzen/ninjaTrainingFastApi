from uuid import UUID

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, int_pk, uuid_field


class AnonymousSession(Base):
    """Зарегистрированная анонимная сессия (идентификатор для заголовка anonymous_session_id)."""

    __tablename__ = "anonymous_session"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    actual: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    anonymous_session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
