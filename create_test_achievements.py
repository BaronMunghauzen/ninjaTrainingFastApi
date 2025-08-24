import asyncio
from app.database import async_session_maker
from app.achievements.service import AchievementService
from sqlalchemy import text

async def create_test_achievements():
    """Создает тестовые достижения с реальными данными из базы"""
    print("🎯 Создание тестовых достижений")
    print("=" * 50)
    
    async with async_session_maker() as session:
        # Получаем пользователя с тренировками
        user_query = text("""
            SELECT u.id, u.uuid, u.first_name, u.last_name, 
                   COUNT(ut.id) as total_trainings,
                   COUNT(CASE WHEN ut.status = 'PASSED' THEN 1 END) as completed_trainings
            FROM "user" u
            LEFT JOIN user_training ut ON u.id = ut.user_id
            GROUP BY u.id, u.uuid, u.first_name, u.last_name
            HAVING COUNT(ut.id) > 0
            ORDER BY COUNT(ut.id) DESC
            LIMIT 1
        """)
        result = await session.execute(user_query)
        user = result.fetchone()
        
        if not user:
            print("❌ Пользователи с тренировками не найдены в базе")
            return
        
        user_id, user_uuid, first_name, last_name, total_trainings, completed_trainings = user
        print(f"👤 Пользователь: {first_name or 'Без имени'} {last_name or 'Без фамилии'} (ID: {user_id}, UUID: {user_uuid})")
        print(f"📊 Тренировки: всего {total_trainings}, завершено {completed_trainings}")
        
        # Получаем несколько завершенных тренировок для анализа
        completed_trainings_query = text("""
            SELECT id, uuid, training_date, completed_at, status
            FROM user_training 
            WHERE user_id = :user_id AND status = 'PASSED'
            ORDER BY completed_at DESC
            LIMIT 5
        """)
        result = await session.execute(completed_trainings_query, {"user_id": user_id})
        completed_trainings_list = result.fetchall()
        
        print(f"\n📅 Последние завершенные тренировки:")
        for i, training in enumerate(completed_trainings_list, 1):
            training_id, training_uuid, training_date, completed_at, status = training
            print(f"  {i}. ID: {training_id}, Дата: {training_date}, Завершена: {completed_at}")
        
        print(f"\n🔍 Проверяем достижения для пользователя {user_uuid}...")
        
        try:
            # Проверяем достижения за количество тренировок
            print("\n📊 Проверяем достижения за количество тренировок...")
            training_count_achievements = await AchievementService.check_training_count_achievements(str(user_uuid))
            
            if training_count_achievements:
                print(f"✅ Выдано {len(training_count_achievements)} достижений за количество тренировок!")
                for ach in training_count_achievements:
                    print(f"   🏆 {ach.name}")
            else:
                print("❌ Достижения за количество тренировок не найдены")
            
            # Проверяем достижения за тренировки в неделю
            print("\n📅 Проверяем достижения за тренировки в неделю...")
            weekly_achievements = await AchievementService.check_weekly_training_achievements(str(user_uuid))
            
            if weekly_achievements:
                print(f"✅ Выдано {len(weekly_achievements)} достижений за тренировки в неделю!")
                for ach in weekly_achievements:
                    print(f"   📅 {ach.name}")
            else:
                print("❌ Достижения за тренировки в неделю не найдены")
            
            # Проверяем достижения за непрерывные недели
            print("\n🔗 Проверяем достижения за непрерывные недели...")
            consecutive_weeks_achievements = await AchievementService.check_consecutive_weeks_achievements(str(user_uuid))
            
            if consecutive_weeks_achievements:
                print(f"✅ Выдано {len(consecutive_weeks_achievements)} достижений за непрерывные недели!")
                for ach in consecutive_weeks_achievements:
                    print(f"   🔗 {ach.name}")
            else:
                print("❌ Достижения за непрерывные недели не найдены")
            
            # Проверяем достижения за непрерывные месяцы
            print("\n📆 Проверяем достижения за непрерывные месяцы...")
            consecutive_months_achievements = await AchievementService.check_consecutive_months_achievements(str(user_uuid))
            
            if consecutive_months_achievements:
                print(f"✅ Выдано {len(consecutive_months_achievements)} достижений за непрерывные месяцы!")
                for ach in consecutive_months_achievements:
                    print(f"   📆 {ach.name}")
            else:
                print("❌ Достижения за непрерывные месяцы не найдены")
            
            # Проверяем все достижения сразу
            print("\n🎯 Проверяем все возможные достижения...")
            all_achievements = await AchievementService.check_all_achievements_for_user(str(user_uuid))
            
            if all_achievements:
                print(f"✅ Всего выдано {len(all_achievements)} новых достижений!")
                for ach in all_achievements:
                    print(f"   🏆 {ach.name}")
            else:
                print("❌ Новых достижений не найдено")
            
        except Exception as e:
            print(f"❌ Ошибка при проверке достижений: {e}")
            import traceback
            traceback.print_exc()
        
        # Показываем итоговое количество достижений
        print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        print("-" * 30)
        
        achievements_count_query = text("SELECT COUNT(*) FROM achievements WHERE user_id = :user_id")
        result = await session.execute(achievements_count_query, {"user_id": user_id})
        achievements_count = result.scalar()
        print(f"Достижений у пользователя: {achievements_count}")
        
        if achievements_count > 0:
            print(f"\n🏆 Все достижения пользователя:")
            achievements_query = text("""
                SELECT name, status, created_at
                FROM achievements 
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """)
            result = await session.execute(achievements_query, {"user_id": user_id})
            achievements = result.fetchall()
            
            for ach in achievements:
                name, status, created_at = ach
                print(f"   🏆 {name} (статус: {status}, создано: {created_at})")

if __name__ == "__main__":
    asyncio.run(create_test_achievements())
