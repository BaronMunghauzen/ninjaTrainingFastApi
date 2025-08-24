import asyncio
from app.database import async_session_maker
from app.achievements.dao import AchievementTypeDAO
from app.achievements.schemas import AchievementTypeDisplay
from typing import List

async def test_router_logic():
    async with async_session_maker() as session:
        print("🧪 ТЕСТИРОВАНИЕ ЛОГИКИ РОУТЕРА")
        print("=" * 50)
        
        try:
            # Имитируем логику роутера
            achievement_type_dao = AchievementTypeDAO(session)
            
            print("1. Тестируем find_active()...")
            active_types = await achievement_type_dao.find_active()
            print(f"✅ Найдено активных типов: {len(active_types)}")
            
            print("\n2. Преобразуем в схему...")
            display_types: List[AchievementTypeDisplay] = []
            
            for i, at in enumerate(active_types[:5]):  # Только первые 5
                try:
                    display = AchievementTypeDisplay.model_validate(at)
                    display_types.append(display)
                    print(f"✅ {i+1}. {display.name} - успешно")
                except Exception as e:
                    print(f"❌ {i+1}. {at.name} - ошибка: {e}")
                    break
            
            print(f"\n📊 Успешно преобразовано: {len(display_types)} из 5")
            
            if display_types:
                print("\n3. Тестируем сериализацию...")
                try:
                    # Пробуем сериализовать в JSON
                    import json
                    from pydantic import TypeAdapter
                    
                    adapter = TypeAdapter(List[AchievementTypeDisplay])
                    json_data = adapter.dump_python(display_types)
                    print(f"✅ JSON сериализация успешна, размер: {len(str(json_data))} символов")
                    
                except Exception as e:
                    print(f"❌ Ошибка сериализации: {e}")
            
            print("\n✅ Тест завершен!")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_router_logic())

