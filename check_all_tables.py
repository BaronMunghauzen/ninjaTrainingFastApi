import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session_maker
from sqlalchemy import text

async def check_all_tables():
    """Проверяет все таблицы в базе данных"""
    async with async_session_maker() as session:
        try:
            # Получаем список всех таблиц
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            result = await session.execute(tables_query)
            tables = result.fetchall()
            
            print("📋 ВСЕ ТАБЛИЦЫ В БАЗЕ ДАННЫХ:")
            print("=" * 60)
            
            for table in tables:
                table_name = table[0]
                print(f"\n📊 Таблица: {table_name}")
                print("-" * 40)
                
                # Получаем количество записей в таблице
                try:
                    count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                    result = await session.execute(count_query)
                    count = result.scalar()
                    print(f"Количество записей: {count}")
                    
                    # Если есть записи, показываем структуру
                    if count > 0:
                        # Получаем структуру таблицы
                        structure_query = text(f"""
                            SELECT column_name, data_type, is_nullable, column_default
                            FROM information_schema.columns 
                            WHERE table_name = '{table_name}' 
                            ORDER BY ordinal_position
                        """)
                        result = await session.execute(structure_query)
                        columns = result.fetchall()
                        
                        print("Структура:")
                        for col in columns:
                            nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                            default = f" DEFAULT {col[3]}" if col[3] else ""
                            print(f"  • {col[0]}: {col[1]} {nullable}{default}")
                        
                        # Показываем несколько примеров записей
                        if count <= 5:
                            sample_query = text(f"SELECT * FROM {table_name} LIMIT 3")
                            result = await session.execute(sample_query)
                            samples = result.fetchall()
                            
                            print("Примеры записей:")
                            for i, sample in enumerate(samples, 1):
                                print(f"  {i}. {sample}")
                        else:
                            print("Примеры записей: (слишком много для показа)")
                            
                except Exception as e:
                    print(f"Ошибка при проверке таблицы {table_name}: {e}")
                
                print()
                
        except Exception as e:
            print(f"❌ Ошибка при проверке таблиц: {e}")

if __name__ == "__main__":
    asyncio.run(check_all_tables())
