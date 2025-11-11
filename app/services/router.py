from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.users.dependencies import get_current_user_user
from app.users.models import User
from app.exercise_reference.dao import ExerciseReferenceDAO
from app.programs.dao import ProgramDAO
from app.trainings.dao import TrainingDAO
from app.users.dao import UsersDAO
from app.services.schemas import SupportRequestCreate, SupportRequestResponse
from app.email_service import email_service
from app.config import SETTINGS_JSON
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/service', tags=['Service'])


@router.get("/search/")
async def search_all(
    user_uuid: UUID,
    search_query: str = Query(..., description="Поисковая строка"),
    current_user: User = Depends(get_current_user_user)
):
    """Поиск по всем таблицам: exercise_reference, programs, trainings"""
    
    # Проверяем права доступа
    if str(current_user.uuid) != str(user_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете искать только для своего профиля"
        )
    
    if not current_user.is_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    # Получаем ID пользователя
    user = await UsersDAO.find_full_data(user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user_id = user.id
    logger.info(f"Поиск для пользователя {user_uuid} (ID: {user_id}) по запросу: '{search_query}'")
    
    try:
        # 1. Поиск в exercise_reference
        exercise_references = await ExerciseReferenceDAO.search_by_caption(
            search_query=search_query,
            user_id=user_id
        )
        
        # 2. Поиск в programs
        programs = await ProgramDAO.search_by_caption(
            search_query=search_query,
            user_id=user_id
        )
        
        # 3. Поиск в trainings
        trainings = await TrainingDAO.search_by_caption(
            search_query=search_query,
            user_id=user_id
        )
        
        logger.info(f"Найдено: {len(exercise_references)} exercise_references, {len(programs)} programs, {len(trainings)} trainings")
        
        return {
            "exercise_references": exercise_references,
            "programs": programs,
            "trainings": trainings,
            "total_results": len(exercise_references) + len(programs) + len(trainings)
        }
        
    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при выполнении поиска: {str(e)}"
        )


@router.post("/support-request/", response_model=SupportRequestResponse)
async def create_support_request(
    request_data: SupportRequestCreate,
    current_user: User = Depends(get_current_user_user)
):
    """Отправить обращение в службу поддержки"""
    
    # Проверяем права доступа
    if str(current_user.uuid) != str(request_data.user_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете отправлять обращения только от своего имени"
        )
    
    if not current_user.is_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    # Получаем данные пользователя
    user = await UsersDAO.find_full_data(request_data.user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Формируем имя пользователя
    user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    if not user_name:
        user_name = user.login
    
    try:
        # Отправляем письмо
        await email_service.send_support_request(
            user_email=user.email,
            user_name=user_name,
            request_type=request_data.request_type,
            message=request_data.message
        )
        
        logger.info(f"Обращение успешно отправлено от пользователя {user.email}")
        
        return SupportRequestResponse(
            success=True,
            message="Ваше обращение успешно отправлено в службу поддержки"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при отправке обращения: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при отправке обращения: {str(e)}"
        ) 


@router.get("/settings/")
async def get_service_settings():
    """Возвращает настройки сервисов"""
    return SETTINGS_JSON