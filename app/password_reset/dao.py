from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, and_, or_
from app.database import async_session_maker
from app.password_reset.models import PasswordResetCode
import secrets
import logging

logger = logging.getLogger(__name__)


class PasswordResetDAO:
    @staticmethod
    async def create_code(user_id: int, expires_minutes: int = 10) -> str:
        """Создать код сброса пароля"""
        # Генерируем 6-значный код
        code = f"{secrets.randbelow(900000) + 100000:06d}"
        
        async with async_session_maker() as session:
            password_reset_code = PasswordResetCode(
                user_id=user_id,
                code=code,
                expires_at=datetime.utcnow() + timedelta(minutes=expires_minutes)
            )
            session.add(password_reset_code)
            await session.commit()
            await session.refresh(password_reset_code)
            
        logger.info(f"Создан код сброса пароля для пользователя {user_id}: {code}")
        return code

    @staticmethod
    async def find_valid_code(email: str, code: str) -> Optional[PasswordResetCode]:
        """Найти действительный код сброса пароля"""
        async with async_session_maker() as session:
            stmt = select(PasswordResetCode).join(PasswordResetCode.user).where(
                and_(
                    PasswordResetCode.user.has(email=email),
                    PasswordResetCode.code == code,
                    PasswordResetCode.used == False,
                    PasswordResetCode.expires_at > datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def mark_as_used(code_id: int) -> bool:
        """Пометить код как использованный"""
        async with async_session_maker() as session:
            stmt = select(PasswordResetCode).where(PasswordResetCode.id == code_id)
            result = await session.execute(stmt)
            code = result.scalar_one_or_none()
            
            if code:
                code.used = True
                await session.commit()
                logger.info(f"Код {code_id} помечен как использованный")
                return True
            return False

    @staticmethod
    async def delete_old_codes(user_id: int) -> None:
        """Удалить все коды пользователя"""
        async with async_session_maker() as session:
            # Удаляем ВСЕ коды пользователя (активные, использованные и истекшие)
            stmt = select(PasswordResetCode).where(
                PasswordResetCode.user_id == user_id
            )
            result = await session.execute(stmt)
            all_codes = result.scalars().all()
            
            for code in all_codes:
                await session.delete(code)
            
            await session.commit()
            logger.info(f"Удалено {len(all_codes)} кодов для пользователя {user_id}")

    @staticmethod
    async def find_by_user_id(user_id: int) -> Optional[PasswordResetCode]:
        """Найти активный код пользователя"""
        async with async_session_maker() as session:
            stmt = select(PasswordResetCode).where(
                and_(
                    PasswordResetCode.user_id == user_id,
                    PasswordResetCode.used == False,
                    PasswordResetCode.expires_at > datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
