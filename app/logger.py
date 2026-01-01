"""
Настройка логирования для приложения
Использует loguru для удобного и гибкого логирования с ротацией файлов
"""
import sys
from pathlib import Path
from loguru import logger

# Создаем директорию для логов, если её нет
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Удаляем стандартный обработчик loguru
logger.remove()

# Добавляем вывод в консоль (только для разработки, уровень DEBUG)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Добавляем логирование в файл с ротацией по дням (INFO и выше)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    rotation="00:00",  # Новый файл каждый день в полночь
    retention="30 days",  # Хранить логи 30 дней
    compression="zip",  # Архивировать старые логи
    encoding="utf-8",
    enqueue=True,  # Асинхронная запись (безопасно для многопоточности)
)

# Добавляем отдельный файл для ошибок (ERROR и CRITICAL)
# Ограничиваем глубину traceback для предотвращения накопления в linecache
logger.add(
    "logs/errors_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="00:00",  # Новый файл каждый день в полночь
    retention="90 days",  # Хранить логи ошибок 90 дней
    compression="zip",
    encoding="utf-8",
    enqueue=True,
    backtrace=True,  # Показывать полный traceback
    diagnose=False,  # Отключаем детальную диагностику для экономии памяти (предотвращает накопление в linecache)
)

# Экспортируем logger для использования в других модулях
__all__ = ["logger"]

