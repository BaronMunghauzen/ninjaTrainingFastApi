# 🚀 Быстрый старт: Логирование

## Установка

```bash
pip install loguru
```

## Использование (3 простых шага)

### 1️⃣ Импортируйте logger

```python
from app.logger import logger
```

### 2️⃣ Используйте в коде

```python
# Информация
logger.info("Пользователь вошел в систему")

# Ошибка
logger.error("Не удалось сохранить данные")

# Исключение с traceback
try:
    result = risky_operation()
except Exception as e:
    logger.exception("Ошибка при выполнении операции")
```

### 3️⃣ Готово! 

Логи автоматически сохраняются в `logs/`:
- `logs/app_2025-01-11.log` - все логи
- `logs/errors_2025-01-11.log` - только ошибки

## Что происходит автоматически

✅ Новый файл создается каждый день  
✅ Старые логи архивируются в `.zip`  
✅ Логи старше 30 дней удаляются  
✅ Ошибки хранятся 90 дней  

## Примеры

**В роутерах:**
```python
from app.logger import logger

@router.post('/exercises/add')
async def add_exercise(exercise: SExerciseAdd, user = Depends(get_current_user)):
    logger.info(f"Добавление упражнения '{exercise.caption}' пользователем {user.email}")
    
    try:
        result = await ExerciseDAO.add(**exercise.dict())
        logger.info(f"✓ Упражнение добавлено: UUID={result.uuid}")
        return result
    except Exception as e:
        logger.error(f"✗ Ошибка добавления упражнения: {e}")
        raise
```

**В сервисах:**
```python
from app.logger import logger

async def send_email(to: str, subject: str):
    logger.info(f"Отправка email на {to}: {subject}")
    
    try:
        await email_service.send(to, subject)
        logger.info("✓ Email отправлен")
    except SMTPException as e:
        logger.error(f"✗ Ошибка отправки email: {e}")
        raise
```

## Уровни

```python
logger.debug("Отладка")       # Только в консоль
logger.info("Информация")     # В файл и консоль
logger.warning("Предупреждение")  # В файл и консоль
logger.error("Ошибка")        # В файл ошибок тоже
logger.critical("Критично!")  # В файл ошибок тоже
```

## Просмотр логов

**Последние 50 строк:**
```bash
# PowerShell (Windows)
Get-Content logs\app_2025-01-11.log -Tail 50

# Bash (Linux/Mac)
tail -f logs/app_2025-01-11.log
```

**Поиск ошибок:**
```bash
# PowerShell
Select-String "ERROR" logs\*.log

# Bash
grep "ERROR" logs/*.log
```

---

📖 **Полная документация:** см. `LOGGING_GUIDE.md`

