import asyncio
from app.database import async_session_maker
from app.achievements.models import AchievementType
from app.achievements.schemas import AchievementTypeDisplay
from sqlalchemy import select

async def test_simple_router():
    async with async_session_maker() as session:
        print("🧪 ТЕСТИРОВАНИЕ ПРОСТОГО РОУТЕРА")
        print("=" * 50)
        
        try:
            # Получаем все типы достижений
            result = await session.execute(select(AchievementType))
            achievement_types = result.scalars().all()
            
            print(f"📊 Найдено типов: {len(achievement_types)}")
            
            # Пробуем преобразовать в схему
            print("\n🔄 Преобразование в схему...")
            for i, at in enumerate(achievement_types[:3]):  # Только первые 3
                try:
                    # Создаем схему напрямую
                    display = AchievementTypeDisplay.model_validate(at)
                    print(f"✅ {i+1}. {display.name} - успешно")
                except Exception as e:
                    print(f"❌ {i+1}. {at.name} - ошибка: {e}")
                    break
            
            print("\n✅ Тест завершен!")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_router())

