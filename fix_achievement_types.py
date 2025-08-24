import asyncio
from app.database import async_session_maker
from app.achievements.models import Achievement, AchievementType
from sqlalchemy import select, update

async def fix_achievement_types():
    async with async_session_maker() as session:
        print("🔧 ИСПРАВЛЕНИЕ СВЯЗЕЙ ДОСТИЖЕНИЙ С ТИПАМИ")
        print("=" * 60)
        
        # Получаем все типы достижений
        result = await session.execute(select(AchievementType))
        achievement_types = result.scalars().all()
        
        # Создаем словарь для быстрого поиска по имени
        type_by_name = {at.name: at for at in achievement_types}
        
        print(f"📊 Найдено {len(achievement_types)} типов достижений")
        print(f"📋 Найдено {len(type_by_name)} уникальных имен")
        
        # Получаем все достижения без типа
        result = await session.execute(
            select(Achievement).where(Achievement.achievement_type_id.is_(None))
        )
        achievements = result.scalars().all()
        
        print(f"🎯 Найдено {len(achievements)} достижений без типа")
        print()
        
        fixed_count = 0
        not_found = []
        
        for achievement in achievements:
            achievement_type = type_by_name.get(achievement.name)
            
            if achievement_type:
                # Обновляем achievement_type_id
                await session.execute(
                    update(Achievement)
                    .where(Achievement.id == achievement.id)
                    .values(achievement_type_id=achievement_type.id)
                )
                print(f"✅ {achievement.name} -> {achievement_type.name} (ID: {achievement_type.id})")
                fixed_count += 1
            else:
                print(f"❌ {achievement.name} - тип не найден")
                not_found.append(achievement.name)
        
        # Коммитим изменения
        await session.commit()
        
        print()
        print("📊 РЕЗУЛЬТАТ:")
        print(f"✅ Исправлено: {fixed_count} достижений")
        print(f"❌ Не найдено: {len(not_found)} достижений")
        
        if not_found:
            print("\n⚠️  Достижения без типа:")
            for name in not_found:
                print(f"   • {name}")
            print("\n💡 Нужно создать соответствующие типы в таблице achievement_types")
        
        print("\n🎯 Проверяем результат...")
        
        # Проверяем результат
        result = await session.execute(
            select(Achievement).where(Achievement.achievement_type_id.is_(None))
        )
        remaining = result.scalars().all()
        
        if not remaining:
            print("✅ Все достижения теперь имеют тип!")
        else:
            print(f"⚠️  Осталось {len(remaining)} достижений без типа")

if __name__ == "__main__":
    asyncio.run(fix_achievement_types())

