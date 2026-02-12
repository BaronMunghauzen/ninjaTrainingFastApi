from uuid import UUID
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException, status, Response, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse
from app.users.auth import get_password_hash, authenticate_user, create_access_token, create_refresh_token
from app.users.dao import UsersDAO
from app.users.dependencies import get_current_user, get_current_admin_user, get_current_user_user
from app.users.models import User
from app.users.schemas import SUserRegister, SUserAuth, SUserUpdate, BroadcastEmailRequest
from app.email_verification.dao import EmailVerificationDAO
from app.email_service import email_service
from app.telegram_service import telegram_service
from app.files.service import FileService
from app.files.dao import FilesDAO
from app.files.schemas import FileUploadResponse, FileResponse as FileResponseSchema

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
    user_dict['actual'] = True
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
    
    # Автоматически активируем триальный период
    try:
        from app.subscriptions.service import SubscriptionService
        trial_result = await SubscriptionService.create_trial_subscription(new_user.id)
        logger.info(f"Триальная подписка активирована для пользователя {new_user.id} до {trial_result['expires_at']}")
    except Exception as e:
        logger.error(f"Ошибка активации триального периода: {e}")
        # Не прерываем регистрацию, если не удалось активировать триал
    
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
    
    # Отправляем уведомление в Telegram о новой регистрации
    try:
        await telegram_service.notify_new_registration(
            user_email=new_user.email,
            user_login=new_user.login,
            user_id=new_user.id,
            user_uuid=str(new_user.uuid)
        )
    except Exception as e:
        # Логируем ошибку, но не прерываем регистрацию
        logger.error(f"Ошибка отправки Telegram уведомления о регистрации: {e}")
    
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
    """Получить информацию о текущем пользователе и обновить время последнего входа"""
    # Обновляем время последнего входа
    await UsersDAO.update(user_data.uuid, last_login_at=datetime.utcnow())
    
    # Обновляем объект user_data для возврата актуальных данных
    updated_user = await UsersDAO.find_one_or_none(uuid=user_data.uuid)
    if updated_user:
        return await updated_user.to_dict()
    
    return await user_data.to_dict()


@router.delete("/me/")
async def deactivate_profile(current_user: User = Depends(get_current_user_user)):
    if not current_user.actual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Профиль уже деактивирован"
        )
    
    await UsersDAO.update(current_user.uuid, actual=False)
    return {"message": "Профиль успешно деактивирован"}


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}


@router.get("/all_users/", summary="Получить всех пользователей с пагинацией и сортировкой")
async def get_all_users(
    user_data: User = Depends(get_current_admin_user),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    sort_by: Optional[str] = Query(None, description="Поле для сортировки (id, login, email, first_name, last_name, etc.)"),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Порядок сортировки (asc или desc)"),
    actual: Optional[bool] = Query(None, description="Фильтр по актуальности пользователя"),
    email_verified: Optional[bool] = Query(None, description="Фильтр по подтверждению email"),
    email_notifications_enabled: Optional[bool] = Query(None, description="Фильтр по включенным email уведомлениям")
) -> dict:
    """Получить всех пользователей с пагинацией и сортировкой (только для администраторов)"""
    # Формируем фильтры
    filters = {}
    if actual is not None:
        filters['actual'] = actual
    if email_verified is not None:
        filters['email_verified'] = email_verified
    if email_notifications_enabled is not None:
        filters['email_notifications_enabled'] = email_notifications_enabled
    
    result = await UsersDAO.find_all_paginated(
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order,
        **filters
    )
    
    return {
        "items": [await user.to_dict() for user in result["items"]],
        "pagination": result["pagination"]
    }

