import asyncio
from app.database import async_session_maker
from app.achievements.dao import AchievementTypeDAO

async def test_achievement_dao():
    async with async_session_maker() as session:
        print("🧪 ТЕСТИРОВАНИЕ DAO ДОСТИЖЕНИЙ")
        print("=" * 50)
        
        try:
            dao = AchievementTypeDAO(session)
            
            print("1. Тестируем find_all()...")
            all_types = await dao.find_all()
            print(f"✅ Найдено типов: {len(all_types)}")
            
            print("\n2. Тестируем find_active()...")
            active_types = await dao.find_active()
            print(f"✅ Найдено активных типов: {len(active_types)}")
            
            print("\n3. Тестируем find_by_category('Праздничные')...")
            holiday_types = await dao.find_by_category('Праздничные')
            print(f"✅ Найдено праздничных типов: {len(holiday_types)}")
            
            print("\n✅ Все тесты прошли успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print(f"Тип ошибки: {type(e).__name__}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_achievement_dao())

