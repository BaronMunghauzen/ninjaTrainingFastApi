import asyncio
from app.database import async_session_maker, get_async_session
from app.achievements.models import AchievementType
from sqlalchemy import select

async def test_database_connection():
    print("🔌 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ")
    print("=" * 60)
    
    try:
        print("1. Проверяем подключение...")
        async with async_session_maker() as session:
            print("✅ Сессия создана успешно")
            
            print("\n2. Тестируем простой запрос...")
            result = await session.execute(select(AchievementType).limit(1))
            achievement_type = result.scalar_one_or_none()
            
            if achievement_type:
                print(f"✅ Запрос выполнен успешно: {achievement_type.name}")
            else:
                print("⚠️  Запрос выполнен, но данных нет")
        
        print("\n3. Тестируем dependency...")
        async for session in get_async_session():
            print("✅ Dependency работает")
            break
        
        print("\n✅ Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print(f"Тип ошибки: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_connection())

