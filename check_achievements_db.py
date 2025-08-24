import asyncio
from app.database import async_session_maker
from app.achievements.models import Achievement
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

async def check_achievements():
    """Проверяет все достижения в базе данных"""
    async with async_session_maker() as session:
        # Получаем все достижения с загрузкой связанных данных
        query = select(Achievement).options(
            joinedload(Achievement.user),
            joinedload(Achievement.user_training),
            joinedload(Achievement.user_program),
            joinedload(Achievement.program)
        )
        
        result = await session.execute(query)
        achievements = result.scalars().all()
        
        print(f"Всего достижений в базе: {len(achievements)}")
        print("=" * 80)
        
        if not achievements:
            print("Достижения не найдены в базе данных")
            return
        
        # Группируем достижения по типам
        achievement_types = {}
        for ach in achievements:
            if ach.name not in achievement_types:
                achievement_types[ach.name] = []
            achievement_types[ach.name].append(ach)
        
        print("Достижения по типам:")
        print("-" * 40)
        
        for ach_type, ach_list in sorted(achievement_types.items()):
            print(f"{ach_type}: {len(ach_list)} шт.")
        
        print("\n" + "=" * 80)
        print("Детальная информация по каждому достижению:")
        print("-" * 80)
        
        for i, ach in enumerate(achievements, 1):
            print(f"\n{i}. ID: {ach.id}")
            print(f"   UUID: {ach.uuid}")
            print(f"   Название: {ach.name}")
            print(f"   Пользователь ID: {ach.user_id}")
            print(f"   Статус: {ach.status}")
            print(f"   User Training ID: {ach.user_training_id}")
            print(f"   User Program ID: {ach.user_program_id}")
            print(f"   Program ID: {ach.program_id}")
            
            # Показываем связанные данные
            if ach.user_training:
                print(f"   Дата тренировки: {ach.training_date}")
                print(f"   Время завершения: {ach.completed_at}")
            
            if ach.user_program:
                print(f"   User Program UUID: {ach.user_program.uuid}")
            
            if ach.program:
                print(f"   Program UUID: {ach.program.uuid}")
                print(f"   Program Name: {ach.program.name}")

if __name__ == "__main__":
    asyncio.run(check_achievements())
