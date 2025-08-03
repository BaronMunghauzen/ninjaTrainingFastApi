from datetime import datetime, timedelta
from typing import Optional
import logging
from sqlalchemy.future import select
from sqlalchemy import and_

from app.dao.base import BaseDAO
from app.email_verification.models import EmailVerification
from app.database import async_session_maker

# Настраиваем логирование
logger = logging.getLogger(__name__)


class EmailVerificationDAO(BaseDAO):
    model = EmailVerification
    
    @classmethod
    async def add(cls, **values):
        """Добавить запись с дополнительным логированием"""
        logger.info(f"EmailVerificationDAO.add вызван с параметрами: {values}")
        logger.info(f"Тип user_id: {type(values.get('user_id'))}, значение: {values.get('user_id')}")
        
        # Убеждаемся, что user_id является int
        if 'user_id' in values:
            values['user_id'] = int(values['user_id'])
            logger.info(f"user_id преобразован в int: {values['user_id']}")
        
        result = await super().add(**values)
        logger.info(f"EmailVerificationDAO.add завершен, результат: {result}")
        return result

    @classmethod
    async def find_valid_token(cls, token: str) -> Optional[EmailVerification]:
        """Найти действующий токен подтверждения"""
        logger.info(f"Поиск действительного токена: {token[:10]}...")
        
        async with async_session_maker() as session:
            query = select(cls.model).where(
                and_(
                    cls.model.token == token,
                    cls.model.used == False,
                    cls.model.expires_at > datetime.utcnow()
                )
            )
            logger.info(f"SQL запрос: {query}")
            result = await session.execute(query)
            verification = result.scalar_one_or_none()
            
            if verification:
                logger.info(f"Найден действительный токен для пользователя ID: {verification.user_id}")
                logger.info(f"Тип user_id в результате: {type(verification.user_id)}")
            else:
                logger.warning("Токен не найден или недействителен")
            
            return verification

    @classmethod
    async def find_by_user_id(cls, user_id: int) -> Optional[EmailVerification]:
        """Найти токен по ID пользователя"""
        logger.info(f"Поиск токена для пользователя ID: {user_id}")
        
        async with async_session_maker() as session:
            query = select(cls.model).where(
                and_(
                    cls.model.user_id == user_id,
                    cls.model.used == False,
                    cls.model.expires_at > datetime.utcnow()
                )
            )
            result = await session.execute(query)
            verification = result.scalar_one_or_none()
            
            if verification:
                logger.info(f"Найден токен для пользователя ID: {user_id}")
            else:
                logger.info(f"Токен для пользователя ID: {user_id} не найден")
            
            return verification

    @classmethod
    async def mark_as_used(cls, verification_id: int) -> bool:
        """Пометить токен как использованный"""
        logger.info(f"Пометка токена как использованного, ID: {verification_id}")
        
        async with async_session_maker() as session:
            query = select(cls.model).where(cls.model.id == verification_id)
            result = await session.execute(query)
            verification = result.scalar_one_or_none()
            
            if verification:
                verification.used = True
                await session.commit()
                logger.info(f"Токен ID: {verification_id} помечен как использованный")
                return True
            else:
                logger.warning(f"Токен ID: {verification_id} не найден")
                return False

    @classmethod
    async def delete_expired_tokens(cls) -> int:
        """Удалить истекшие токены"""
        logger.info("Удаление истекших токенов...")
        
        async with async_session_maker() as session:
            query = select(cls.model).where(
                and_(
                    cls.model.expires_at < datetime.utcnow(),
                    cls.model.used == True
                )
            )
            result = await session.execute(query)
            expired_tokens = result.scalars().all()
            
            for token in expired_tokens:
                await session.delete(token)
            
            await session.commit()
            logger.info(f"Удалено {len(expired_tokens)} истекших токенов")
            return len(expired_tokens) 