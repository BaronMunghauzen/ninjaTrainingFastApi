# 📝 Руководство по логированию

## Обзор

В проекте настроена система логирования с автоматической ротацией файлов по дням. Логи сохраняются в папку `logs/`.

## Возможности

✅ **Автоматическая ротация** - новый файл создается каждый день в полночь  
✅ **Архивация старых логов** - старые логи автоматически архивируются в `.zip`  
✅ **Разделение по уровням** - отдельные файлы для общих логов и ошибок  
✅ **Цветной вывод в консоль** - удобно для разработки  
✅ **Асинхронная запись** - не блокирует основной поток  
✅ **Безопасность для многопоточности** - можно использовать в async коде  

## Структура логов

```
logs/
├── app_2025-01-10.log          # Все логи за 10 января 2025
├── app_2025-01-11.log          # Все логи за 11 января 2025
├── app_2025-01-09.log.zip      # Архив старых логов
├── errors_2025-01-10.log       # Только ошибки за 10 января
└── errors_2025-01-11.log       # Только ошибки за 11 января
```

## Настройки хранения

- **Обычные логи (INFO+)**: хранятся **30 дней**, затем удаляются
- **Логи ошибок (ERROR+)**: хранятся **90 дней**, затем удаляются
- Логи старше 1 дня автоматически архивируются в `.zip`

## Использование

### Вариант 1: С библиотекой loguru (рекомендуется) ⭐

```python
from app.logger import logger

# Информационное сообщение
logger.info("Пользователь вошел в систему")

# Предупреждение
logger.warning("Попытка доступа к несуществующему ресурсу")

# Ошибка
logger.error("Не удалось подключиться к базе данных")

# Критическая ошибка
logger.critical("Система остановлена")

# Отладочное сообщение (не попадает в файлы, только в консоль при DEBUG режиме)
logger.debug(f"Параметры запроса: {params}")

# Логирование с контекстом
logger.info(f"Создано упражнение: {exercise.caption}")

# Логирование исключений с полным traceback
try:
    result = dangerous_operation()
except Exception as e:
    logger.exception("Ошибка при выполнении операции")
    # Или так:
    logger.error(f"Ошибка: {e}")
```

### Вариант 2: Со встроенным logging (без дополнительных зависимостей)

Если не хотите устанавливать `loguru`, используйте `logger_standard.py`:

1. В `app/main.py` измените импорт:
```python
# Вместо
from app.logger import logger

# Используйте
from app.logger_standard import logger
```

2. Использование аналогично:
```python
from app.logger_standard import logger

logger.info("Информационное сообщение")
logger.error("Ошибка")
logger.warning("Предупреждение")
```

## Примеры из проекта

### В роутерах

```python
from app.logger import logger

@router.post('/add/')
async def add_exercise(exercise: SExerciseAdd):
    logger.info(f"Добавление нового упражнения: {exercise.caption}")
    try:
        result = await ExerciseDAO.add(**exercise.dict())
        logger.info(f"Упражнение успешно добавлено, UUID: {result.uuid}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при добавлении упражнения: {e}")
        raise
```

### В сервисах

```python
from app.logger import logger

class PaymentService:
    async def process_payment(self, amount: float, user_id: int):
        logger.info(f"Обработка платежа: {amount} руб. для пользователя {user_id}")
        
        try:
            result = await self._charge(amount)
            logger.info(f"Платеж успешен: transaction_id={result.id}")
            return result
        except PaymentError as e:
            logger.error(f"Ошибка платежа для пользователя {user_id}: {e}")
            raise
```

### В middleware

```python
from app.logger import logger

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Запрос: {request.method} {request.url.path}")
    
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    logger.info(
        f"Ответ: {response.status_code} | "
        f"Время: {duration:.3f}s | "
        f"Путь: {request.url.path}"
    )
    
    return response
```

### Логирование с дополнительным контекстом

```python
from app.logger import logger

# Добавление контекста к логам
logger.bind(user_id=user.id).info("Пользователь обновил профиль")

# С несколькими полями
logger.bind(
    user_id=user.id,
    action="update_profile",
    ip=request.client.host
).info("Обновление профиля")
```

## Уровни логирования

| Уровень | Когда использовать | Куда попадает |
|---------|-------------------|---------------|
| `DEBUG` | Отладочная информация | Только консоль (при DEBUG=True) |
| `INFO` | Обычные операции | Консоль + `app_*.log` |
| `WARNING` | Предупреждения | Консоль + `app_*.log` |
| `ERROR` | Ошибки | Консоль + `app_*.log` + `errors_*.log` |
| `CRITICAL` | Критические ошибки | Консоль + `app_*.log` + `errors_*.log` |

## Установка

### Для варианта с loguru (рекомендуется):

```bash
pip install -r req.txt
```

Библиотека `loguru` уже добавлена в `req.txt`.

### Для варианта со стандартным logging:

Ничего устанавливать не нужно - используется встроенный модуль Python.

## Настройка

Все настройки находятся в `app/logger.py`:

```python
# Изменить период хранения логов
retention="30 days",  # Измените на нужное значение

# Изменить время ротации
rotation="00:00",  # Полночь, можно "500 MB" для ротации по размеру

# Изменить уровень логирования
level="INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Отключить архивацию
compression=None,  # Вместо "zip"
```

## Мониторинг логов

### Просмотр последних логов:
```bash
# Windows PowerShell
Get-Content logs\app_2025-01-11.log -Tail 50

# Linux/Mac
tail -f logs/app_2025-01-11.log
```

### Поиск ошибок:
```bash
# Windows PowerShell
Select-String "ERROR" logs\app_*.log

# Linux/Mac
grep "ERROR" logs/app_*.log
```

### Просмотр логов за конкретную дату:
```bash
cat logs/app_2025-01-10.log
```

## Best Practices

1. **Используйте правильный уровень** - не пишите все в ERROR
2. **Добавляйте контекст** - укажите ID пользователя, UUID объекта и т.д.
3. **Не логируйте чувствительные данные** - пароли, токены, личную информацию
4. **Используйте f-strings для форматирования** - удобнее и быстрее
5. **Логируйте важные события** - создание/изменение/удаление данных
6. **Для исключений используйте logger.exception()** - автоматически добавит traceback

## Примеры плохих и хороших логов

❌ **Плохо:**
```python
logger.info("Error")  # Неинформативно
logger.error("User")  # Что с пользователем?
logger.info(f"Password: {password}")  # Секретные данные!
```

✅ **Хорошо:**
```python
logger.error(f"Не удалось обновить пользователя {user_id}: объект не найден")
logger.info(f"Пользователь {user.email} успешно аутентифицирован")
logger.warning(f"Подписка {subscription_id} истекает через 3 дня")
```

## Troubleshooting

### Логи не создаются
- Проверьте, существует ли папка `logs/`
- Проверьте права на запись в папку

### Слишком большие файлы логов
- Уменьшите период хранения в `retention`
- Добавьте ротацию по размеру: `rotation="100 MB"`

### Логи не ротируются
- Убедитесь, что приложение работает во время ротации (полночь)
- Проверьте системное время сервера

## Дополнительная информация

- [Документация loguru](https://loguru.readthedocs.io/)
- [Документация logging (Python)](https://docs.python.org/3/library/logging.html)

