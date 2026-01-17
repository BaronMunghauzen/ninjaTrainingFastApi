"""
DAO для работы с промокодами
"""
from app.dao.base import BaseDAO
from app.promo_codes.models import PromoCode
from app.database import async_session_maker
from sqlalchemy import select


class PromoCodeDAO(BaseDAO):
    """DAO для работы с промокодами"""
    model = PromoCode
    
    @classmethod
    async def find_by_code(cls, code: str):
        """Найти промокод по коду"""
        async with async_session_maker() as session:
            query = select(cls.model).where(cls.model.code == code.upper().strip())
            result = await session.execute(query)
            promo_code = result.scalar_one_or_none()
            if promo_code:
                session.expunge(promo_code)
            return promo_code

