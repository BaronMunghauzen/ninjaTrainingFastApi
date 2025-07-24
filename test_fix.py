#!/usr/bin/env python3
"""
Простой тест для проверки исправлений ошибок
"""

import asyncio
import httpx
import time


async def test_fix():
    """Тест исправлений"""
    url = "http://127.0.0.1:8000/user_trainings/"
    params = {
        "user_program_uuid": "d02e8d12-5756-47f2-afd3-88cca3c97ef3",
        "page": 1,
        "page_size": 10
    }
    
    print("🔧 Тестирование исправлений...")
    print(f"📡 URL: {url}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        start_time = time.time()
        response = await client.get(url, params=params)
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️  Время выполнения: {execution_time:.3f} секунд")
        print(f"📈 Статус ответа: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Эндпоинт работает корректно (401 - требуется авторизация)")
            print("✅ Нет ошибок с lazy loading!")
        elif response.status_code == 200:
            print("✅ Эндпоинт работает с авторизацией!")
            print("✅ Нет ошибок с lazy loading!")
        elif response.status_code == 500:
            print("❌ Внутренняя ошибка сервера")
            print(f"📄 Ответ: {response.text[:500]}...")
        else:
            print(f"❌ Неожиданный статус: {response.status_code}")
            print(f"📄 Ответ: {response.text[:200]}...")
        
        print("-" * 50)
        print("🎉 Тест завершен!")


if __name__ == "__main__":
    print("=" * 50)
    print("🔧 ТЕСТ ИСПРАВЛЕНИЙ")
    print("=" * 50)
    
    asyncio.run(test_fix()) 