@router.put("/update/{user_uuid}")
async def update_user(user_uuid: UUID, user: SUserUpdate, user_data: User = Depends(get_current_user_user)) -> dict:
    update_data = user.model_dump(exclude_unset=True)
    
    # Проверяем, действительно ли изменился email
    email_changed = False
    if 'email' in update_data:
        # Получаем текущего пользователя из БД для сравнения
        current_user_from_db = await UsersDAO.find_full_data(user_uuid)
        if current_user_from_db and current_user_from_db.email != update_data['email']:
            email_changed = True
            update_data['email_verified'] = False
            update_data['email_verification_sent_at'] = datetime.utcnow()
            logger.info(f"Email действительно изменился для пользователя {user_uuid}: {current_user_from_db.email} -> {update_data['email']}")
        else:
            logger.info(f"Email не изменился для пользователя {user_uuid}, пропускаем email verification")
    
    check = await UsersDAO.update(user_uuid, **update_data)
    if check:
        updated_user = await UsersDAO.find_full_data(user_uuid)
        
        # Если email действительно изменился, отправляем новое подтверждение
        if email_changed:
            try:
                # Удаляем старый токен, если есть
                old_verification = await EmailVerificationDAO.find_by_user_id(updated_user.id)
                if old_verification:
                    logger.info("Удаление старого токена...")
                    await EmailVerificationDAO.mark_as_used(old_verification.id)
                
                # Генерируем новый токен
                verification_token = generate_verification_token()
                logger.info("Создание нового токена для обновленного email...")
                
                # Создаем новый токен
                await EmailVerificationDAO.add(
                    user_id=updated_user.id,
                    token=verification_token,
                    expires_at=datetime.utcnow() + timedelta(hours=24)
                )
                
                # Отправляем email подтверждения на новый email
                logger.info(f"Отправка email подтверждения на новый email: {updated_user.email}")
                await email_service.send_verification_email(updated_user.email, verification_token)
                logger.info("Email подтверждения отправлен успешно")
                
                return {
                    "message": "Пользователь успешно обновлен! Проверьте новый email для подтверждения.",
                    "user": await updated_user.to_dict()
                }
            except Exception as e:
                logger.error(f"Ошибка отправки email подтверждения: {e}")
                # Возвращаем успешное обновление, но с предупреждением
                return {
                    "message": "Пользователь успешно обновлен! Ошибка отправки email подтверждения.",
                    "user": await updated_user.to_dict()
                }
        else:
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
        # Возвращаем страницу с ошибкой вместо JSON
        return FileResponse("static/email-verification-error.html", media_type="text/html")
    
    logger.info(f"Найден действительный токен для пользователя ID: {verification.user_id}")
    
    # Находим пользователя по ID и получаем его UUID
    user = await UsersDAO.find_one_or_none_by_id(verification.user_id)
    if not user:
        logger.error(f"Пользователь с ID {verification.user_id} не найден")
        # Возвращаем страницу с ошибкой вместо JSON
        return FileResponse("static/email-verification-error.html", media_type="text/html")
    
    # Подтверждаем email пользователя по UUID
    await UsersDAO.update(user.uuid, email_verified=True)
    await EmailVerificationDAO.mark_as_used(verification.id)
    
    logger.info(f"Email подтвержден для пользователя ID: {verification.user_id}")
    # Возвращаем страницу успеха вместо JSON
    return FileResponse("static/email-verified.html", media_type="text/html")


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


# Эндпоинты для работы с аватаром
@router.post("/upload/avatar/{user_uuid}", response_model=FileUploadResponse)
async def upload_avatar(
    user_uuid: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_user)
):
    """Загрузка аватара пользователя"""
    # Проверяем, что пользователь загружает свой аватар
    if str(current_user.uuid) != str(user_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете загружать только свой аватар"
        )
    
    # Проверяем, что пользователь имеет права
    if not current_user.is_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    # Ищем существующий аватар
    existing_avatar = await FilesDAO.find_avatar_by_user_id(current_user.id)
    old_file_uuid = str(existing_avatar.uuid) if existing_avatar else None
    
    # Сохраняем новый файл
    saved_file = await FileService.save_file(
        file=file,
        entity_type="user",
        entity_id=current_user.id,
        old_file_uuid=old_file_uuid
    )
    
    # Обновляем поле avatar_id у пользователя
    await UsersDAO.update(current_user.uuid, avatar_id=saved_file.id)
    
    # Удаляем старые аватары пользователя (оставляем только новый)
    if existing_avatar:
        await FilesDAO.delete_old_avatars_for_user(current_user.id, keep_latest=True)
    
    return FileUploadResponse(
        message="Аватар успешно загружен",
        file=FileResponseSchema.model_validate(saved_file)
    )


