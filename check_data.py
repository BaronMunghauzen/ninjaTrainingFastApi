import asyncio
from app.database import async_session_maker
from sqlalchemy import text

async def check_data():
    """Проверяет наличие данных в связанных таблицах"""
    async with async_session_maker() as session:
        print("Проверка данных в связанных таблицах:")
        print("=" * 50)
        
        # Проверяем пользователей
        users_query = text("SELECT COUNT(*) FROM \"user\"")
        result = await session.execute(users_query)
        users_count = result.scalar()
        print(f"Пользователей: {users_count}")
        
        if users_count > 0:
            # Показываем первого пользователя
            user_query = text('SELECT id, uuid, name FROM "user" LIMIT 1')
            result = await session.execute(user_query)
            user = result.fetchone()
            if user:
                print(f"  Первый пользователь: ID={user[0]}, UUID={user[1]}, Name={user[2]}")
        
        # Проверяем программы
        programs_query = text("SELECT COUNT(*) FROM program")
        result = await session.execute(programs_query)
        programs_count = result.scalar()
        print(f"Программ: {programs_count}")
        
        if programs_count > 0:
            # Показываем первую программу
            program_query = text("SELECT id, uuid, name FROM program LIMIT 1")
            result = await session.execute(program_query)
            program = result.fetchone()
            if program:
                print(f"  Первая программа: ID={program[0]}, UUID={program[1]}, Name={program[2]}")
        
        # Проверяем user_program
        user_programs_query = text("SELECT COUNT(*) FROM user_program")
        result = await session.execute(user_programs_query)
        user_programs_count = result.scalar()
        print(f"User Programs: {user_programs_count}")
        
        if user_programs_count > 0:
            # Показываем первый user_program
            up_query = text("SELECT id, uuid, user_id, program_id FROM user_program LIMIT 1")
            result = await session.execute(up_query)
            up = result.fetchone()
            if up:
                print(f"  Первый User Program: ID={up[0]}, UUID={up[1]}, User ID={up[2]}, Program ID={up[3]}")
        
        # Проверяем user_training
        user_trainings_query = text("SELECT COUNT(*) FROM user_training")
        result = await session.execute(user_trainings_query)
        user_trainings_count = result.scalar()
        print(f"User Trainings: {user_trainings_count}")
        
        if user_trainings_count > 0:
            # Показываем первые тренировки
            ut_query = text("SELECT id, uuid, user_id, user_program_id, status, completed_at FROM user_training LIMIT 3")
            result = await session.execute(ut_query)
            trainings = result.fetchall()
            print(f"  Первые тренировки:")
            for i, training in enumerate(trainings, 1):
                print(f"    {i}. ID={training[0]}, UUID={training[1]}, User ID={training[2]}, Status={training[4]}, Completed={training[5]}")
        
        print("\n" + "=" * 50)
        print("Рекомендации:")
        if users_count == 0:
            print("❌ Нет пользователей - нужно создать хотя бы одного пользователя")
        if programs_count == 0:
            print("❌ Нет программ - нужно создать хотя бы одну программу")
        if user_programs_count == 0:
            print("❌ Нет user_program - нужно связать пользователя с программой")
        if user_trainings_count == 0:
            print("❌ Нет тренировок - нужно создать тренировки для тестирования достижений")
        
        if users_count > 0 and programs_count > 0 and user_programs_count > 0 and user_trainings_count > 0:
            print("✅ Все необходимые данные есть - можно создавать достижения")

if __name__ == "__main__":
    asyncio.run(check_data())
