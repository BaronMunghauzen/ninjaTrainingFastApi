from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    _scheduler = None
    
    @classmethod
    def initialize(cls):
        """Инициализация scheduler"""
        if cls._scheduler is None:
            cls._scheduler = BackgroundScheduler()
            cls._scheduler.start()
            logger.info("✅ APScheduler запущен")
    
    @classmethod
    def schedule_timer_notification(
        cls,
        job_id: str,
        scheduled_time: datetime,
        fcm_token: str,
        exercise_name: str,
    ):
        """
        Планирует отправку уведомления о завершении таймера
        
        Args:
            job_id: Уникальный ID задачи (например, user_uuid + timestamp)
            scheduled_time: Когда отправить уведомление
            fcm_token: FCM токен устройства
            exercise_name: Название упражнения
        """
        if cls._scheduler is None:
            cls.initialize()
        
        from .firebase_service import FirebaseService
        
        try:
            # Удаляем старую задачу если она есть
            cls.cancel_job(job_id)
            
            # Планируем новую задачу
            cls._scheduler.add_job(
                func=FirebaseService.send_notification,
                trigger=DateTrigger(run_date=scheduled_time),
                id=job_id,
                args=[
                    fcm_token,
                    'Время отдыха закончилось! ⏰',
                    f'Можете приступать к следующему подходу: {exercise_name}',
                    {'type': 'timer_end', 'exercise': exercise_name}
                ],
                replace_existing=True,
                misfire_grace_time=30,  # Если задержка до 30 сек - все равно выполнить
            )
            
            logger.info(f"✅ Задача запланирована: {job_id} на {scheduled_time}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка планирования задачи: {e}")
            raise
    
    @classmethod
    def cancel_job(cls, job_id: str):
        """Отменяет запланированную задачу"""
        if cls._scheduler is None:
            return
        
        try:
            cls._scheduler.remove_job(job_id)
            logger.info(f"✅ Задача отменена: {job_id}")
        except Exception:
            pass  # Задачи может не быть - это ОК

    @classmethod
    def get_scheduled_jobs(cls):
        """Возвращает список всех запланированных задач"""
        if cls._scheduler is None:
            return []
        return cls._scheduler.get_jobs()
    
    @classmethod
    def shutdown(cls):
        """Останавливает scheduler"""
        if cls._scheduler is not None:
            cls._scheduler.shutdown()
            cls._scheduler = None
            logger.info("✅ APScheduler остановлен")