@router.delete("/avatar/{user_uuid}")
async def delete_avatar(
    user_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
):
    """Удаление аватара пользователя"""
    # Проверяем, что пользователь удаляет свой аватар
    if str(current_user.uuid) != str(user_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете удалять только свой аватар"
        )
    
    # Проверяем, что пользователь имеет права
    if not current_user.is_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    # Ищем текущий аватар пользователя
    existing_avatar = await FilesDAO.find_avatar_by_user_id(current_user.id)
    
    if not existing_avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аватар не найден"
        )
    
    # Удаляем файл с сервера и из БД
    success = await FileService.delete_file_by_uuid(str(existing_avatar.uuid))
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении файла"
        )
    
    # Обновляем поле avatar_id у пользователя (устанавливаем в None)
    await UsersDAO.update(current_user.uuid, avatar_id=None)
    
    return {"message": "Аватар успешно удален"}


@router.post("/toggle-email-notifications/{user_uuid}", summary="Переключить email уведомления")
async def toggle_email_notifications(
    user_uuid: UUID,
    admin_user: User = Depends(get_current_admin_user)
) -> dict:
    """Переключить статус email уведомлений для пользователя (только для администраторов)"""
    # Находим пользователя, для которого нужно изменить настройки
    target_user = await UsersDAO.find_one_or_none(uuid=user_uuid)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Получаем текущее значение или устанавливаем True по умолчанию
    current_value = target_user.email_notifications_enabled
    new_value = not current_value if current_value is not None else True
    
    # Обновляем значение
    await UsersDAO.update(user_uuid, email_notifications_enabled=new_value)
    
    return {
        "message": "Настройки email уведомлений обновлены",
        "email_notifications_enabled": new_value,
        "user_uuid": str(user_uuid)
    }


@router.post("/broadcast-email/", summary="Массовая рассылка email (только для администраторов)")
async def broadcast_email(
    request: BroadcastEmailRequest,
    admin_user: User = Depends(get_current_admin_user)
) -> dict:
    """Отправить email всем пользователям с включенными email уведомлениями"""
    try:
        # Находим всех пользователей с включенными email уведомлениями и actual = True
        users = await UsersDAO.find_users_with_email_notifications_enabled()
        
        logger.info(f"Найдено пользователей с включенными email уведомлениями: {len(users)}")
        
        if not users:
            return {
                "message": "Нет пользователей с включенными email уведомлениями",
                "sent_count": 0,
                "total_users": 0
            }
        
        # Собираем список email адресов
        recipients = [user.email for user in users if user.email]
        logger.info(f"Список получателей: {recipients}")
        
        if not recipients:
            return {
                "message": "Не найдено email адресов для рассылки",
                "sent_count": 0,
                "total_users": len(users)
            }
        
        # Отправляем массовую рассылку
        result = await email_service.send_broadcast_email(
            recipients=recipients,
            subject=request.subject,
            body=request.body
        )
        
        return {
            "message": "Массовая рассылка email выполнена",
            "total_users": len(users),
            "success_count": result["success_count"],
            "failed_count": result["failed_count"],
            "failed_emails": result["failed_emails"]
        }
        
    except Exception as e:
        logger.error(f"Ошибка при массовой рассылке email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при отправке рассылки: {str(e)}"
        )


