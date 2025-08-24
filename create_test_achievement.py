#!/usr/bin/env python3
"""
Скрипт для создания тестового достижения напрямую в базе данных
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from sqlalchemy import text

async def create_test_achievement():
    """Создает тестовое достижение напрямую в базе данных"""
    
    print("🎯 СОЗДАНИЕ ТЕСТОВОГО ДОСТИЖЕНИЯ")
    print("=" * 60)
    
    async with async_session_maker() as session:
        try:
            # 1. Проверяем существующих пользователей
            print("\n👥 Проверяем пользователей...")
            users_query = text('SELECT id, uuid, email FROM "user" LIMIT 3')
            result = await session.execute(users_query)
            users = result.fetchall()
            
            if not users:
                print("❌ Нет пользователей в базе данных!")
                print("   Сначала создайте пользователя через API или напрямую в БД")
                return
            
            print(f"✅ Найдено пользователей: {len(users)}")
            for user in users:
                print(f"   • ID: {user[0]}, Email: {user[2]}")
            
            # Берем первого пользователя для тестирования
            test_user = users[0]
            print(f"\n🎯 Используем пользователя: ID {test_user[0]}, Email: {test_user[2]}")
            
            # 2. Создаем тестовое достижение напрямую через SQL
            print("\n🏆 Создаем тестовое достижение...")
            
            # Генерируем UUID для достижения
            uuid_query = text("SELECT gen_random_uuid()")
            result = await session.execute(uuid_query)
            achievement_uuid = result.scalar()
            
            # Создаем достижение
            insert_query = text("""
                INSERT INTO achievements (
                    uuid, 
                    name, 
                    user_id, 
                    status, 
                    created_at, 
                    updated_at
                ) VALUES (
                    :uuid,
                    :name,
                    :user_id,
                    :status,
                    :created_at,
                    :updated_at
                ) RETURNING id;
            """)
            
            now = datetime.now()
            result = await session.execute(insert_query, {
                "uuid": achievement_uuid,
                "name": "Тестовое достижение",
                "user_id": test_user[0],
                "status": "active",
                "created_at": now,
                "updated_at": now
            })
            
            achievement_id = result.scalar()
            
            print(f"✅ Создано тестовое достижение!")
            print(f"   ID: {achievement_id}")
            print(f"   UUID: {achievement_uuid}")
            print(f"   Название: Тестовое достижение")
            print(f"   Пользователь: {test_user[2]} (ID: {test_user[0]})")
            print(f"   Статус: active")
            print(f"   Создано: {now}")
            
            # 3. Проверяем результат
            print("\n📊 ПРОВЕРЯЕМ РЕЗУЛЬТАТ:")
            print("-" * 40)
            
            # Подсчитываем общее количество
            count_query = text("SELECT COUNT(*) FROM achievements")
            result = await session.execute(count_query)
            total_count = result.scalar()
            print(f"Всего достижений в базе: {total_count}")
            
            # Показываем созданное достижение
            select_query = text("""
                SELECT id, uuid, name, user_id, status, created_at, updated_at
                FROM achievements 
                WHERE id = :achievement_id
            """)
            result = await session.execute(select_query, {"achievement_id": achievement_id})
            achievement = result.fetchone()
            
            if achievement:
                print(f"\n📋 Созданное достижение:")
                print(f"   ID: {achievement[0]}")
                print(f"   UUID: {achievement[1]}")
                print(f"   Название: {achievement[2]}")
                print(f"   ID пользователя: {achievement[3]}")
                print(f"   Статус: {achievement[4]}")
                print(f"   Создано: {achievement[5]}")
                print(f"   Обновлено: {achievement[6]}")
            
            # 4. Показываем все достижения пользователя
            user_achievements_query = text("""
                SELECT id, uuid, name, status, created_at 
                FROM achievements 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC
            """)
            result = await session.execute(user_achievements_query, {"user_id": test_user[0]})
            user_achievements = result.fetchall()
            
            print(f"\n📋 Все достижения пользователя {test_user[2]}:")
            print("-" * 40)
            for achievement in user_achievements:
                print(f"• {achievement[2]} (статус: {achievement[3]}, создано: {achievement[4]})")
            
            print(f"\n🎯 Теперь вы можете:")
            print("   1. Запустить: python check_achievements.py")
            print("   2. Запустить: python view_achievements_sql.py")
            print("   3. Запустить: python check_all_tables.py")
            print("   4. Проверить через API: GET /achievements/")
            print("   5. Посмотреть в вашей СУБД (pgAdmin, DBeaver, etc.)")
            
            # 5. Показываем SQL запрос для повторного создания
            print(f"\n💡 SQL запрос для повторного создания:")
            print("-" * 40)
            print(f"""
INSERT INTO achievements (uuid, name, user_id, status, created_at, updated_at)
VALUES (
    '{achievement_uuid}',
    'Тестовое достижение 2',
    {test_user[0]},
    'active',
    NOW(),
    NOW()
);
            """)
            
        except Exception as e:
            print(f"❌ Ошибка при создании тестового достижения: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_achievement())





