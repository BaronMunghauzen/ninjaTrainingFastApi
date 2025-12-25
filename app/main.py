from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
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
from app.notifications.router import router as router_notifications
from app.last_values.router import router as router_last_values
from app.logger import logger
from pydantic import EmailStr
from app.email_service import email_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    """
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


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_request_data(request: Request, call_next):
    body = await request.body()
    
    # Проверяем, является ли это файловым запросом
    is_file_upload = any(path in str(request.url) for path in [
        '/upload-image', '/upload-video', '/upload-avatar'
    ])
    
    if is_file_upload:
        # Для файловых запросов логируем только метаданные
        logger.info(
            f"Request: {request.method} {request.url}\n"
            f"Headers: {dict(request.headers)}\n"
            f"Body: [FILE UPLOAD - content not logged]"
        )
    else:
        # Для остальных запросов логируем полное тело
        logger.info(
            f"Request: {request.method} {request.url}\n"
            f"Headers: {dict(request.headers)}\n"
            f"Body: {body.decode(errors='replace')}"
        )
    
    # Восстанавливаем body для downstream
    async def receive():
        return {"type": "http.request", "body": body}
    request = Request(request.scope, receive)
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
        elif err['type'] == 'value_error':
            errors.append(f"Некорректное значение для поля '{err['loc'][-1]}'")
        else:
            errors.append(err['msg'])
    
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
app.include_router(router_notifications)
app.include_router(router_last_values)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")