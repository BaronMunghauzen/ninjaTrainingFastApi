#!/usr/bin/env python3
"""
Быстрый просмотр таблицы типов достижений
"""

import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from sqlalchemy import text

async def quick_view_achievement_types():
    """Быстро показывает таблицу типов достижений"""
    
    print("🏆 БЫСТРЫЙ ПРОСМОТР ТИПОВ ДОСТИЖЕНИЙ")
    print("=" * 60)
    
    async with async_session_maker() as session:
        try:
            # 1. Общая статистика
            count_query = text("SELECT COUNT(*) FROM achievement_types")
            result = await session.execute(count_query)
            total_count = result.scalar()
            
            print(f"📊 Всего типов достижений: {total_count}")
            
            if total_count == 0:
                print("📭 Таблица пуста")
                return
            
            # 2. Статистика по категориям
            category_query = text("""
                SELECT category, COUNT(*) as count
                FROM achievement_types 
                GROUP BY category 
                ORDER BY count DESC
            """)
            result = await session.execute(category_query)
            categories = result.fetchall()
            
            print(f"\n📈 По категориям:")
            for cat in categories:
                print(f"   • {cat[0]}: {cat[1]} типов")
            
            # 3. Все достижения в компактном виде
            print(f"\n📋 ВСЕ ДОСТИЖЕНИЯ:")
            print("-" * 80)
            
            achievements_query = text("""
                SELECT 
                    name, 
                    category, 
                    subcategory, 
                    points, 
                    icon,
                    description
                FROM achievement_types 
                ORDER BY category, points DESC
            """)
            result = await session.execute(achievements_query)
            achievements = result.fetchall()
            
            current_category = None
            for achievement in achievements:
                if achievement[1] != current_category:
                    current_category = achievement[1]
                    print(f"\n🎯 {current_category.upper()}:")
                    print("-" * 40)
                
                print(f"  {achievement[4]} {achievement[0]:<25} | {achievement[2]:<20} | {achievement[3]:>4} очков")
                print(f"      {achievement[5]}")
            
            # 4. Топ-5 по очкам
            print(f"\n🥇 ТОП-5 ПО ОЧКАМ:")
            print("-" * 60)
            
            top_query = text("""
                SELECT name, category, points, icon
                FROM achievement_types 
                ORDER BY points DESC 
                LIMIT 5
            """)
            result = await session.execute(top_query)
            top_achievements = result.fetchall()
            
            for i, achievement in enumerate(top_achievements, 1):
                print(f"  {i}. {achievement[3]} {achievement[0]} ({achievement[1]}) - {achievement[2]} очков")
            
            print(f"\n🎯 Всего типов: {total_count}")
            print(f"📊 Общая сумма очков: {sum(a[3] for a in achievements)}")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(quick_view_achievement_types())





