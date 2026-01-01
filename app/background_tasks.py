"""
Фоновые задачи приложения
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.subscriptions.service import SubscriptionService
from app.logger import logger

# Глобальный планировщик
scheduler = None


def clear_linecache():
    """
    Очистка linecache для предотвращения утечки памяти
    linecache используется для хранения traceback'ов и может накапливаться
    """
    try:
        import linecache
        linecache.clearcache()
        logger.debug("✓ linecache очищен для предотвращения утечки памяти")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось очистить linecache: {e}")


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
    
    # Задача 2: Очистка linecache каждые 6 часов для предотвращения утечки памяти
    # linecache используется для хранения traceback'ов и может накапливаться со временем
    scheduler.add_job(
        clear_linecache,
        IntervalTrigger(hours=6),
        id='clear_linecache',
        name='Очистка linecache',
        replace_existing=True
    )
    
    logger.info("Запланированные задачи:")
    logger.info("- Проверка истекших подписок: каждый день в 01:00")
    logger.info("- Очистка linecache: каждые 6 часов (предотвращение утечки памяти)")
    
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
