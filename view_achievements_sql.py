#!/usr/bin/env python3
"""
Скрипт для прямого просмотра таблицы достижений через SQL
"""

import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from sqlalchemy import text

async def view_achievements_sql():
    """Показывает таблицу достижений через прямые SQL запросы"""
    
    print("🔍 ПРЯМОЙ ПРОСМОТР ТАБЛИЦЫ ACHIEVEMENTS")
    print("=" * 60)
    
    async with async_session_maker() as session:
        try:
            # 1. Проверяем существование таблицы
            print("\n📋 Проверяем существование таблицы...")
            table_exists_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'achievements'
                );
            """)
            result = await session.execute(table_exists_query)
            table_exists = result.scalar()
            
            if not table_exists:
                print("❌ Таблица 'achievements' не существует!")
                return
            
            print("✅ Таблица 'achievements' существует")
            
            # 2. Показываем структуру таблицы
            print("\n🏗️ СТРУКТУРА ТАБЛИЦЫ:")
            print("-" * 40)
            structure_query = text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    ordinal_position
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'achievements' 
                ORDER BY ordinal_position;
            """)
            result = await session.execute(structure_query)
            columns = result.fetchall()
            
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"  {col[4]:2d}. {col[0]:<20} {col[1]:<15} {nullable}{default}")
            
            # 3. Показываем количество записей
            print("\n📊 КОЛИЧЕСТВО ЗАПИСЕЙ:")
            print("-" * 40)
            count_query = text("SELECT COUNT(*) FROM achievements")
            result = await session.execute(count_query)
            total_count = result.scalar()
            print(f"Всего записей: {total_count}")
            
            # 4. Показываем все записи (если есть)
            if total_count > 0:
                print(f"\n📋 ВСЕ ЗАПИСИ В ТАБЛИЦЕ:")
                print("-" * 40)
                
                # Получаем все записи
                all_records_query = text("""
                    SELECT 
                        id,
                        uuid,
                        name,
                        user_id,
                        status,
                        user_training_id,
                        user_program_id,
                        program_id,
                        created_at,
                        updated_at
                    FROM achievements 
                    ORDER BY created_at DESC;
                """)
                result = await session.execute(all_records_query)
                records = result.fetchall()
                
                for i, record in enumerate(records, 1):
                    print(f"\n🎯 Запись #{i}:")
                    print(f"   ID: {record[0]}")
                    print(f"   UUID: {record[1]}")
                    print(f"   Название: {record[2]}")
                    print(f"   ID пользователя: {record[3]}")
                    print(f"   Статус: {record[4]}")
                    print(f"   ID тренировки: {record[5]}")
                    print(f"   ID программы пользователя: {record[6]}")
                    print(f"   ID программы: {record[7]}")
                    print(f"   Создано: {record[8]}")
                    print(f"   Обновлено: {record[9]}")
                    print("   " + "-" * 30)
            else:
                print("\n📭 Таблица пуста - записей нет")
                
                # Показываем пример INSERT запроса
                print("\n💡 Пример INSERT запроса для создания достижения:")
                print("-" * 40)
                print("""
INSERT INTO achievements (uuid, name, user_id, status, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'Первое достижение',
    1,
    'active',
    NOW(),
    NOW()
);
                """)
            
            # 5. Показываем статистику по статусам
            print("\n📈 СТАТИСТИКА ПО СТАТУСАМ:")
            print("-" * 40)
            status_stats_query = text("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM achievements 
                GROUP BY status 
                ORDER BY count DESC;
            """)
            result = await session.execute(status_stats_query)
            status_stats = result.fetchall()
            
            if status_stats:
                for stat in status_stats:
                    print(f"  • {stat[0]}: {stat[1]} записей")
            else:
                print("  Нет данных для статистики")
            
            # 6. Показываем топ пользователей по количеству достижений
            print("\n👥 ТОП ПОЛЬЗОВАТЕЛЕЙ ПО ДОСТИЖЕНИЯМ:")
            print("-" * 40)
            top_users_query = text("""
                SELECT 
                    user_id,
                    COUNT(*) as achievements_count
                FROM achievements 
                GROUP BY user_id 
                ORDER BY achievements_count DESC 
                LIMIT 5;
            """)
            result = await session.execute(top_users_query)
            top_users = result.fetchall()
            
            if top_users:
                for user in top_users:
                    print(f"  • Пользователь ID {user[0]}: {user[1]} достижений")
            else:
                print("  Нет данных о пользователях")
                
        except Exception as e:
            print(f"❌ Ошибка при просмотре таблицы: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(view_achievements_sql())





