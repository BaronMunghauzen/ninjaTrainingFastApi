import asyncio
from app.database import async_session_maker
from sqlalchemy import text

async def check_table_structure():
    """Проверяет структуру таблицы achievements"""
    async with async_session_maker() as session:
        # Проверяем существование таблицы
        check_table_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'achievements'
        """)
        
        result = await session.execute(check_table_query)
        table_exists = result.scalar()
        
        if table_exists:
            print("✅ Таблица 'achievements' существует в базе данных")
            
            # Получаем структуру таблицы
            structure_query = text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'achievements'
                ORDER BY ordinal_position
            """)
            
            result = await session.execute(structure_query)
            columns = result.fetchall()
            
            print("\nСтруктура таблицы 'achievements':")
            print("-" * 80)
            print(f"{'Колонка':<20} {'Тип данных':<15} {'NULL':<8} {'Значение по умолчанию'}")
            print("-" * 80)
            
            for col in columns:
                column_name, data_type, is_nullable, column_default = col
                nullable = "YES" if is_nullable == "YES" else "NO"
                default = column_default if column_default else "NULL"
                print(f"{column_name:<20} {data_type:<15} {nullable:<8} {default}")
            
            # Проверяем количество записей
            count_query = text("SELECT COUNT(*) FROM achievements")
            result = await session.execute(count_query)
            count = result.scalar()
            
            print(f"\nКоличество записей в таблице: {count}")
            
            # Проверяем внешние ключи
            fk_query = text("""
                SELECT 
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name = 'achievements'
            """)
            
            result = await session.execute(fk_query)
            foreign_keys = result.fetchall()
            
            if foreign_keys:
                print("\nВнешние ключи:")
                print("-" * 40)
                for fk in foreign_keys:
                    constraint_name, table_name, column_name, foreign_table, foreign_column = fk
                    print(f"  {column_name} -> {foreign_table}.{foreign_column}")
            else:
                print("\nВнешние ключи не найдены")
                
        else:
            print("❌ Таблица 'achievements' не найдена в базе данных")

if __name__ == "__main__":
    asyncio.run(check_table_structure())
