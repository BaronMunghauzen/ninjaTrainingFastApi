"""
Тестовый скрипт для проверки работы логирования
Запустите: python test_logging.py
"""

from app.logger import logger

def test_logging():
    """Тест различных уровней логирования"""
    
    print("🧪 Тестирование системы логирования...\n")
    
    # DEBUG - только в консоль
    logger.debug("Это отладочное сообщение (только в консоль)")
    
    # INFO - в файл и консоль
    logger.info("✓ Информационное сообщение (файл + консоль)")
    
    # WARNING - в файл и консоль
    logger.warning("⚠ Предупреждение (файл + консоль)")
    
    # ERROR - в файл ошибок тоже
    logger.error("✗ Сообщение об ошибке (файл + файл ошибок + консоль)")
    
    # Тест логирования с контекстом
    user_id = 12345
    action = "создание упражнения"
    logger.info(f"Пользователь {user_id} выполнил действие: {action}")
    
    # Тест логирования исключения
    try:
        result = 10 / 0
    except Exception as e:
        logger.exception("Поймано исключение (с полным traceback)")
    
    print("\n✅ Тестирование завершено!")
    print(f"📁 Проверьте логи в папке 'logs/'")
    print(f"   - app_*.log - все логи")
    print(f"   - errors_*.log - только ошибки")

if __name__ == "__main__":
    test_logging()

