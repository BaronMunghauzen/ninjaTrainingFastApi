#!/usr/bin/env python3
"""
Скрипт для создания таблицы со списком всех типов достижений
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from sqlalchemy import text

async def create_achievement_types_table():
    """Создает таблицу со списком всех типов достижений"""
    
    print("🏆 СОЗДАНИЕ ТАБЛИЦЫ ТИПОВ ДОСТИЖЕНИЙ")
    print("=" * 60)
    
    async with async_session_maker() as session:
        try:
            # 1. Создаем таблицу achievement_types
            print("\n📋 Создаем таблицу achievement_types...")
            
            create_table_query = text("""
                CREATE TABLE IF NOT EXISTS achievement_types (
                    id SERIAL PRIMARY KEY,
                    uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
                    name VARCHAR NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    category VARCHAR NOT NULL,
                    subcategory VARCHAR,
                    requirements TEXT,
                    icon VARCHAR,
                    points INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
            """)
            
            await session.execute(create_table_query)
            print("✅ Таблица achievement_types создана")
            
            # 2. Создаем индексы для быстрого поиска
            print("\n🔍 Создаем индексы...")
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_achievement_types_category ON achievement_types(category)",
                "CREATE INDEX IF NOT EXISTS idx_achievement_types_name ON achievement_types(name)",
                "CREATE INDEX IF NOT EXISTS idx_achievement_types_active ON achievement_types(is_active)"
            ]
            
            for index_query in indexes:
                await session.execute(text(index_query))
            
            print("✅ Индексы созданы")
            
            # 3. Заполняем таблицу всеми типами достижений
            print("\n📝 Заполняем таблицу типами достижений...")
            
            # Список всех достижений системы
            achievement_types = [
                # Временные достижения
                {
                    "name": "Ранняя пташка",
                    "description": "5 тренировок с 5 до 8 утра",
                    "category": "Временные",
                    "subcategory": "Утренние",
                    "requirements": "Завершить 5 тренировок в период с 5:00 до 8:00 утра",
                    "icon": "🌅",
                    "points": 50
                },
                {
                    "name": "Сова",
                    "description": "5 тренировок с 21 до 00 (полночь)",
                    "category": "Временные",
                    "subcategory": "Ночные",
                    "requirements": "Завершить 5 тренировок в период с 21:00 до 00:00",
                    "icon": "🦉",
                    "points": 50
                },
                
                # Праздничные достижения
                {
                    "name": "С Новым годом",
                    "description": "Тренировка в новогоднюю ночь",
                    "category": "Праздничные",
                    "subcategory": "Новый год",
                    "requirements": "Завершить тренировку 1 января",
                    "icon": "🎄",
                    "points": 100
                },
                {
                    "name": "Международный женский день",
                    "description": "Тренировка 8 марта",
                    "category": "Праздничные",
                    "subcategory": "8 марта",
                    "requirements": "Завершить тренировку 8 марта",
                    "icon": "🌸",
                    "points": 100
                },
                {
                    "name": "Мужской день",
                    "description": "Тренировка 23 февраля",
                    "category": "Праздничные",
                    "subcategory": "23 февраля",
                    "requirements": "Завершить тренировку 23 февраля",
                    "icon": "🦸",
                    "points": 100
                },
                
                # Достижения за количество тренировок
                {
                    "name": "1 тренировка",
                    "description": "Первая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Начальный уровень",
                    "requirements": "Завершить 1 тренировку",
                    "icon": "🎯",
                    "points": 10
                },
                {
                    "name": "3 тренировки",
                    "description": "Третья тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Начальный уровень",
                    "requirements": "Завершить 3 тренировки",
                    "icon": "🎯",
                    "points": 20
                },
                {
                    "name": "5 тренировок",
                    "description": "Пятая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Начальный уровень",
                    "requirements": "Завершить 5 тренировок",
                    "icon": "🎯",
                    "points": 30
                },
                {
                    "name": "7 тренировок",
                    "description": "Седьмая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Средний уровень",
                    "requirements": "Завершить 7 тренировок",
                    "icon": "🎯",
                    "points": 40
                },
                {
                    "name": "10 тренировок",
                    "description": "Десятая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Средний уровень",
                    "requirements": "Завершить 10 тренировок",
                    "icon": "🎯",
                    "points": 50
                },
                {
                    "name": "15 тренировок",
                    "description": "Пятнадцатая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Средний уровень",
                    "requirements": "Завершить 15 тренировок",
                    "icon": "🎯",
                    "points": 60
                },
                {
                    "name": "20 тренировок",
                    "description": "Двадцатая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Продвинутый уровень",
                    "requirements": "Завершить 20 тренировок",
                    "icon": "🎯",
                    "points": 70
                },
                {
                    "name": "25 тренировок",
                    "description": "Двадцать пятая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Продвинутый уровень",
                    "requirements": "Завершить 25 тренировок",
                    "icon": "🎯",
                    "points": 80
                },
                {
                    "name": "30 тренировок",
                    "description": "Тридцатая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Продвинутый уровень",
                    "requirements": "Завершить 30 тренировок",
                    "icon": "🎯",
                    "points": 90
                },
                {
                    "name": "40 тренировок",
                    "description": "Сороковая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Эксперт",
                    "requirements": "Завершить 40 тренировок",
                    "icon": "🎯",
                    "points": 100
                },
                {
                    "name": "50 тренировок",
                    "description": "Пятидесятая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Эксперт",
                    "requirements": "Завершить 50 тренировок",
                    "icon": "🎯",
                    "points": 120
                },
                {
                    "name": "75 тренировок",
                    "description": "Семьдесят пятая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Мастер",
                    "requirements": "Завершить 75 тренировок",
                    "icon": "🎯",
                    "points": 150
                },
                {
                    "name": "100 тренировок",
                    "description": "Сотая тренировка пользователя",
                    "category": "Количество тренировок",
                    "subcategory": "Легенда",
                    "requirements": "Завершить 100 тренировок",
                    "icon": "🎯",
                    "points": 200
                },
                
                # Достижения за тренировки в неделю
                {
                    "name": "3 раза в неделю",
                    "description": "3 тренировки за неделю",
                    "category": "Недельные",
                    "subcategory": "Регулярность",
                    "requirements": "Выполнить 3 тренировки за одну неделю",
                    "icon": "📅",
                    "points": 40
                },
                {
                    "name": "4 раза в неделю",
                    "description": "4 тренировки за неделю",
                    "category": "Недельные",
                    "subcategory": "Регулярность",
                    "requirements": "Выполнить 4 тренировки за одну неделю",
                    "icon": "📅",
                    "points": 50
                },
                {
                    "name": "5 раза в неделю",
                    "description": "5 тренировок за неделю",
                    "category": "Недельные",
                    "subcategory": "Регулярность",
                    "requirements": "Выполнить 5 тренировок за одну неделю",
                    "icon": "📅",
                    "points": 60
                },
                {
                    "name": "6 раза в неделю",
                    "description": "6 тренировок за неделю",
                    "category": "Недельные",
                    "subcategory": "Регулярность",
                    "requirements": "Выполнить 6 тренировок за одну неделю",
                    "icon": "📅",
                    "points": 70
                },
                {
                    "name": "7 раза в неделю",
                    "description": "7 тренировок за неделю",
                    "category": "Недельные",
                    "subcategory": "Регулярность",
                    "requirements": "Выполнить 7 тренировок за одну неделю",
                    "icon": "📅",
                    "points": 80
                },
                
                # Достижения за непрерывные недели
                {
                    "name": "2 недели подряд",
                    "description": "2 недели тренировок подряд",
                    "category": "Непрерывные недели",
                    "subcategory": "Выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 2 недели подряд",
                    "icon": "🔄",
                    "points": 60
                },
                {
                    "name": "3 недели подряд",
                    "description": "3 недели тренировок подряд",
                    "category": "Непрерывные недели",
                    "subcategory": "Выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 3 недели подряд",
                    "icon": "🔄",
                    "points": 80
                },
                {
                    "name": "4 недели подряд",
                    "description": "4 недели тренировок подряд",
                    "category": "Непрерывные недели",
                    "subcategory": "Выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 4 недели подряд",
                    "icon": "🔄",
                    "points": 100
                },
                {
                    "name": "5 недель подряд",
                    "description": "5 недель тренировок подряд",
                    "category": "Непрерывные недели",
                    "subcategory": "Выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 5 недель подряд",
                    "icon": "🔄",
                    "points": 120
                },
                {
                    "name": "6 недель подряд",
                    "description": "6 недель тренировок подряд",
                    "category": "Непрерывные недели",
                    "subcategory": "Выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 6 недель подряд",
                    "icon": "🔄",
                    "points": 140
                },
                {
                    "name": "7 недель подряд",
                    "description": "7 недель тренировок подряд",
                    "category": "Непрерывные недели",
                    "subcategory": "Выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 7 недель подряд",
                    "icon": "🔄",
                    "points": 160
                },
                
                # Достижения за непрерывные месяцы
                {
                    "name": "2 месяца подряд",
                    "description": "2 месяца тренировок подряд",
                    "category": "Непрерывные месяцы",
                    "subcategory": "Долгосрочная выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 2 месяца подряд",
                    "icon": "📆",
                    "points": 200
                },
                {
                    "name": "3 месяца подряд",
                    "description": "3 месяца тренировок подряд",
                    "category": "Непрерывные месяцы",
                    "subcategory": "Долгосрочная выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 3 месяца подряд",
                    "icon": "📆",
                    "points": 250
                },
                {
                    "name": "4 месяца подряд",
                    "description": "4 месяца тренировок подряд",
                    "category": "Непрерывные месяцы",
                    "subcategory": "Долгосрочная выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 4 месяца подряд",
                    "icon": "📆",
                    "points": 300
                },
                {
                    "name": "5 месяцев подряд",
                    "description": "5 месяцев тренировок подряд",
                    "category": "Непрерывные месяцы",
                    "subcategory": "Долгосрочная выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 5 месяцев подряд",
                    "icon": "📆",
                    "points": 350
                },
                {
                    "name": "6 месяцев подряд",
                    "description": "6 месяцев тренировок подряд",
                    "category": "Непрерывные месяцы",
                    "subcategory": "Долгосрочная выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 6 месяцев подряд",
                    "icon": "📆",
                    "points": 400
                },
                {
                    "name": "7 месяцев подряд",
                    "description": "7 месяцев тренировок подряд",
                    "category": "Непрерывные месяцы",
                    "subcategory": "Долгосрочная выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 7 месяцев подряд",
                    "icon": "📆",
                    "points": 450
                },
                {
                    "name": "8 месяцев подряд",
                    "description": "8 месяцев тренировок подряд",
                    "category": "Непрерывные месяцы",
                    "subcategory": "Долгосрочная выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 8 месяцев подряд",
                    "icon": "📆",
                    "points": 500
                },
                {
                    "name": "9 месяцев подряд",
                    "description": "9 месяцев тренировок подряд",
                    "category": "Непрерывные месяцы",
                    "subcategory": "Долгосрочная выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 9 месяцев подряд",
                    "icon": "📆",
                    "points": 550
                },
                {
                    "name": "10 месяцев подряд",
                    "description": "10 месяцев тренировок подряд",
                    "category": "Непрерывные месяцы",
                    "subcategory": "Долгосрочная выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 10 месяцев подряд",
                    "icon": "📆",
                    "points": 600
                },
                {
                    "name": "11 месяцев подряд",
                    "description": "11 месяцев тренировок подряд",
                    "category": "Непрерывные месяцы",
                    "subcategory": "Долгосрочная выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю 11 месяцев подряд",
                    "icon": "📆",
                    "points": 650
                },
                
                # Достижения за длительные периоды
                {
                    "name": "1 год без перерывов",
                    "description": "1 год тренировок без перерывов",
                    "category": "Долгосрочные",
                    "subcategory": "Годовая выносливость",
                    "requirements": "Выполнить минимум 1 тренировку в неделю в течение года",
                    "icon": "⏰",
                    "points": 1000
                },
                
                # Специальные достижения
                {
                    "name": "Мощь и сила",
                    "description": "За выполнение силовых упражнений",
                    "category": "Специальные",
                    "subcategory": "Сила",
                    "requirements": "Завершить полную программу силовых тренировок",
                    "icon": "⭐",
                    "points": 300
                }
            ]
            
            # 4. Вставляем все типы достижений
            print(f"\n📝 Вставляем {len(achievement_types)} типов достижений...")
            
            insert_query = text("""
                INSERT INTO achievement_types (
                    name, description, category, subcategory, requirements, icon, points
                ) VALUES (
                    :name, :description, :category, :subcategory, :requirements, :icon, :points
                ) ON CONFLICT (name) DO UPDATE SET
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    subcategory = EXCLUDED.subcategory,
                    requirements = EXCLUDED.requirements,
                    icon = EXCLUDED.icon,
                    points = EXCLUDED.points,
                    updated_at = NOW();
            """)
            
            inserted_count = 0
            for achievement_type in achievement_types:
                try:
                    await session.execute(insert_query, achievement_type)
                    inserted_count += 1
                    print(f"   ✅ {achievement_type['name']}")
                except Exception as e:
                    print(f"   ❌ {achievement_type['name']}: {e}")
            
            # 5. Коммитим изменения
            await session.commit()
            print(f"\n🎉 Успешно вставлено {inserted_count} типов достижений!")
            
            # 6. Показываем результат
            print("\n📊 ПРОВЕРЯЕМ РЕЗУЛЬТАТ:")
            print("-" * 40)
            
            # Подсчитываем общее количество
            count_query = text("SELECT COUNT(*) FROM achievement_types")
            result = await session.execute(count_query)
            total_count = result.scalar()
            print(f"Всего типов достижений в таблице: {total_count}")
            
            # Статистика по категориям
            category_stats_query = text("""
                SELECT category, COUNT(*) as count
                FROM achievement_types 
                GROUP BY category 
                ORDER BY count DESC
            """)
            result = await session.execute(category_stats_query)
            category_stats = result.fetchall()
            
            print(f"\n📈 Статистика по категориям:")
            for stat in category_stats:
                print(f"   • {stat[0]}: {stat[1]} типов")
            
            # Показываем несколько примеров
            sample_query = text("""
                SELECT name, category, subcategory, points, icon
                FROM achievement_types 
                ORDER BY points DESC 
                LIMIT 5
            """)
            result = await session.execute(sample_query)
            samples = result.fetchall()
            
            print(f"\n🏆 Топ-5 достижений по очкам:")
            for i, sample in enumerate(samples, 1):
                print(f"   {i}. {sample[4]} {sample[0]} ({sample[1]} - {sample[2]}) - {sample[3]} очков")
            
            print(f"\n🎯 Теперь вы можете:")
            print("   1. Просмотреть таблицу: SELECT * FROM achievement_types;")
            print("   2. Найти по категории: SELECT * FROM achievement_types WHERE category = 'Временные';")
            print("   3. Найти по очкам: SELECT * FROM achievement_types WHERE points >= 100;")
            print("   4. Создать скрипт для просмотра: python view_achievement_types.py")
            
        except Exception as e:
            print(f"❌ Ошибка при создании таблицы типов достижений: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(create_achievement_types_table())
