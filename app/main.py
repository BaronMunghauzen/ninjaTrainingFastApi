from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager

# Import models before routers to ensure SQLAlchemy relationships are properly initialized
# Import UserFavoriteExercise BEFORE ExerciseReference to ensure it's registered first
from app.user_favorite_exercises.models import UserFavoriteExercise  # noqa: F401
from app.exercise_reference.models import ExerciseReference  # noqa: F401

from app.users.router import router as router_users
from app.categories.router import router as router_categories
from app.programs.router import router as router_programs
from app.trainings.router import router as router_trainings
from app.exercise_groups.router import router as router_exercise_groups
from app.exercises.router import router as router_exercises
from app.user_program.router import router as router_user_programs
from app.user_training.router import router as router_user_trainings
from app.user_exercises.router import router as router_user_exercises
from app.files.router import router as router_files
from app.exercise_reference.router import router as exercise_reference_router
from app.services.router import router as router_services
from app.achievements.router import router as router_achievements
from app.password_reset.router import router as router_password_reset
from app.user_measurements.router import router as router_user_measurements
from app.subscriptions.router import router as router_subscriptions
from app.promo_codes.router import router as router_promo_codes
from app.notifications.router import router as router_notifications
from app.last_values.router import router as router_last_values
from app.logs.router import router as router_logs
from app.food_recognition.router import router as router_food_recognition
from app.recipes.router import router as router_recipes
from app.calorie_calculator.router import router as router_calorie_calculator
from app.food_progress.router import router as router_food_progress
from app.meal_plans.router import router as router_meal_plans
from app.logger import logger
from pydantic import EmailStr
from app.email_service import email_service
import tracemalloc
from typing import Dict, List
from collections import deque
import time


