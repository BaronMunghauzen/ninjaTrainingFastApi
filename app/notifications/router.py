from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
import uuid as uuid_lib

from app.database import get_async_session
from app.users.models import User
from app.services.firebase_service import FirebaseService
from app.services.scheduler_service import SchedulerService
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Pydantic модели для запросов
class UpdateFCMTokenRequest(BaseModel):
    user_uuid: str
    fcm_token: str

class ScheduleTimerRequest(BaseModel):
    user_uuid: str
    exercise_uuid: str
    exercise_name: str
    duration_seconds: int

class CancelTimerRequest(BaseModel):
    user_uuid: str


@router.post("/update-fcm-token")
async def update_fcm_token(
    request: UpdateFCMTokenRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Обновление FCM токена пользователя
    
    Вызывается Flutter при:
    - Первом запуске приложения
    - Обновлении токена (Firebase может обновлять токены)
    - Переустановке приложения
    """
    try:
        result = await session.execute(
            select(User).filter(User.uuid == request.user_uuid)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Обновляем FCM токен
        user.fcm_token = request.fcm_token
        await session.commit()
        
        return {
            "status": "success",
            "message": "FCM токен обновлен",
            "user_uuid": request.user_uuid
        }
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обновления токена: {str(e)}")


@router.post("/schedule-timer")
async def schedule_timer(
    request: ScheduleTimerRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Планирование уведомления о завершении таймера
    
    Вызывается Flutter когда пользователь запускает таймер отдыха.
    Backend запланирует отправку push-уведомления через N секунд.
    """
    try:
        # Получаем пользователя и его FCM токен
        result = await session.execute(
            select(User).filter(User.uuid == request.user_uuid)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        if not user.fcm_token:
            raise HTTPException(
                status_code=400, 
                detail="У пользователя нет FCM токена. Приложение должно сначала отправить токен."
            )
        
        # Вычисляем время когда нужно отправить уведомление
        scheduled_time = datetime.utcnow() + timedelta(seconds=request.duration_seconds)
        
        # Создаем уникальный ID задачи
        job_id = f"timer_{request.user_uuid}_{request.exercise_uuid}_{int(datetime.utcnow().timestamp())}"
        
        # Планируем задачу через Scheduler
        SchedulerService.schedule_timer_notification(
            job_id=job_id,
            scheduled_time=scheduled_time,
            fcm_token=user.fcm_token,
            exercise_name=request.exercise_name,
        )
        
        return {
            "status": "success",
            "message": f"Уведомление запланировано через {request.duration_seconds} сек",
            "job_id": job_id,
            "scheduled_time": scheduled_time.isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка планирования: {str(e)}")


@router.post("/cancel-timer")
async def cancel_timer(
    request: CancelTimerRequest,
):
    """
    Отмена запланированного уведомления
    
    Вызывается если пользователь вручную закрыл таймер до его завершения.
    """
    try:
        # Находим и отменяем все задачи этого пользователя
        jobs = SchedulerService.get_scheduled_jobs()
        cancelled_count = 0
        
        for job in jobs:
            if job.id.startswith(f"timer_{request.user_uuid}_"):
                SchedulerService.cancel_job(job.id)
                cancelled_count += 1
        
        return {
            "status": "success",
            "message": f"Отменено задач: {cancelled_count}",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отмены: {str(e)}")


@router.post("/test-notification")
async def test_notification(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Тестовая отправка уведомления (для проверки что FCM работает)
    """
    try:
        result = await session.execute(
            select(User).filter(User.uuid == user_uuid)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.fcm_token:
            raise HTTPException(status_code=400, detail="FCM токен не найден")
        
        # Инициализируем Firebase если не инициализирован
        FirebaseService.initialize()
        
        # Отправляем тестовое уведомление НЕМЕДЛЕННО
        success = FirebaseService.send_notification(
            fcm_token=user.fcm_token,
            title='Тестовое уведомление',
            body='Firebase настроен правильно! ✅',
            data={'type': 'test'}
        )
        
        if success:
            return {"status": "success", "message": "Уведомление отправлено"}
        else:
            raise HTTPException(status_code=500, detail="Не удалось отправить уведомление")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/scheduled-jobs")
async def get_scheduled_jobs():
    """Возвращает список всех запланированных уведомлений"""
    jobs = SchedulerService.get_scheduled_jobs()
    return {
        "count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "name": job.name,
            }
            for job in jobs
        ]
    }
