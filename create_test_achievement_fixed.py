#!/usr/bin/env python3
"""
Исправленный скрипт для создания тестового достижения
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from sqlalchemy import text

async def create_test_achievement_fixed():
    """Создает тестовое достижение с правильной обработкой транзакций"""
    
    print("🎯 СОЗДАНИЕ ТЕСТОВОГО ДОСТИЖЕНИЯ (ИСПРАВЛЕНО)")
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
                return
            
            print(f"✅ Найдено пользователей: {len(users)}")
            for user in users:
                print(f"   • ID: {user[0]}, Email: {user[2]}")
            
            # Берем первого пользователя для тестирования
            test_user = users[0]
            print(f"\n🎯 Используем пользователя: ID {test_user[0]}, Email: {test_user[2]}")
            
            # 2. Проверяем текущее состояние таблицы
            print("\n📊 Проверяем текущее состояние таблицы...")
            count_before_query = text("SELECT COUNT(*) FROM achievements")
            result = await session.execute(count_before_query)
            count_before = result.scalar()
            print(f"Достижений до создания: {count_before}")
            
            # 3. Создаем тестовое достижение
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
                "name": "Тестовое достижение (исправлено)",
                "user_id": test_user[0],
                "status": "active",
                "created_at": now,
                "updated_at": now
            })
            
            achievement_id = result.scalar()
            
            # 4. ЯВНО коммитим транзакцию
            await session.commit()
            
            print(f"✅ Создано тестовое достижение!")
            print(f"   ID: {achievement_id}")
            print(f"   UUID: {achievement_uuid}")
            print(f"   Название: Тестовое достижение (исправлено)")
            print(f"   Пользователь: {test_user[2]} (ID: {test_user[0]})")
            print(f"   Статус: active")
            print(f"   Создано: {now}")
            print(f"   Транзакция закоммичена!")
            
            # 5. Проверяем результат после коммита
            print("\n📊 ПРОВЕРЯЕМ РЕЗУЛЬТАТ ПОСЛЕ КОММИТА:")
            print("-" * 40)
            
            # Подсчитываем общее количество
            count_after_query = text("SELECT COUNT(*) FROM achievements")
            result = await session.execute(count_after_query)
            count_after = result.scalar()
            print(f"Достижений после создания: {count_after}")
            
            if count_after > count_before:
                print(f"✅ Успешно добавлено {count_after - count_before} достижений!")
            else:
                print("❌ Достижения не добавились!")
            
            # 6. Показываем созданное достижение
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
            else:
                print("❌ Созданное достижение не найдено!")
            
            # 7. Показываем все достижения пользователя
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
            if user_achievements:
                for achievement in user_achievements:
                    print(f"• {achievement[2]} (статус: {achievement[3]}, создано: {achievement[4]})")
            else:
                print("  У пользователя нет достижений")
            
            # 8. Показываем все достижения в таблице
            all_achievements_query = text("""
                SELECT id, name, user_id, status, created_at 
                FROM achievements 
                ORDER BY created_at DESC
            """)
            result = await session.execute(all_achievements_query)
            all_achievements = result.fetchall()
            
            print(f"\n📋 Все достижения в таблице:")
            print("-" * 40)
            if all_achievements:
                for achievement in all_achievements:
                    print(f"• ID {achievement[0]}: {achievement[1]} (пользователь: {achievement[2]}, статус: {achievement[3]})")
            else:
                print("  В таблице нет достижений")
            
            print(f"\n🎯 Теперь вы можете:")
            print("   1. Запустить: python check_achievements.py")
            print("   2. Запустить: python view_achievements_sql.py")
            print("   3. Запустить: python check_all_tables.py")
            
        except Exception as e:
            print(f"❌ Ошибка при создании тестового достижения: {e}")
            import traceback
            traceback.print_exc()
            # Откатываем транзакцию в случае ошибки
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(create_test_achievement_fixed())





