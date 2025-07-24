import pytest
import time
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_user_trainings_performance():
    """Тест производительности эндпоинта user_trainings"""
    async with AsyncClient(base_url="http://test") as ac:
        # Тестируем запрос с user_program_uuid
        start_time = time.time()
        
        response = await ac.get(
            "/user_trainings/",
            params={
                "user_program_uuid": "d02e8d12-5756-47f2-afd3-88cca3c97ef3",
                "page": 1,
                "page_size": 50
            }
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Проверяем, что запрос выполнился успешно
        assert response.status_code == 200
        
        # Проверяем, что время выполнения приемлемое (менее 2 секунд)
        assert execution_time < 2.0, f"Запрос выполнился за {execution_time:.2f} секунд, что слишком долго"
        
        # Проверяем структуру ответа
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert "total_count" in data["pagination"]
        assert "page" in data["pagination"]
        assert "page_size" in data["pagination"]
        
        print(f"✅ Запрос выполнился за {execution_time:.2f} секунд")
        print(f"📊 Получено {len(data['data'])} записей из {data['pagination']['total_count']} всего")


@pytest.mark.asyncio
async def test_user_trainings_pagination():
    """Тест пагинации"""
    async with AsyncClient(base_url="http://test") as ac:
        # Тестируем первую страницу
        response1 = await ac.get(
            "/user_trainings/",
            params={
                "user_program_uuid": "d02e8d12-5756-47f2-afd3-88cca3c97ef3",
                "page": 1,
                "page_size": 10
            }
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Тестируем вторую страницу
        response2 = await ac.get(
            "/user_trainings/",
            params={
                "user_program_uuid": "d02e8d12-5756-47f2-afd3-88cca3c97ef3",
                "page": 2,
                "page_size": 10
            }
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Проверяем, что данные на разных страницах разные
        if data1["data"] and data2["data"]:
            assert data1["data"][0]["uuid"] != data2["data"][0]["uuid"]
        
        # Проверяем пагинацию
        assert data1["pagination"]["page"] == 1
        assert data2["pagination"]["page"] == 2
        assert data1["pagination"]["page_size"] == 10
        assert data2["pagination"]["page_size"] == 10
        assert data1["pagination"]["total_count"] == data2["pagination"]["total_count"] 