import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from sqlalchemy import text

async def check_achievements():
    """Проверяет содержимое таблицы достижений"""
    async with async_session_maker() as session:
        try:
            # Проверяем количество записей в таблице achievements
            count_query = text("SELECT COUNT(*) FROM achievements")
            result = await session.execute(count_query)
            count = result.scalar()
            print(f"📊 Количество достижений в базе данных: {count}")
            
            if count > 0:
                # Получаем все достижения
                achievements_query = text("""
                    SELECT id, uuid, name, user_id, status, 
                           user_training_id, user_program_id, program_id,
                           created_at, updated_at
                    FROM achievements 
                    ORDER BY created_at DESC
                """)
                result = await session.execute(achievements_query)
                achievements = result.fetchall()
                
                print(f"\n📋 Список всех достижений:")
                print("=" * 80)
                for achievement in achievements:
                    print(f"ID: {achievement[0]}")
                    print(f"UUID: {achievement[1]}")
                    print(f"Название: {achievement[2]}")
                    print(f"ID пользователя: {achievement[3]}")
                    print(f"Статус: {achievement[4]}")
                    print(f"ID тренировки: {achievement[5]}")
                    print(f"ID программы пользователя: {achievement[6]}")
                    print(f"ID программы: {achievement[7]}")
                    print(f"Создано: {achievement[8]}")
                    print(f"Обновлено: {achievement[9]}")
                    print("-" * 40)
            else:
                print("📭 Таблица достижений пуста")
                
        except Exception as e:
            print(f"❌ Ошибка при проверке достижений: {e}")

if __name__ == "__main__":
    asyncio.run(check_achievements())


