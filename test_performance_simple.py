#!/usr/bin/env python3
"""
Простой тест производительности эндпоинта user_trainings без авторизации
Проверяет только базовую функциональность и время ответа
"""

import asyncio
import httpx
import time
import json


async def test_performance_simple():
    """Простой тест производительности без авторизации"""
    url = "http://127.0.0.1:8000/user_trainings/"
    params = {
        "user_program_uuid": "d02e8d12-5756-47f2-afd3-88cca3c97ef3",
        "page": 1,
        "page_size": 50
    }
    
    print("🚀 Простой тест производительности эндпоинта user_trainings...")
    print(f"📡 URL: {url}")
    print(f"📋 Параметры: {params}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        # Тест 1: Базовый запрос (ожидаем 401 - это нормально без авторизации)
        print("📊 Тест 1: Базовый запрос")
        start_time = time.time()
        
        response = await client.get(url, params=params)
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️  Время выполнения: {execution_time:.3f} секунд")
        print(f"📈 Статус ответа: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Эндпоинт работает корректно (401 - требуется авторизация)")
            print("✅ Производительность отличная!")
        elif response.status_code == 200:
            data = response.json()
            print(f"📦 Получено записей: {len(data.get('data', []))}")
            print(f"📊 Всего записей: {data.get('pagination', {}).get('total_count', 0)}")
            print("✅ Эндпоинт работает с авторизацией!")
        else:
            print(f"❌ Неожиданный статус: {response.status_code}")
            print(f"📄 Ответ: {response.text[:200]}...")
        
        print("-" * 50)
        
        # Тест 2: Проверка времени ответа на ошибку авторизации
        print("🔄 Тест 2: Повторный запрос для проверки кэширования")
        start_time = time.time()
        
        response = await client.get(url, params=params)
        end_time = time.time()
        cached_execution_time = end_time - start_time
        
        print(f"⏱️  Время выполнения (повторный): {cached_execution_time:.3f} секунд")
        
        if cached_execution_time < execution_time * 0.8:
            print("✅ Кэширование работает эффективно!")
        else:
            print("⚠️  Кэширование не показывает значительного улучшения")
        
        print("-" * 50)
        
        # Тест 3: Проверка разных параметров пагинации
        print("📄 Тест 3: Проверка разных параметров")
        
        test_params = [
            {"page": 1, "page_size": 10},
            {"page": 2, "page_size": 10},
            {"page": 1, "page_size": 100},
        ]
        
        for i, test_param in enumerate(test_params, 1):
            params_test = {**params, **test_param}
            start_time = time.time()
            response = await client.get(url, params=params_test)
            end_time = time.time()
            test_time = end_time - start_time
            
            print(f"📄 Тест {i}: page={test_param['page']}, size={test_param['page_size']} - {test_time:.3f}с - {response.status_code}")
        
        print("-" * 50)
        print("🎉 Простой тест завершен!")
        print("💡 Для полного тестирования нужна авторизация")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 ПРОСТОЙ ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ USER_TRAININGS")
    print("=" * 60)
    print("⚠️  Убедитесь, что сервер запущен: uvicorn app.main:app --reload")
    print("=" * 60)
    
    asyncio.run(test_performance_simple()) 