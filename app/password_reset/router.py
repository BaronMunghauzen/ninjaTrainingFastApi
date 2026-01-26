import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Query
from app.password_reset.dao import PasswordResetDAO
from app.password_reset.schemas import (
    PasswordResetRequest, 
    PasswordResetVerify,
    PasswordResetConfirm, 
    PasswordResetResponse
)
from app.users.dao import UsersDAO
from app.users.auth import get_password_hash
from app.email_service import email_service
from app.users.models import User
from app.database import async_session_maker
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/auth', tags=['Password Reset'])


@router.post("/forgot-password/", response_model=PasswordResetResponse)
async def forgot_password(request: PasswordResetRequest):
    """Запрос на сброс пароля"""
    logger.info(f"Запрос сброса пароля для email: {request.email}")
    
    # Проверяем, существует ли пользователь с таким email (case-insensitive)
    user = None
    async with async_session_maker() as session:
        stmt = select(User).where(func.lower(User.email) == func.lower(request.email))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            session.expunge(user)
    if not user:
        # Для безопасности не сообщаем, что пользователь не найден
        logger.warning(f"Попытка сброса пароля для несуществующего email: {request.email}")
        return PasswordResetResponse(
            message="Если пользователь с таким email существует, на него будет отправлен код для сброса пароля"
        )
    
    # Удаляем старые коды пользователя (всегда создаем новый)
    await PasswordResetDAO.delete_old_codes(user.id)
    
    # Создаем новый код
    try:
        code = await PasswordResetDAO.create_code(user.id, expires_minutes=10)
        logger.info(f"Создан код сброса пароля для пользователя {user.id}")
        
        # Отправляем email с кодом для сброса
        await email_service.send_password_reset_code(user.email, code)
        logger.info(f"Email с кодом сброса пароля отправлен на {user.email}")
        
        return PasswordResetResponse(
            message="Код для сброса пароля отправлен на ваш email"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при создании кода сброса пароля: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при отправке кода для сброса пароля"
        )


@router.post("/verify-code/", response_model=PasswordResetResponse)
async def verify_code(request: PasswordResetVerify):
    """Проверка кода подтверждения"""
    logger.info(f"Попытка проверки кода для email: {request.email}")
    
    # Проверяем код
    code_record = await PasswordResetDAO.find_valid_code(request.email, request.code)
    if not code_record:
        logger.warning(f"Недействительный или истекший код для {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или истекший код подтверждения"
        )
    
    logger.info(f"Код подтвержден для пользователя {code_record.user_id}")
    return PasswordResetResponse(
        message="Код подтвержден успешно"
    )


@router.post("/reset-password/", response_model=PasswordResetResponse)
async def reset_password(request: PasswordResetConfirm):
    """Сброс пароля по коду"""
    logger.info(f"Попытка сброса пароля для email: {request.email}")
    
    # Проверяем код
    code_record = await PasswordResetDAO.find_valid_code(request.email, request.code)
    if not code_record:
        logger.warning(f"Недействительный или истекший код для {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или истекший код подтверждения"
        )
    
    # Получаем пользователя
    user = await UsersDAO.find_one_or_none_by_id(code_record.user_id)
    if not user:
        logger.error(f"Пользователь с ID {code_record.user_id} не найден")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    try:
        # Обновляем пароль
        hashed_password = get_password_hash(request.new_password)
        await UsersDAO.update(user.uuid, password=hashed_password)
        
        # Помечаем код как использованный
        await PasswordResetDAO.mark_as_used(code_record.id)
        
        logger.info(f"Пароль успешно сброшен для пользователя {user.id}")
        
        return PasswordResetResponse(
            message="Пароль успешно изменен"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при сбросе пароля: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при изменении пароля"
        )


