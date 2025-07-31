from uuid import UUID
import secrets
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Response, Depends, Query
from app.users.auth import get_password_hash, authenticate_user, create_access_token, create_refresh_token
from app.users.dao import UsersDAO
from app.users.dependencies import get_current_user, get_current_admin_user, get_current_user_user
from app.users.models import User
from app.users.schemas import SUserRegister, SUserAuth, SUserUpdate
from app.email_verification.dao import EmailVerificationDAO
from app.email_service import email_service

# Настраиваем логирование
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/auth', tags=['Auth'])


def generate_verification_token() -> str:
    """Генерировать токен для подтверждения email"""
    token = secrets.token_urlsafe(32)
    logger.info(f"Сгенерирован токен: {token[:10]}...")
    return token


@router.post("/register/")
async def register_user(user_data: SUserRegister) -> dict:
    logger.info(f"Попытка регистрации пользователя: {user_data.email}")
    
    user = await UsersDAO.find_one_or_none(email=user_data.email)
    if user:
        logger.warning(f"Пользователь с email {user_data.email} уже существует")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь уже существует'
        )
    
    user_dict = user_data.model_dump()
    user_dict['password'] = get_password_hash(user_data.password)
    
    # Устанавливаем значения по умолчанию только для обязательных полей
    user_dict['subscription_status'] = 'pending'
    user_dict['subscription_until'] = None
    user_dict['theme'] = 'dark'
    user_dict['is_user'] = True
    user_dict['is_admin'] = False
    # Добавляем новые поля для email verification
    user_dict['email_verified'] = False
    user_dict['email_verification_sent_at'] = datetime.utcnow()
    
    logger.info("Создание пользователя в БД...")
    # Создаем пользователя
    user_uuid = await UsersDAO.add(**user_dict)
    logger.info(f"Пользователь создан с UUID: {user_uuid}")
    
    # Получаем созданного пользователя
    new_user = await UsersDAO.find_full_data(user_uuid)
    logger.info(f"Получен пользователь с ID: {new_user.id}")
    
    # Генерируем токен для подтверждения email
    verification_token = generate_verification_token()
    
    logger.info("Сохранение токена в БД...")
    # Сохраняем токен в БД
    await EmailVerificationDAO.add(
        user_id=new_user.id,
        token=verification_token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    logger.info("Токен сохранен в БД")
    
    # Отправляем email для подтверждения
    try:
        logger.info("Попытка отправки email подтверждения...")
        await email_service.send_verification_email(new_user.email, verification_token)
        logger.info("Email подтверждения отправлен успешно")
    except Exception as e:
        # Логируем ошибку, но не прерываем регистрацию
        logger.error(f"Ошибка отправки email: {e}")
        logger.error(f"Тип ошибки: {type(e).__name__}")
    
    # Создаем токены для нового пользователя
    access_token = create_access_token({"sub": str(new_user.id)})
    refresh_token = create_refresh_token({"sub": str(new_user.id)})
    
    logger.info(f"Регистрация завершена успешно для {new_user.email}")
    return {
        'message': 'Вы успешно зарегистрированы! Проверьте email для подтверждения.',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'email_verified': False
    }


@router.post("/login/")
async def auth_user(response: Response, user_data: SUserAuth):
    logger.info(f"Попытка входа пользователя: {user_data.user_identity}")
    
    check = await authenticate_user(user_identity=user_data.user_identity, password=user_data.password)
    if check is None:
        logger.warning(f"Неудачная попытка входа для: {user_data.user_identity}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Неверные данные для входа или пароль')
    
    access_token = create_access_token({"sub": str(check.id)})
    refresh_token = create_refresh_token({"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    
    logger.info(f"Успешный вход пользователя: {check.email}")
    return {
        'access_token': access_token, 
        'refresh_token': refresh_token,
        'email_verified': check.email_verified
    }


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)):
    return await user_data.to_dict()


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}


@router.get("/all_users/")
async def get_all_users(user_data: User = Depends(get_current_admin_user)):
    return await UsersDAO.find_all()

@router.put("/update/{user_uuid}")
async def update_user(user_uuid: UUID, user: SUserUpdate, user_data: User = Depends(get_current_user_user)) -> dict:
    update_data = user.model_dump(exclude_unset=True)
    check = await UsersDAO.update(user_uuid, **update_data)
    if check:
        updated_user = await UsersDAO.find_full_data(user_uuid)
        return {
            "message": "Пользователь успешно обновлен!",
            "user": await updated_user.to_dict()
        }
    else:
        return {"message": "Ошибка при обновлении пользователя!"}


# Новые методы для email verification
@router.get("/verify-email/")
async def verify_email(token: str = Query(..., description="Токен подтверждения email")):
    """Подтвердить email по токену"""
    logger.info(f"Попытка подтверждения email с токеном: {token[:10]}...")
    
    verification = await EmailVerificationDAO.find_valid_token(token)
    if not verification:
        logger.warning(f"Недействительный токен: {token[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или истекший токен"
        )
    
    logger.info(f"Найден действительный токен для пользователя ID: {verification.user_id}")
    
    # Находим пользователя по ID и получаем его UUID
    user = await UsersDAO.find_one_or_none_by_id(verification.user_id)
    if not user:
        logger.error(f"Пользователь с ID {verification.user_id} не найден")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Подтверждаем email пользователя по UUID
    await UsersDAO.update(user.uuid, email_verified=True)
    await EmailVerificationDAO.mark_as_used(verification.id)
    
    logger.info(f"Email подтвержден для пользователя ID: {verification.user_id}")
    return {"message": "Email успешно подтвержден!"}


@router.post("/resend-verification/")
async def resend_verification_email(email: str = Query(..., description="Email для повторной отправки")):
    """Повторно отправить email для подтверждения"""
    logger.info(f"Запрос повторной отправки email для: {email}")
    
    user = await UsersDAO.find_one_or_none(email=email)
    if not user:
        logger.warning(f"Пользователь не найден: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    if user.email_verified:
        logger.warning(f"Email уже подтвержден для: {email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже подтвержден"
        )
    
    logger.info(f"Найден пользователь ID: {user.id} для повторной отправки")
    
    # Удаляем старый токен, если есть
    old_verification = await EmailVerificationDAO.find_by_user_id(user.id)
    if old_verification:
        logger.info("Удаление старого токена...")
        await EmailVerificationDAO.mark_as_used(old_verification.id)
    
    # Генерируем новый токен
    verification_token = generate_verification_token()
    
    logger.info("Создание нового токена...")
    # Создаем новый токен
    await EmailVerificationDAO.add(
        user_id=user.id,
        token=verification_token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    # Обновляем время отправки
    await UsersDAO.update(user.uuid, email_verification_sent_at=datetime.utcnow())
    
    # Отправляем email
    try:
        logger.info("Попытка повторной отправки email...")
        await email_service.send_verification_email(user.email, verification_token)
        logger.info("Email повторно отправлен успешно")
        return {"message": "Email для подтверждения отправлен повторно"}
    except Exception as e:
        logger.error(f"Ошибка повторной отправки email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка отправки email: {str(e)}"
        )