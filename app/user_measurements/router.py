from fastapi import APIRouter

from app.user_measurements.measurement_types_router import router as measurement_types_router
from app.user_measurements.measurements_router import router as measurements_router

# Создаем основной роутер
router = APIRouter()

# Подключаем подроутеры
router.include_router(measurement_types_router)
router.include_router(measurements_router)
