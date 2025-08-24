import asyncio
from app.database import async_session_maker
from app.achievements.models import AchievementType
from sqlalchemy import select

async def check_holiday_types():
    async with async_session_maker() as session:
        # Проверяем праздничные типы
        holiday_names = ['С Новым годом', 'Международный женский день', 'Мужской день']
        
        for name in holiday_names:
            result = await session.execute(
                select(AchievementType).where(AchievementType.name == name)
            )
            achievement_type = result.scalar_one_or_none()
            
            if achievement_type:
                print(f"✅ {name} - найден (ID: {achievement_type.id})")
            else:
                print(f"❌ {name} - не найден")
        
        # Проверяем все типы с "2025" в названии
        result = await session.execute(
            select(AchievementType).where(AchievementType.name.like('%2025%'))
        )
        types_2025 = result.scalars().all()
        
        print(f"\n🎯 Типы с '2025' в названии: {len(types_2025)}")
        for t in types_2025:
            print(f"   • {t.name}")

if __name__ == "__main__":
    asyncio.run(check_holiday_types())

