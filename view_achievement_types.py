#!/usr/bin/env python3
"""
Скрипт для просмотра таблицы типов достижений
"""

import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from sqlalchemy import text

async def view_achievement_types():
    """Показывает таблицу типов достижений"""
    
    print("🏆 ПРОСМОТР ТАБЛИЦЫ ТИПОВ ДОСТИЖЕНИЙ")
    print("=" * 60)
    
    async with async_session_maker() as session:
        try:
            # 1. Проверяем существование таблицы
            print("\n📋 Проверяем существование таблицы...")
            table_exists_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'achievement_types'
                );
            """)
            result = await session.execute(table_exists_query)
            table_exists = result.scalar()
            
            if not table_exists:
                print("❌ Таблица 'achievement_types' не существует!")
                print("   Сначала запустите: python create_achievement_types_table.py")
                return
            
            print("✅ Таблица 'achievement_types' существует")
            
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
                AND table_name = 'achievement_types' 
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
            count_query = text("SELECT COUNT(*) FROM achievement_types")
            result = await session.execute(count_query)
            total_count = result.scalar()
            print(f"Всего типов достижений: {total_count}")
            
            if total_count == 0:
                print("\n📭 Таблица пуста - типы достижений не добавлены")
                return
            
            # 4. Статистика по категориям
            print(f"\n📈 СТАТИСТИКА ПО КАТЕГОРИЯМ:")
            print("-" * 40)
            category_stats_query = text("""
                SELECT category, COUNT(*) as count
                FROM achievement_types 
                GROUP BY category 
                ORDER BY count DESC
            """)
            result = await session.execute(category_stats_query)
            category_stats = result.fetchall()
            
            for stat in category_stats:
                print(f"  • {stat[0]}: {stat[1]} типов")
            
            # 5. Статистика по подкатегориям
            print(f"\n📊 СТАТИСТИКА ПО ПОДКАТЕГОРИЯМ:")
            print("-" * 40)
            subcategory_stats_query = text("""
                SELECT subcategory, COUNT(*) as count
                FROM achievement_types 
                WHERE subcategory IS NOT NULL
                GROUP BY subcategory 
                ORDER BY count DESC
            """)
            result = await session.execute(subcategory_stats_query)
            subcategory_stats = result.fetchall()
            
            for stat in subcategory_stats:
                print(f"  • {stat[0]}: {stat[1]} типов")
            
            # 6. Статистика по очкам
            print(f"\n🏆 СТАТИСТИКА ПО ОЧКАМ:")
            print("-" * 40)
            points_stats_query = text("""
                SELECT 
                    MIN(points) as min_points,
                    MAX(points) as max_points,
                    AVG(points) as avg_points,
                    SUM(points) as total_points
                FROM achievement_types
            """)
            result = await session.execute(points_stats_query)
            points_stats = result.fetchone()
            
            print(f"  • Минимум очков: {points_stats[0]}")
            print(f"  • Максимум очков: {points_stats[1]}")
            print(f"  • Среднее очков: {points_stats[2]:.1f}")
            print(f"  • Общая сумма очков: {points_stats[3]}")
            
            # 7. Топ-10 достижений по очкам
            print(f"\n🥇 ТОП-10 ДОСТИЖЕНИЙ ПО ОЧКАМ:")
            print("-" * 60)
            top_query = text("""
                SELECT 
                    name, 
                    category, 
                    subcategory, 
                    points, 
                    icon,
                    description
                FROM achievement_types 
                ORDER BY points DESC 
                LIMIT 10
            """)
            result = await session.execute(top_query)
            top_achievements = result.fetchall()
            
            for i, achievement in enumerate(top_achievements, 1):
                print(f"  {i:2d}. {achievement[4]} {achievement[0]:<25} | {achievement[1]:<15} | {achievement[2]:<20} | {achievement[3]:>4} очков")
                print(f"      {achievement[5]}")
                if i < len(top_achievements):
                    print()
            
            # 8. Все достижения по категориям
            print(f"\n📋 ВСЕ ДОСТИЖЕНИЯ ПО КАТЕГОРИЯМ:")
            print("=" * 80)
            
            for category in [stat[0] for stat in category_stats]:
                print(f"\n🎯 {category.upper()}:")
                print("-" * 40)
                
                category_query = text("""
                    SELECT 
                        name, 
                        subcategory, 
                        points, 
                        icon,
                        requirements
                    FROM achievement_types 
                    WHERE category = :category
                    ORDER BY points DESC
                """)
                result = await session.execute(category_query, {"category": category})
                category_achievements = result.fetchall()
                
                for achievement in category_achievements:
                    print(f"  {achievement[3]} {achievement[0]:<25} | {achievement[1]:<20} | {achievement[2]:>4} очков")
                    print(f"      Требования: {achievement[4]}")
                    print()
            
            # 9. Поиск по ключевым словам
            print(f"\n🔍 ПОИСК ПО КЛЮЧЕВЫМ СЛОВАМ:")
            print("-" * 40)
            
            search_keywords = ["утро", "ночь", "неделя", "месяц", "год", "сила", "тренировка"]
            
            for keyword in search_keywords:
                search_query = text("""
                    SELECT name, category, points, icon
                    FROM achievement_types 
                    WHERE LOWER(name) LIKE LOWER(:keyword) 
                       OR LOWER(description) LIKE LOWER(:keyword)
                       OR LOWER(requirements) LIKE LOWER(:keyword)
                    ORDER BY points DESC
                """)
                result = await session.execute(search_query, {"keyword": f"%{keyword}%"})
                search_results = result.fetchall()
                
                if search_results:
                    print(f"\n  🔎 '{keyword}':")
                    for result_item in search_results:
                        print(f"    • {result_item[3]} {result_item[0]} ({result_item[1]}) - {result_item[2]} очков")
            
            # 10. SQL запросы для работы с таблицей
            print(f"\n💡 ПОЛЕЗНЫЕ SQL ЗАПРОСЫ:")
            print("-" * 40)
            print("""
-- Все достижения определенной категории
SELECT * FROM achievement_types WHERE category = 'Временные';

-- Достижения с высокими очками
SELECT * FROM achievement_types WHERE points >= 100 ORDER BY points DESC;

-- Поиск по названию
SELECT * FROM achievement_types WHERE name ILIKE '%неделя%';

-- Статистика по категориям
SELECT category, COUNT(*), AVG(points), SUM(points) 
FROM achievement_types 
GROUP BY category 
ORDER BY SUM(points) DESC;

-- Достижения определенного уровня сложности
SELECT * FROM achievement_types 
WHERE subcategory IN ('Начальный уровень', 'Средний уровень')
ORDER BY points;
            """)
            
        except Exception as e:
            print(f"❌ Ошибка при просмотре таблицы типов достижений: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(view_achievement_types())





