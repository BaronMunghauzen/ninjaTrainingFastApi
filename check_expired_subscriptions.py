"""
Скрипт для проверки и деактивации истекших подписок
Запускается по расписанию (cron)
"""

import asyncio
import logging
from app.subscriptions.service import SubscriptionService

logging.basicConfig(level=logging.INFO)

async def main():
    """Проверка истекших подписок"""
    print("Запуск проверки истекших подписок...")
    
    try:
        expired_count = await SubscriptionService.check_and_update_expired_subscriptions()
        print(f"Готово! Деактивировано подписок: {expired_count}")
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
