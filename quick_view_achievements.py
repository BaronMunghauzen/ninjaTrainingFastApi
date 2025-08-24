#!/usr/bin/env python3
"""
Быстрый просмотр всех достижений в удобном формате
"""

import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from sqlalchemy import text

async def quick_view_achievements():
    """Быстро показывает все достижения в удобном формате"""
    
    print("🏆 БЫСТРЫЙ ПРОСМОТР ВСЕХ ДОСТИЖЕНИЙ")
    print("=" * 60)
    
    async with async_session_maker() as session:
        try:
            # 1. Общая статистика
            count_query = text("SELECT COUNT(*) FROM achievements")
            result = await session.execute(count_query)
            total_count = result.scalar()
            
            print(f"📊 Всего достижений в базе: {total_count}")
            
            if total_count == 0:
                print("📭 Таблица пуста")
                return
            
            # 2. Статистика по статусам
            status_query = text("""
                SELECT status, COUNT(*) as count
                FROM achievements 
                GROUP BY status 
                ORDER BY count DESC
            """)
            result = await session.execute(status_query)
            status_stats = result.fetchall()
            
            print(f"\n📈 Статистика по статусам:")
            for stat in status_stats:
                print(f"   • {stat[0]}: {stat[1]} записей")
            
            # 3. Статистика по пользователям
            users_query = text("""
                SELECT user_id, COUNT(*) as count
                FROM achievements 
                GROUP BY user_id 
                ORDER BY count DESC
            """)
            result = await session.execute(users_query)
            users_stats = result.fetchall()
            
            print(f"\n👥 Статистика по пользователям:")
            for user_stat in users_stats:
                # Получаем email пользователя
                email_query = text('SELECT email FROM "user" WHERE id = :user_id')
                email_result = await session.execute(email_query, {"user_id": user_stat[0]})
                email = email_result.scalar()
                print(f"   • Пользователь {user_stat[0]} ({email}): {user_stat[1]} достижений")
            
            # 4. Все достижения в компактном виде
            print(f"\n📋 ВСЕ ДОСТИЖЕНИЯ:")
            print("-" * 60)
            
            achievements_query = text("""
                SELECT 
                    a.id,
                    a.name,
                    a.status,
                    a.user_id,
                    u.email,
                    a.created_at
                FROM achievements a
                JOIN "user" u ON a.user_id = u.id
                ORDER BY a.created_at DESC
            """)
            result = await session.execute(achievements_query)
            achievements = result.fetchall()
            
            for i, achievement in enumerate(achievements, 1):
                print(f"{i:2d}. [{achievement[2].upper():<8}] {achievement[1]:<30} | Пользователь: {achievement[4]} | {achievement[5]}")
            
            # 5. Группировка по типам достижений
            print(f"\n🎯 ГРУППИРОВКА ПО ТИПАМ:")
            print("-" * 60)
            
            # Временные достижения
            time_achievements = [a for a in achievements if a[1] in ['Ранняя пташка', 'Сова']]
            if time_achievements:
                print(f"🌅 Временные достижения ({len(time_achievements)}):")
                for a in time_achievements:
                    print(f"   • {a[1]}")
            
            # Праздничные достижения
            holiday_achievements = [a for a in achievements if any(x in a[1] for x in ['Новым годом', 'женский день', 'Мужской день'])]
            if holiday_achievements:
                print(f"🎉 Праздничные достижения ({len(holiday_achievements)}):")
                for a in holiday_achievements:
                    print(f"   • {a[1]}")
            
            # Достижения за количество тренировок
            training_count_achievements = [a for a in achievements if 'тренировк' in a[1] and not any(x in a[1] for x in ['неделю', 'недели', 'месяца'])]
            if training_count_achievements:
                print(f"💪 За количество тренировок ({len(training_count_achievements)}):")
                for a in training_count_achievements:
                    print(f"   • {a[1]}")
            
            # Достижения за недели
            weekly_achievements = [a for a in achievements if 'неделю' in a[1] or 'недели' in a[1]]
            if weekly_achievements:
                print(f"📅 За недели ({len(weekly_achievements)}):")
                for a in weekly_achievements:
                    print(f"   • {a[1]}")
            
            # Достижения за месяцы
            monthly_achievements = [a for a in achievements if 'месяца' in a[1]]
            if monthly_achievements:
                print(f"📆 За месяцы ({len(monthly_achievements)}):")
                for a in monthly_achievements:
                    print(f"   • {a[1]}")
            
            # Специальные достижения
            special_achievements = [a for a in achievements if a[1] in ['Мощь и сила']]
            if special_achievements:
                print(f"⭐ Специальные ({len(special_achievements)}):")
                for a in special_achievements:
                    print(f"   • {a[1]}")
            
            # 6. Последние достижения
            print(f"\n🕒 ПОСЛЕДНИЕ ДОСТИЖЕНИЯ:")
            print("-" * 60)
            recent_achievements = achievements[:5]
            for a in recent_achievements:
                print(f"   • {a[1]} - {a[5]}")
            
            print(f"\n🎯 Всего типов достижений: {len(set(a[1] for a in achievements))}")
            print(f"📊 Общее количество записей: {total_count}")
            
        except Exception as e:
            print(f"❌ Ошибка при просмотре достижений: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_view_achievements())





