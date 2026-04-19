from uuid import UUID, uuid4

from sqlalchemy import select

from app.anonymous_session.models import AnonymousSession
from app.dao.base import BaseDAO
from app.database import async_session_maker


class AnonymousSessionDAO(BaseDAO):
    model = AnonymousSession

    @classmethod
    async def create_session(cls) -> UUID:
        session_uuid = uuid4()
        async with async_session_maker() as db_session:
            async with db_session.begin():
                row = AnonymousSession(anonymous_session_id=session_uuid, actual=True)
                db_session.add(row)
        return session_uuid

    @classmethod
    async def exists_active(cls, session_id: UUID) -> bool:
        async with async_session_maker() as session:
            q = (
                select(cls.model.id)
                .where(
                    cls.model.anonymous_session_id == session_id,
                    cls.model.actual.is_(True),
                )
                .limit(1)
            )
            return (await session.scalar(q)) is not None
