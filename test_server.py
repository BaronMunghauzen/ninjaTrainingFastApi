import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.achievements.dao import AchievementTypeDAO
from app.achievements.schemas import AchievementTypeDisplay
from typing import List

# Создаем тестовое приложение
app = FastAPI()

@app.get("/")
def home():
    return {"message": "Тестовый сервер работает!"}

@app.get("/achievements/types", response_model=List[AchievementTypeDisplay])
async def get_achievement_types(
    session: AsyncSession = Depends(get_async_session)
):
    """Получить все типы достижений"""
    try:
        achievement_type_dao = AchievementTypeDAO(session)
        active_types = await achievement_type_dao.find_active()
        return active_types
    except Exception as e:
        print(f"Ошибка в API: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    print("🚀 Запуск тестового сервера...")
    print("📡 API будет доступен на http://localhost:8000")
    print("🎯 Тестовый эндпоинт: http://localhost:8000/achievements/types")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

