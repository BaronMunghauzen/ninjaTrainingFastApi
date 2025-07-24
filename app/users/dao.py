from app.dao.base import BaseDAO
from app.users.models import User
from sqlalchemy import select


class UsersDAO(BaseDAO):
    model = User
    
    @classmethod
    async def find_users_by_avatar_id(cls, avatar_id: int):
        """Поиск всех пользователей, которые ссылаются на файл как аватар"""
        from app.database import async_session_maker
        async with async_session_maker() as session:
            query = select(cls.model).where(cls.model.avatar_id == avatar_id)
            result = await session.execute(query)
            return result.scalars().all()