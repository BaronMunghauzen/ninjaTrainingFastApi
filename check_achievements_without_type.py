import asyncio
from app.database import async_session_maker
from app.achievements.models import Achievement
from sqlalchemy import select

async def check_achievements_without_type():
    async with async_session_maker() as session:
        # Находим достижения без achievement_type_id
        result = await session.execute(
            select(Achievement).where(Achievement.achievement_type_id.is_(None))
        )
        achievements = result.scalars().all()
        
        print(f"🏆 ДОСТИЖЕНИЯ БЕЗ ТИПА: {len(achievements)}")
        print("=" * 50)
        
        for achievement in achievements:
            print(f"• {achievement.name} (ID: {achievement.id}, UUID: {achievement.uuid})")
        
        if not achievements:
            print("✅ Все достижения имеют тип!")
        else:
            print(f"\n⚠️  Найдено {len(achievements)} достижений без типа")
            print("💡 Нужно связать их с соответствующими типами в таблице achievement_types")

if __name__ == "__main__":
    asyncio.run(check_achievements_without_type())

