#!/usr/bin/env python3
"""
Скрипт для тестирования производительности эндпоинта user_trainings
Запускать после запуска сервера: uvicorn app.main:app --reload
"""

import asyncio
import httpx
import time
import json


async def test_performance():
    """Тест производительности эндпоинта user_trainings"""
    url = "http://127.0.0.1:8000/user_trainings/"
    params = {
        "user_program_uuid": "d02e8d12-5756-47f2-afd3-88cca3c97ef3",
        "page": 1,
        "page_size": 50
    }
    
    print("🚀 Тестирование производительности эндпоинта user_trainings...")
    print(f"📡 URL: {url}")
    print(f"📋 Параметры: {params}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        # Тест 1: Базовый запрос
        print("📊 Тест 1: Базовый запрос")
        start_time = time.time()
        
        response = await client.get(url, params=params)
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️  Время выполнения: {execution_time:.2f} секунд")
        print(f"📈 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📦 Получено записей: {len(data.get('data', []))}")
            print(f"📊 Всего записей: {data.get('pagination', {}).get('total_count', 0)}")
            
            if execution_time < 2.0:
                print("✅ Производительность отличная!")
            elif execution_time < 5.0:
                print("⚠️  Производительность приемлемая")
            else:
                print("❌ Производительность требует улучшения")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"📄 Ответ: {response.text[:200]}...")
        
        print("-" * 50)
        
        # Тест 2: Тест кэширования (повторный запрос)
        print("🔄 Тест 2: Проверка кэширования")
        start_time = time.time()
        
        response = await client.get(url, params=params)
        end_time = time.time()
        cached_execution_time = end_time - start_time
        
        print(f"⏱️  Время выполнения (кэш): {cached_execution_time:.2f} секунд")
        
        if cached_execution_time < execution_time * 0.8:
            print("✅ Кэширование работает эффективно!")
        else:
            print("⚠️  Кэширование не показывает значительного улучшения")
        
        print("-" * 50)
        
        # Тест 3: Тест пагинации
        print("📄 Тест 3: Проверка пагинации")
        
        # Первая страница
        params_page1 = {**params, "page": 1, "page_size": 10}
        response = await client.get(url, params=params_page1)
        if response.status_code == 200:
            data1 = response.json()
            print(f"📄 Страница 1: {len(data1.get('data', []))} записей")
            
            # Вторая страница
            params_page2 = {**params, "page": 2, "page_size": 10}
            response2 = await client.get(url, params=params_page2)
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"📄 Страница 2: {len(data2.get('data', []))} записей")
                
                if data1.get('data') and data2.get('data'):
                    if data1['data'][0]['uuid'] != data2['data'][0]['uuid']:
                        print("✅ Пагинация работает корректно!")
                    else:
                        print("❌ Пагинация работает некорректно")
                else:
                    print("⚠️  Недостаточно данных для проверки пагинации")
            else:
                print(f"❌ Ошибка при получении страницы 2: {response2.status_code}")
        else:
            print(f"❌ Ошибка при получении страницы 1: {response.status_code}")
        
        print("-" * 50)
        print("🎉 Тестирование завершено!")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ ПРОИЗВОДИТЕЛЬНОСТИ USER_TRAININGS")
    print("=" * 60)
    print("⚠️  Убедитесь, что сервер запущен: uvicorn app.main:app --reload")
    print("=" * 60)
    
    asyncio.run(test_performance()) 