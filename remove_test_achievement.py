import asyncio
from app.database import async_session_maker
from app.achievements.models import Achievement
from sqlalchemy import select, delete

async def remove_test_achievement():
    async with async_session_maker() as session:
        print("🗑️  УДАЛЕНИЕ ТЕСТОВОГО ДОСТИЖЕНИЯ")
        print("=" * 50)
        
        # Находим тестовое достижение
        result = await session.execute(
            select(Achievement).where(Achievement.name == 'Тестовое достижение (исправлено)')
        )
        achievement = result.scalar_one_or_none()
        
        if achievement:
            # Удаляем достижение
            await session.execute(
                delete(Achievement).where(Achievement.id == achievement.id)
            )
            print(f"✅ Удалено: {achievement.name} (ID: {achievement.id})")
            
            # Коммитим изменения
            await session.commit()
            
            # Проверяем результат
            result = await session.execute(
                select(Achievement).where(Achievement.achievement_type_id.is_(None))
            )
            remaining = result.scalars().all()
            
            if not remaining:
                print("✅ Все достижения теперь имеют тип!")
            else:
                print(f"⚠️  Осталось {len(remaining)} достижений без типа")
        else:
            print("❌ Тестовое достижение не найдено")

if __name__ == "__main__":
    asyncio.run(remove_test_achievement())