# Глобальное хранилище для истории использования памяти
_memory_history: deque = deque(maxlen=100)  # Храним последние 100 измерений
_tracemalloc_started = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    """
    global _tracemalloc_started
    
    # Запускаем отслеживание памяти для поиска утечек
    try:
        tracemalloc.start()
        _tracemalloc_started = True
        logger.info("✅ Tracemalloc запущен для отслеживания утечек памяти")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось запустить tracemalloc: {e}")
    
    # Запуск приложения
    from app.background_tasks import start_scheduler
    start_scheduler()
    
    # Инициализация Firebase и Scheduler сервисов
    try:
        from app.services.firebase_service import FirebaseService
        from app.services.scheduler_service import SchedulerService
        
        # Инициализируем Firebase
        try:
            FirebaseService.initialize()
            logger.info("✅ Firebase инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Firebase: {e}")
        
        # Инициализируем Scheduler
        try:
            SchedulerService.initialize()
            logger.info("✅ Scheduler инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Scheduler: {e}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации сервисов: {e}")
    
    yield
    
    # Остановка приложения
    from app.background_tasks import stop_scheduler
    stop_scheduler()
    
    # Останавливаем Scheduler
    try:
        from app.services.scheduler_service import SchedulerService
        SchedulerService.shutdown()
        logger.info("✅ Scheduler остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка остановки Scheduler: {e}")
    
    # Останавливаем tracemalloc
    if _tracemalloc_started:
        try:
            tracemalloc.stop()
            logger.info("✅ Tracemalloc остановлен")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка остановки tracemalloc: {e}")


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_request_data(request: Request, call_next):
    # Проверяем, является ли это файловым запросом
    is_file_upload = any(path in str(request.url) for path in [
        '/upload-image', '/upload-video', '/upload-avatar'
    ])
    
    # Проверяем, является ли это запросом на скачивание файла
    is_file_download = any(path in str(request.url) for path in [
        '/files/file/', '/logs/download'
    ])
    
    if is_file_upload:
        # Для файловых запросов логируем только метаданные (не читаем body в память)
        # Не трогаем запрос вообще - FastAPI сам обработает body для файлов
        logger.info(
            f"Request: {request.method} {request.url}\n"
            f"Headers: {dict(request.headers)}\n"
            f"Body: [FILE UPLOAD - content not logged to save memory]"
        )
        response = await call_next(request)
    elif is_file_download:
        # Для запросов на скачивание файлов логируем только метаданные
        logger.info(
            f"Request: {request.method} {request.url}\n"
            f"Headers: {dict(request.headers)}\n"
            f"Body: [FILE DOWNLOAD - no body to log]"
        )
        response = await call_next(request)
    else:
        # Для остальных запросов читаем body только для логирования
        # Но делаем это безопасно, чтобы не сломать запрос
        try:
            body = await request.body()
            
            # Ограничиваем размер логируемого body (первые 1000 символов)
            body_preview = body.decode(errors='replace')[:1000]
            if len(body) > 1000:
                body_preview += "... [truncated]"
            
            logger.info(
                f"Request: {request.method} {request.url}\n"
                f"Headers: {dict(request.headers)}\n"
                f"Body: {body_preview}"
            )
            
            # Восстанавливаем body для downstream
            async def receive():
                return {"type": "http.request", "body": body}
            request = Request(request.scope, receive)
        except Exception as e:
            # Если не удалось прочитать body, просто логируем без него
            logger.warning(f"Could not read request body: {e}")
        
        response = await call_next(request)
    
    if response.status_code == 403:
        response.delete_cookie("users_access_token")
    
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Кастомный обработчик ошибок валидации"""
    errors = []
    for err in exc.errors():
        if err['type'] == 'missing':
            # Получаем имя поля из локации
            field_name = err['loc'][-1] if err['loc'] else 'unknown'
            errors.append(f"Поле '{field_name}' обязательно для заполнения")
        elif err['type'] == 'value_error' or err['type'] == 'value_error.model':
            # Проверяем, есть ли кастомное сообщение об ошибке
            if 'msg' in err and err['msg'] and not err['msg'].startswith('Value error'):
                errors.append(err['msg'])
            else:
                # Получаем имя поля из локации, пропуская 'body'
                loc = [str(loc) for loc in err['loc'] if loc != 'body']
                field_name = loc[-1] if loc else 'unknown'
                errors.append(f"Некорректное значение для поля '{field_name}'")
        elif err['type'] == 'model':
            # Ошибки валидации модели (например, из @model_validator)
            errors.append(err['msg'])
        else:
            # Для других типов ошибок используем сообщение
            errors.append(err.get('msg', 'Ошибка валидации'))
    
    # Если есть ошибки, возвращаем первую
    detail = errors[0] if errors else "Ошибка валидации данных"
    
    # Универсальное сообщение
    msg = "Ошибка при добавлении объекта" if request.method in ("POST", "PUT") else "Ошибка валидации запроса"
    return JSONResponse(
        status_code=422,
        content={"message": msg, "detail": detail}
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Кастомный обработчик ошибок SQLAlchemy"""
    # Логируем детали ошибки для отладки
    logger.error(f"SQLAlchemy error: {exc}")
    
    # Получаем детали ошибки
    orig = getattr(exc, 'orig', None)
    msg = str(orig) if orig else str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "message": "Database error", 
            "detail": msg,
            "type": "database_error"
        }
    )


@app.get("/")
def home_page():
    return {"message": "Привет!"}


@app.get("/health/memory")
async def memory_health():
    """
    Endpoint для мониторинга использования памяти приложением
    Полезно для диагностики утечек памяти и OOM проблем
    
    ВАЖНО: Если system_memory.percent растет без нагрузки - это признак утечки памяти!
    """
    global _memory_history
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        rss_mb = round(memory_info.rss / 1024 / 1024, 2)
        
        # Получаем информацию о системной памяти
        system_memory = psutil.virtual_memory()
        
        # Сохраняем текущее измерение в историю
        current_time = time.time()
        _memory_history.append({
            "timestamp": current_time,
            "rss_mb": rss_mb,
            "system_percent": round(system_memory.percent, 2)
        })
        
        # Анализируем тренд (рост памяти за последние измерения)
        memory_trend = _analyze_memory_trend()
        
        # Получаем топ-5 процессов по использованию памяти (для диагностики)
        top_processes = []
        try:
            all_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['memory_info']:
                        all_processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'] or 'unknown',
                            'rss_mb': round(pinfo['memory_info'].rss / 1024 / 1024, 2),
                            'percent': round(pinfo['memory_percent'] or 0, 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Сортируем по RSS и берем топ-5
            top_processes = sorted(all_processes, key=lambda x: x['rss_mb'], reverse=True)[:5]
        except Exception as e:
            logger.warning(f"Не удалось получить список процессов: {e}")
        
        # Информация о пуле соединений БД
        db_pool_info = {}
        try:
            from app.database import engine
            pool = engine.pool
            db_pool_info = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "max_overflow": pool._max_overflow
            }
        except Exception as e:
            db_pool_info = {"error": str(e)}
        
        # Вычисляем изменение памяти (если есть кеш)
        memory_change = None
        try:
            # Простая проверка: если доступной памяти стало меньше, это плохо
            if system_memory.percent > 80:
                memory_change = "⚠️ КРИТИЧНО: Использование памяти > 80%"
            elif system_memory.percent > 70:
                memory_change = "⚠️ ВНИМАНИЕ: Использование памяти > 70%"
            elif system_memory.available < 1000 * 1024 * 1024:  # Меньше 1GB доступно
                memory_change = "⚠️ ВНИМАНИЕ: Доступно меньше 1GB памяти"
        except:
            pass
        
        return {
            "process_memory": {
                "rss_mb": rss_mb,  # Resident Set Size в MB
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),  # Virtual Memory Size в MB
                "percent": round(process.memory_percent(), 2)  # Процент от общей памяти системы
            },
            "system_memory": {
                "total_mb": round(system_memory.total / 1024 / 1024, 2),
                "available_mb": round(system_memory.available / 1024 / 1024, 2),
                "used_mb": round(system_memory.used / 1024 / 1024, 2),
                "percent": round(system_memory.percent, 2),
                "warning": memory_change
            },
            "memory_trend": memory_trend,  # Анализ тренда использования памяти
            "top_processes": top_processes,  # Топ-5 процессов по памяти
            "db_pool": db_pool_info,  # Информация о пуле соединений БД
            "status": "ok",
            "recommendations": _get_memory_recommendations(system_memory.percent, rss_mb)
        }
    except ImportError:
        return {
            "status": "error",
            "message": "psutil не установлен. Установите: pip install psutil"
        }
    except Exception as e:
        logger.error(f"Ошибка при получении информации о памяти: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/health/memory/leak-detection")
async def memory_leak_detection():
    """
    Детальный анализ памяти для поиска утечек
    Использует tracemalloc для отслеживания выделения памяти
    """
    global _tracemalloc_started
    
    if not _tracemalloc_started:
        return {
            "status": "error",
            "message": "Tracemalloc не запущен. Перезапустите приложение."
        }
    
    try:
        import psutil
        import os
        import gc
        
        # Получаем текущий снимок памяти
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        # Топ-10 мест по использованию памяти
        top_allocations = []
        for index, stat in enumerate(top_stats[:10], 1):
            top_allocations.append({
                "rank": index,
                "filename": stat.traceback[0].filename if stat.traceback else "unknown",
                "lineno": stat.traceback[0].lineno if stat.traceback else 0,
                "size_mb": round(stat.size / 1024 / 1024, 2),
                "count": stat.count
            })
        
        # Информация о процессах
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        # Собираем мусор для сравнения
        gc.collect()
        
        # Анализ объектов в памяти
        import sys
        object_counts = {}
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            object_counts[obj_type] = object_counts.get(obj_type, 0) + 1
        
        # Топ-10 типов объектов по количеству
        top_object_types = sorted(object_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "status": "ok",
            "current_memory": {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2)
            },
            "top_allocations": top_allocations,  # Топ мест выделения памяти
            "top_object_types": [{"type": k, "count": v} for k, v in top_object_types],
            "gc_stats": {
                "collections": gc.get_stats(),
                "counts": gc.get_count()
            },
            "recommendations": _get_leak_detection_recommendations(top_allocations, memory_info.rss / 1024 / 1024)
        }
    except Exception as e:
        logger.error(f"Ошибка при анализе утечек памяти: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def _analyze_memory_trend() -> Dict:
    """Анализирует тренд использования памяти"""
    global _memory_history
    
    if len(_memory_history) < 2:
        return {
            "status": "insufficient_data",
            "message": "Недостаточно данных для анализа. Проверьте endpoint несколько раз."
        }
    
    # Берем последние 10 измерений
    recent = list(_memory_history)[-10:]
    first = recent[0]
    last = recent[-1]
    
    rss_change = last["rss_mb"] - first["rss_mb"]
    system_change = last["system_percent"] - first["system_percent"]
    
    # Определяем тренд
    if rss_change > 50:  # Рост больше 50MB
        trend = "⚠️ РОСТ: Память процесса растет!"
        severity = "high"
    elif rss_change > 20:  # Рост больше 20MB
        trend = "⚠️ Рост: Память процесса медленно растет"
        severity = "medium"
    elif rss_change < -10:  # Снижение больше 10MB
        trend = "✅ Снижение: Память процесса уменьшается"
        severity = "low"
    else:
        trend = "✅ Стабильно: Память процесса стабильна"
        severity = "low"
    
    return {
        "status": "ok",
        "trend": trend,
        "severity": severity,
        "rss_change_mb": round(rss_change, 2),
        "system_percent_change": round(system_change, 2),
        "measurements_count": len(recent),
        "time_span_seconds": round(last["timestamp"] - first["timestamp"], 2)
    }


def _get_leak_detection_recommendations(top_allocations: List[Dict], current_rss_mb: float) -> List[str]:
    """Генерирует рекомендации на основе анализа утечек"""
    recommendations = []
    
    # Проверяем подозрительные места
    suspicious_files = []
    for alloc in top_allocations:
        if alloc["size_mb"] > 10:  # Больше 10MB в одном месте
            suspicious_files.append(f"{alloc['filename']}:{alloc['lineno']} ({alloc['size_mb']}MB)")
    
    if suspicious_files:
        recommendations.append("🚨 Обнаружены места с большим выделением памяти:")
        recommendations.extend([f"  - {f}" for f in suspicious_files[:5]])
        recommendations.append("Проверьте эти места в коде на утечки памяти")
    
    if current_rss_mb > 1000:
        recommendations.append("⚠️ Приложение использует > 1GB. Проверьте на утечки памяти")
    
    if not recommendations:
        recommendations.append("✅ Подозрительных мест не обнаружено")
        recommendations.append("Продолжайте мониторинг через /health/memory")
    
    return recommendations


def _get_memory_recommendations(system_percent: float, process_rss_mb: float) -> list[str]:
    """Генерирует рекомендации на основе использования памяти"""
    recommendations = []
    
    if system_percent > 90:
        recommendations.append("🚨 КРИТИЧНО: Системная память > 90%. Риск OOM killer!")
        recommendations.append("Рекомендация: Перезапустите приложение или найдите процессы-пожиратели памяти")
    elif system_percent > 80:
        recommendations.append("⚠️ ВНИМАНИЕ: Системная память > 80%. Следите за ростом!")
        recommendations.append("Рекомендация: Проверьте топ процессов и освободите память")
    elif system_percent > 70:
        recommendations.append("ℹ️ Системная память > 70%. Нормально, но следите за трендом")
    
    if process_rss_mb > 1500:
        recommendations.append("🚨 КРИТИЧНО: Приложение использует > 1.5GB. Возможна утечка памяти!")
    elif process_rss_mb > 1000:
        recommendations.append("⚠️ ВНИМАНИЕ: Приложение использует > 1GB. Проверьте на утечки")
    elif process_rss_mb > 500:
        recommendations.append("ℹ️ Приложение использует > 500MB. Это нормально для Python приложений")
    
    if not recommendations:
        recommendations.append("✅ Использование памяти в норме")
    
    return recommendations


@app.get("/feedback", response_class=FileResponse)
def feedback_page():
    return FileResponse("static/feedback.html")


@app.post("/feedback")
async def submit_feedback(email: EmailStr = Form(...), message: str = Form("")):
    try:
        await email_service.send_support_request(
            user_email=str(email),
            user_name="Anonymous",
            request_type="App feedback",
            message=message or "(пустое сообщение)"
        )
        return RedirectResponse(url="/static/feedback-success.html", status_code=303)
    except Exception as e:
        logger.error(f"Ошибка отправки feedback: {e}")
        return JSONResponse(status_code=500, content={"detail": "Не удалось отправить сообщение. Попробуйте позже."})


app.include_router(router_users)
app.include_router(router_categories)
app.include_router(router_programs)
app.include_router(router_trainings)
app.include_router(router_exercise_groups)
app.include_router(router_exercises)
app.include_router(router_user_programs)
app.include_router(router_user_trainings)
app.include_router(router_user_exercises)
app.include_router(router_files)
app.include_router(exercise_reference_router)
app.include_router(router_services)
app.include_router(router_achievements)
app.include_router(router_password_reset)
app.include_router(router_user_measurements)
app.include_router(router_subscriptions)
app.include_router(router_promo_codes)
app.include_router(router_notifications)
app.include_router(router_last_values)
app.include_router(router_logs)
app.include_router(router_food_recognition)
app.include_router(router_recipes)
app.include_router(router_calorie_calculator)
app.include_router(router_food_progress)
app.include_router(router_meal_plans)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")