#!/usr/bin/env python3
"""
Демонстрационный скрипт для создания тестовых достижений
"""

import asyncio
import sys
import os
from datetime import datetime, date

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from app.achievements.dao import AchievementDAO
from app.users.dao import UsersDAO
from app.user_training.dao import UserTrainingDAO
from app.user_program.dao import UserProgramDAO
from app.programs.dao import ProgramDAO
from sqlalchemy import text

async def create_demo_achievements():
    """Создает демонстрационные достижения в базе данных"""
    
    print("🎯 СОЗДАНИЕ ДЕМОНСТРАЦИОННЫХ ДОСТИЖЕНИЙ")
    print("=" * 60)
    
    async with async_session_maker() as session:
        try:
            # 1. Проверяем существующих пользователей
            print("\n👥 Проверяем пользователей...")
            users_query = text('SELECT id, uuid, email FROM "user" LIMIT 5')
            result = await session.execute(users_query)
            users = result.fetchall()
            
            if not users:
                print("❌ Нет пользователей в базе данных!")
                print("   Сначала создайте пользователя через API или напрямую в БД")
                return
            
            print(f"✅ Найдено пользователей: {len(users)}")
            for user in users:
                print(f"   • ID: {user[0]}, Email: {user[2]}")
            
            # Берем первого пользователя для демонстрации
            demo_user = users[0]
            print(f"\n🎯 Используем пользователя: ID {demo_user[0]}, Email: {demo_user[2]}")
            
            # 2. Создаем демонстрационные достижения
            print("\n🏆 Создаем демонстрационные достижения...")
            
            # Список достижений для демонстрации
            demo_achievements = [
                {
                    "name": "1 тренировка",
                    "status": "active",
                    "description": "Первая тренировка пользователя"
                },
                {
                    "name": "3 тренировки",
                    "status": "active", 
                    "description": "Третья тренировка пользователя"
                },
                {
                    "name": "5 тренировок",
                    "status": "active",
                    "description": "Пятая тренировка пользователя"
                },
                {
                    "name": "Ранняя пташка",
                    "status": "active",
                    "description": "5 тренировок с 5 до 8 утра"
                },
                {
                    "name": "Сова",
                    "status": "active",
                    "description": "5 тренировок с 21 до 00"
                },
                {
                    "name": "С Новым годом 2025",
                    "status": "active",
                    "description": "Тренировка в новогоднюю ночь"
                },
                {
                    "name": "Международный женский день 2025",
                    "status": "active",
                    "description": "Тренировка 8 марта"
                },
                {
                    "name": "Мужской день 2025",
                    "status": "active",
                    "description": "Тренировка 23 февраля"
                },
                {
                    "name": "Мощь и сила",
                    "status": "active",
                    "description": "За выполнение силовых упражнений"
                },
                {
                    "name": "3 раза в неделю",
                    "status": "active",
                    "description": "3 тренировки за неделю"
                },
                {
                    "name": "2 недели подряд",
                    "status": "active",
                    "description": "2 недели тренировок подряд"
                },
                {
                    "name": "2 месяца подряд",
                    "status": "active",
                    "description": "2 месяца тренировок подряд"
                }
            ]
            
            created_count = 0
            
            for achievement_data in demo_achievements:
                try:
                    # Создаем достижение через DAO
                    achievement_uuid = await AchievementDAO.add(
                        name=achievement_data["name"],
                        user_id=demo_user[0],
                        status=achievement_data["status"]
                    )
                    
                    print(f"✅ Создано: {achievement_data['name']} (UUID: {achievement_uuid})")
                    created_count += 1
                    
                except Exception as e:
                    print(f"❌ Ошибка создания '{achievement_data['name']}': {e}")
            
            print(f"\n🎉 Создано достижений: {created_count} из {len(demo_achievements)}")
            
            # 3. Показываем результат
            print("\n📊 ПРОВЕРЯЕМ РЕЗУЛЬТАТ:")
            print("-" * 40)
            
            # Подсчитываем общее количество
            count_query = text("SELECT COUNT(*) FROM achievements")
            result = await session.execute(count_query)
            total_count = result.scalar()
            print(f"Всего достижений в базе: {total_count}")
            
            # Показываем достижения пользователя
            user_achievements_query = text("""
                SELECT id, uuid, name, status, created_at 
                FROM achievements 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC
            """)
            result = await session.execute(user_achievements_query, {"user_id": demo_user[0]})
            user_achievements = result.fetchall()
            
            print(f"\n📋 Достижения пользователя {demo_user[2]}:")
            print("-" * 40)
            for achievement in user_achievements:
                print(f"• {achievement[2]} (статус: {achievement[3]}, создано: {achievement[4]})")
            
            print(f"\n🎯 Теперь вы можете:")
            print("   1. Запустить: python check_achievements.py")
            print("   2. Запустить: python check_all_tables.py")
            print("   3. Проверить через API: GET /achievements/")
            print("   4. Посмотреть в вашей СУБД (pgAdmin, DBeaver, etc.)")
            
        except Exception as e:
            print(f"❌ Ошибка при создании демо-достижений: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_demo_achievements())
