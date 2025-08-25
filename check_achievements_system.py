#!/usr/bin/env python3
"""
Итоговая проверка всей системы достижений
"""

import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from sqlalchemy import text

async def check_achievements_system():
    """Проверяет всю систему достижений"""
    
    print("🏆 ПРОВЕРКА ВСЕЙ СИСТЕМЫ ДОСТИЖЕНИЙ")
    print("=" * 80)
    
    async with async_session_maker() as session:
        try:
            # 1. Проверяем существование обеих таблиц
            print("\n📋 ПРОВЕРКА ТАБЛИЦ:")
            print("-" * 40)
            
            tables = ['achievements', 'achievement_types']
            table_status = {}
            
            for table in tables:
                exists_query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    );
                """)
                result = await session.execute(exists_query, {"table_name": table})
                exists = result.scalar()
                table_status[table] = exists
                
                status_icon = "✅" if exists else "❌"
                print(f"  {status_icon} Таблица '{table}': {'существует' if exists else 'НЕ существует'}")
            
            if not all(table_status.values()):
                print("\n❌ Некоторые таблицы отсутствуют!")
                print("   Запустите скрипты создания таблиц")
                return
            
            print("\n✅ Все таблицы существуют!")
            
            # 2. Статистика по таблице типов достижений
            print("\n📊 СТАТИСТИКА ПО ТИПАМ ДОСТИЖЕНИЙ:")
            print("-" * 40)
            
            types_count_query = text("SELECT COUNT(*) FROM achievement_types")
            result = await session.execute(types_count_query)
            types_count = result.scalar()
            print(f"  • Всего типов достижений: {types_count}")
            
            if types_count > 0:
                # Статистика по категориям
                category_stats_query = text("""
                    SELECT category, COUNT(*) as count
                    FROM achievement_types 
                    GROUP BY category 
                    ORDER BY count DESC
                """)
                result = await session.execute(category_stats_query)
                category_stats = result.fetchall()
                
                print(f"  • По категориям:")
                for stat in category_stats:
                    print(f"    - {stat[0]}: {stat[1]} типов")
                
                # Общая сумма очков
                total_points_query = text("SELECT SUM(points) FROM achievement_types")
                result = await session.execute(total_points_query)
                total_points = result.scalar()
                print(f"  • Общая сумма очков: {total_points}")
            
            # 3. Статистика по выданным достижениям
            print("\n🏅 СТАТИСТИКА ПО ВЫДАННЫМ ДОСТИЖЕНИЯМ:")
            print("-" * 40)
            
            achievements_count_query = text("SELECT COUNT(*) FROM achievements")
            result = await session.execute(achievements_count_query)
            achievements_count = result.scalar()
            print(f"  • Всего выданных достижений: {achievements_count}")
            
            if achievements_count > 0:
                # Статистика по статусам
                status_stats_query = text("""
                    SELECT status, COUNT(*) as count
                    FROM achievements 
                    GROUP BY status 
                    ORDER BY count DESC
                """)
                result = await session.execute(status_stats_query)
                status_stats = result.fetchall()
                
                print(f"  • По статусам:")
                for stat in status_stats:
                    print(f"    - {stat[0]}: {stat[1]} достижений")
                
                # Статистика по пользователям
                users_stats_query = text("""
                    SELECT user_id, COUNT(*) as count
                    FROM achievements 
                    GROUP BY user_id 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                result = await session.execute(users_stats_query)
                users_stats = result.fetchall()
                
                print(f"  • Топ пользователей по достижениям:")
                for user_stat in users_stats:
                    # Получаем email пользователя
                    email_query = text('SELECT email FROM "user" WHERE id = :user_id')
                    email_result = await session.execute(email_query, {"user_id": user_stat[0]})
                    email = email_result.scalar()
                    print(f"    - Пользователь {user_stat[0]} ({email}): {user_stat[1]} достижений")
            
            # 4. Проверка связей между таблицами
            print("\n🔗 ПРОВЕРКА СВЯЗЕЙ МЕЖДУ ТАБЛИЦАМИ:")
            print("-" * 40)
            
            if achievements_count > 0 and types_count > 0:
                # Проверяем, есть ли достижения, которых нет в типах
                missing_types_query = text("""
                    SELECT DISTINCT a.name
                    FROM achievements a
                    LEFT JOIN achievement_types at ON a.name = at.name
                    WHERE at.name IS NULL
                """)
                result = await session.execute(missing_types_query)
                missing_types = result.fetchall()
                
                if missing_types:
                    print(f"  ⚠️  Найдено {len(missing_types)} достижений без типа:")
                    for missing in missing_types:
                        print(f"    - {missing[0]}")
                else:
                    print("  ✅ Все выданные достижения имеют соответствующие типы")
                
                # Проверяем, есть ли типы, которые еще не выдавались
                unused_types_query = text("""
                    SELECT at.name, at.category, at.points
                    FROM achievement_types at
                    LEFT JOIN achievements a ON at.name = a.name
                    WHERE a.name IS NULL
                    ORDER BY at.points DESC
                    LIMIT 5
                """)
                result = await session.execute(unused_types_query)
                unused_types = result.fetchall()
                
                if unused_types:
                    print(f"  📝 Топ-5 типов достижений, которые еще не выдавались:")
                    for unused in unused_types:
                        print(f"    - {unused[0]} ({unused[1]}) - {unused[2]} очков")
                else:
                    print("  🎉 Все типы достижений уже выдавались!")
            
            # 5. Общая оценка системы
            print("\n📈 ОБЩАЯ ОЦЕНКА СИСТЕМЫ:")
            print("-" * 40)
            
            if types_count >= 40 and achievements_count > 0:
                print("  🏆 Отлично! Система достижений полностью настроена")
                print("  ✅ Таблица типов достижений заполнена")
                print("  ✅ Есть выданные достижения пользователям")
                print("  ✅ Система готова к использованию")
            elif types_count >= 40:
                print("  🎯 Хорошо! Типы достижений настроены")
                print("  ✅ Таблица типов достижений заполнена")
                print("  ⚠️  Нет выданных достижений (можно создать тестовые)")
                print("  💡 Система готова к тестированию")
            else:
                print("  ❌ Система достижений не полностью настроена")
                print("  ⚠️  Не все типы достижений добавлены")
                print("  💡 Запустите скрипты создания таблиц")
            
            # 6. Рекомендации
            print("\n💡 РЕКОМЕНДАЦИИ:")
            print("-" * 40)
            
            if types_count >= 40:
                print("  ✅ Типы достижений настроены корректно")
                print("  💡 Можете добавлять новые типы через SQL или Python")
                print("  💡 Используйте таблицу для отображения в UI")
                print("  💡 Связывайте с таблицей achievements для отслеживания прогресса")
            
            if achievements_count > 0:
                print("  ✅ Система выдачи достижений работает")
                print("  💡 Можете создавать новые достижения для пользователей")
                print("  💡 Анализируйте прогресс пользователей")
            else:
                print("  💡 Создайте тестовые достижения: python create_test_achievement.py")
                print("  💡 Или демонстрационные: python demo_achievements.py")
            
            print("\n🎯 ДОСТУПНЫЕ СКРИПТЫ:")
            print("-" * 40)
            print("  • python quick_view_achievement_types.py - быстрый просмотр типов")
            print("  • python view_achievement_types.py - детальный просмотр типов")
            print("  • python quick_view_achievements.py - быстрый просмотр достижений")
            print("  • python check_achievements.py - проверка достижений")
            print("  • python check_all_tables.py - общая проверка БД")
            
            print("\n🚀 СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
            
        except Exception as e:
            print(f"❌ Ошибка при проверке системы достижений: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_achievements_system())





