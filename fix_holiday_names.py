import asyncio
from app.database import async_session_maker
from app.achievements.models import Achievement
from sqlalchemy import select, update

async def fix_holiday_names():
    async with async_session_maker() as session:
        print("🎄 ИСПРАВЛЕНИЕ НАЗВАНИЙ ПРАЗДНИЧНЫХ ДОСТИЖЕНИЙ")
        print("=" * 60)
        
        # Маппинг названий
        name_mapping = {
            'С Новым годом 2025': 'С Новым годом',
            'Международный женский день 2025': 'Международный женский день',
            'Мужской день 2025': 'Мужской день'
        }
        
        fixed_count = 0
        
        for old_name, new_name in name_mapping.items():
            # Находим достижение со старым названием
            result = await session.execute(
                select(Achievement).where(Achievement.name == old_name)
            )
            achievement = result.scalar_one_or_none()
            
            if achievement:
                # Обновляем название
                await session.execute(
                    update(Achievement)
                    .where(Achievement.id == achievement.id)
                    .values(name=new_name)
                )
                print(f"✅ '{old_name}' -> '{new_name}'")
                fixed_count += 1
            else:
                print(f"❌ '{old_name}' - не найдено")
        
        # Коммитим изменения
        await session.commit()
        
        print(f"\n📊 Исправлено названий: {fixed_count}")
        
        # Теперь исправляем связи с типами
        print("\n🔗 Исправляем связи с типами...")
        
        result = await session.execute(
            select(Achievement).where(Achievement.achievement_type_id.is_(None))
        )
        achievements = result.scalars().all()
        
        if not achievements:
            print("✅ Все достижения теперь имеют тип!")
        else:
            print(f"⚠️  Осталось {len(achievements)} достижений без типа:")
            for a in achievements:
                print(f"   • {a.name}")

if __name__ == "__main__":
    asyncio.run(fix_holiday_names())

