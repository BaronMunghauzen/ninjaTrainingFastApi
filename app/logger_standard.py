"""
Настройка логирования для приложения (стандартный logging)
Использует встроенный модуль logging с ротацией файлов по дням
"""
import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

# Создаем директорию для логов, если её нет
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Формат логов
log_format = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Создаем основной logger
logger = logging.getLogger("ninjaTraining")
logger.setLevel(logging.INFO)
logger.propagate = False  # Не передавать в root logger

# Очищаем существующие обработчики, если есть
if logger.handlers:
    logger.handlers.clear()

# 1. Консольный вывод
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# 2. Файл с ротацией по дням (все логи INFO и выше)
file_handler = TimedRotatingFileHandler(
    filename="logs/app.log",
    when="midnight",  # Ротация в полночь
    interval=1,  # Каждый день
    backupCount=30,  # Хранить 30 дней
    encoding="utf-8",
    utc=False  # Использовать локальное время
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_format)
# Добавляем суффикс к имени файла с датой
file_handler.suffix = "%Y-%m-%d"
logger.addHandler(file_handler)

# 3. Отдельный файл для ошибок (ERROR и CRITICAL)
error_handler = TimedRotatingFileHandler(
    filename="logs/errors.log",
    when="midnight",
    interval=1,
    backupCount=90,  # Хранить ошибки 90 дней
    encoding="utf-8",
    utc=False
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_format)
error_handler.suffix = "%Y-%m-%d"
logger.addHandler(error_handler)

# Функция для получения logger
def get_logger(name: str = None):
    """
    Получить logger для модуля
    
    Args:
        name: Имя модуля (обычно __name__)
    
    Returns:
        logging.Logger: Настроенный logger
    """
    if name:
        return logger.getChild(name)
    return logger

__all__ = ["logger", "get_logger"]

