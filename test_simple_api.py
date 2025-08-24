import asyncio
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.achievements.dao import AchievementTypeDAO
from app.achievements.schemas import AchievementTypeDisplay
from typing import List

# Создаем простое FastAPI приложение
app = FastAPI()

@app.get("/test/achievements/types", response_model=List[AchievementTypeDisplay])
async def test_get_achievement_types(
    session: AsyncSession = Depends(get_async_session)
):
    """Тестовый эндпоинт для получения типов достижений"""
    try:
        achievement_type_dao = AchievementTypeDAO(session)
        active_types = await achievement_type_dao.find_active()
        return active_types
    except Exception as e:
        print(f"Ошибка в тестовом API: {e}")
        raise

# Тестируем API
async def test_api():
    print("🧪 ТЕСТИРОВАНИЕ ПРОСТОГО API")
    print("=" * 50)
    
    try:
        with TestClient(app) as client:
            print("1. Тестируем эндпоинт...")
            response = client.get("/test/achievements/types")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API работает! Получено {len(data)} типов достижений")
                
                if data:
                    print(f"   Первый тип: {data[0]['name']}")
            else:
                print(f"❌ API вернул ошибку: {response.status_code}")
                print(f"   Ответ: {response.text}")
        
        print("\n✅ Тест завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api())

