from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from typing import Optional, List
from datetime import date
from pathlib import Path
from io import BytesIO

from app.food_recognition.dao import FoodRecognitionDAO
from app.food_recognition.rb import RBFoodRecognition
from app.food_recognition.schemas import SFoodRecognition, SFoodRecognitionAdd, SFoodRecognitionUpdate, SFoodRecognitionListResponse
from app.food_recognition.service import FoodRecognitionService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO
from app.files.service import FileService
from app.subscriptions.dao import SubscriptionDAO
from app.logger import logger

router = APIRouter(prefix='/api/food-recognition', tags=['Распознавание еды по фото'])

# Лимиты запросов
TRIAL_DAILY_LIMIT = 3
PAID_DAILY_LIMIT = 20


async def check_subscription_and_limits(user: User):
    """
    Проверяет, имеет ли пользователь активную подписку и не превысил ли лимит запросов
    
    Raises:
        HTTPException: Если нет подписки или превышен лимит
    """
    # Проверяем статус подписки
    if user.subscription_status.value != 'active':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Для использования функции распознавания еды требуется активная подписка"
        )
    
    # Определяем, триальная ли подписка
    subscriptions = await SubscriptionDAO.find_all(
        user_id=user.id,
        is_trial=False
    )
    is_trial = len(subscriptions) == 0
    
    # Определяем лимит
    daily_limit = TRIAL_DAILY_LIMIT if is_trial else PAID_DAILY_LIMIT
    
    # Подсчитываем количество запросов сегодня
    requests_today = await FoodRecognitionDAO.count_requests_today(user.id)
    
    if requests_today >= daily_limit:
        limit_type = "триальном" if is_trial else "обычном"
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Превышен лимит запросов на {limit_type} подписке. "
                   f"Доступно {daily_limit} запросов в день. "
                   f"Использовано сегодня: {requests_today}"
        )


@router.post("/recognize", response_model=SFoodRecognition)
async def recognize_food(
    file: UploadFile = File(..., description="Фотография еды"),
    comment: Optional[str] = Form(None, description="Комментарий для уточнения"),
    user: User = Depends(get_current_user)
):
    """
    Распознавание еды по фотографии
    
    Доступно только для пользователей с активной подпиской.
    Лимиты:
    - Триальная подписка: 3 запроса в день
    - Обычная подписка: 20 запросов в день
    """
    # Проверяем подписку и лимиты
    await check_subscription_and_limits(user)
    
    try:
        # Читаем содержимое файла до сохранения, чтобы можно было использовать его дважды
        file_content = await file.read()
        file_size = len(file_content)
        
        # Валидация размера файла
        if file_size > FileService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Файл слишком большой. Максимальный размер: {FileService.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Валидация типа файла
        FileService.validate_image_file(file)
        
        # Сохраняем файл на диск
        from uuid import uuid4
        upload_dir = Path(FileService.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        generated_uuid = str(uuid4())
        file_extension = Path(file.filename).suffix if file.filename else ".jpg"
        new_filename = f"{generated_uuid}{file_extension}"
        file_path = upload_dir / new_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Создаем запись в БД для файла
        file_data = {
            "filename": file.filename or "unknown",
            "file_path": str(file_path),
            "file_size": file_size,
            "mime_type": file.content_type or "image/jpeg",
            "entity_type": "food_recognition",
            "entity_id": 0  # Временно
        }
        saved_file_uuid = await FilesDAO.add(**file_data)
        saved_file = await FilesDAO.find_one_or_none(uuid=saved_file_uuid)
        
        # Создаем временный файл-объект для отправки в сервис
        temp_file = BytesIO(file_content)
        
        # Создаем UploadFile-подобный объект для отправки в сервис
        file_for_service = UploadFile(
            filename=file.filename,
            file=temp_file
        )
        # Устанавливаем content_type для корректной отправки
        file_for_service.content_type = file.content_type or "image/jpeg"
        
        # Отправляем запрос на распознавание
        response = await FoodRecognitionService.recognize_food(file_for_service, comment)
        
        # Парсим ответ
        parsed_data = FoodRecognitionService.parse_response(response)
        
        # Подготавливаем данные для сохранения в БД
        db_data = {
            "user_id": user.id,
            "image_id": saved_file.id,
            "comment": comment,
            **parsed_data
        }
        
        # Сохраняем в БД
        recognition_uuid = await FoodRecognitionDAO.add(**db_data)
        
        # Получаем созданную запись
        recognition = await FoodRecognitionDAO.find_full_data(recognition_uuid)
        
        # Обновляем entity_id в файле
        if saved_file:
            await FilesDAO.update(saved_file.uuid, entity_id=recognition.id)
        
        # Возвращаем результат
        result = recognition.to_dict()
        result["json_response"] = response  # Возвращаем полный ответ
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при распознавании еды для пользователя {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при распознавании еды: {str(e)}"
        )


@router.get("/", response_model=SFoodRecognitionListResponse)
async def get_food_recognition_history(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    created_from: Optional[date] = Query(None, description="Дата создания (от)"),
    created_to: Optional[date] = Query(None, description="Дата создания (до)"),
    actual: Optional[bool] = Query(None, description="Фильтр по актуальности"),
    name: Optional[str] = Query(None, description="Поиск по названию (вхождение без учета регистра)"),
    user: User = Depends(get_current_user)
):
    """
    Получить историю всех запросов распознавания еды пользователя
    
    Фильтрация:
    - created_from/created_to: по дате создания
    - actual: по актуальности записи
    - name: поиск по названию еды (вхождение строки без учета регистра)
    
    Сортировка: по дате создания, самые новые первыми
    """
    try:
        result = await FoodRecognitionDAO.find_by_user_with_pagination(
            user_id=user.id,
            page=page,
            size=size,
            created_from=created_from,
            created_to=created_to,
            actual=actual,
            name=name
        )
        
        # Преобразуем объекты в словари
        items = [item.to_dict() for item in result["items"]]
        
        return {
            "items": items,
            "pagination": result["pagination"]
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении истории распознавания для пользователя {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении истории распознавания"
        )


@router.get("/{recognition_uuid}", response_model=SFoodRecognition)
async def get_food_recognition_by_uuid(
    recognition_uuid: UUID,
    user: User = Depends(get_current_user)
):
    """Получить запись распознавания еды по UUID"""
    try:
        recognition = await FoodRecognitionDAO.find_full_data(recognition_uuid)
        
        # Проверяем, что запись принадлежит пользователю
        if recognition.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет доступа к этой записи"
            )
        
        result = recognition.to_dict()
        # Парсим json_response обратно в словарь
        if result.get("json_response"):
            import json
            result["json_response"] = json.loads(result["json_response"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении записи распознавания {recognition_uuid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении записи распознавания"
        )


@router.put("/{recognition_uuid}/deactivate")
async def deactivate_food_recognition(
    recognition_uuid: UUID,
    user: User = Depends(get_current_user)
):
    """Деактуализировать запись распознавания еды (установить actual = False)"""
    try:
        recognition = await FoodRecognitionDAO.find_one_or_none(uuid=recognition_uuid)
        
        if not recognition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись распознавания не найдена"
            )
        
        # Проверяем, что запись принадлежит пользователю
        if recognition.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет доступа к этой записи"
            )
        
        # Обновляем actual = False
        await FoodRecognitionDAO.update(recognition_uuid, actual=False)
        
        return {"message": "Запись деактуализирована", "uuid": str(recognition_uuid)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при деактуализации записи {recognition_uuid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при деактуализации записи"
        )

