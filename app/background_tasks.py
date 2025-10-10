"""
Фоновые задачи приложения
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.subscriptions.service import SubscriptionService
from app.logger import logger

# Глобальный планировщик
scheduler = None


def start_scheduler():
    """
    Запуск планировщика фоновых задач
    
    Вызывается при старте приложения
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Планировщик уже запущен")
        return
    
    scheduler = AsyncIOScheduler()
    
    # Задача 1: Проверка истекших подписок каждый день в 01:00
    scheduler.add_job(
        SubscriptionService.check_and_update_expired_subscriptions,
        CronTrigger(hour=1, minute=0),
        id='check_expired_subscriptions',
        name='Проверка истекших подписок',
        replace_existing=True
    )
    
    logger.info("Запланированные задачи:")
    logger.info("- Проверка истекших подписок: каждый день в 01:00")
    
    # Запускаем планировщик
    scheduler.start()
    logger.info("✓ Планировщик фоновых задач запущен")


def stop_scheduler():
    """
    Остановка планировщика при выключении приложения
    """
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        logger.info("✓ Планировщик фоновых задач остановлен")
        scheduler = None
