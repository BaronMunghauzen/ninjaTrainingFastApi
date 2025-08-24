import asyncio
from app.database import async_session_maker
from app.achievements.models import AchievementType
from sqlalchemy import select

async def check_none_values():
    async with async_session_maker() as session:
        print("🔍 ПРОВЕРКА ЗАПИСЕЙ С NONE ЗНАЧЕНИЯМИ")
        print("=" * 60)
        
        # Проверяем записи с None в обязательных полях
        result = await session.execute(
            select(AchievementType).where(
                (AchievementType.name.is_(None)) |
                (AchievementType.description.is_(None)) |
                (AchievementType.category.is_(None))
            )
        )
        problematic_types = result.scalars().all()
        
        if problematic_types:
            print(f"❌ Найдено {len(problematic_types)} проблемных записей:")
            for at in problematic_types:
                print(f"   • ID: {at.id}, UUID: {at.uuid}")
                print(f"     name: {repr(at.name)}")
                print(f"     description: {repr(at.description)}")
                print(f"     category: {repr(at.category)}")
                print()
        else:
            print("✅ Все обязательные поля заполнены")
        
        # Проверяем записи с None в is_active
        result = await session.execute(
            select(AchievementType).where(AchievementType.is_active.is_(None))
        )
        none_active_types = result.scalars().all()
        
        if none_active_types:
            print(f"⚠️  Найдено {len(none_active_types)} записей с is_active = None:")
            for at in none_active_types:
                print(f"   • {at.name} (ID: {at.id})")
        else:
            print("✅ Все записи имеют значение is_active")

if __name__ == "__main__":
    asyncio.run(check_none_values())

