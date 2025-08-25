from functools import lru_cache
from uuid import UUID
from typing import Optional

from asyncpg import UniqueViolationError
from fastapi import status, HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, inspect, UniqueConstraint, delete
from app.database import async_session_maker
from app.exceptions import CategotyNotFoundException


class BaseDAO:
    model = None
    uuid_fk_map = {}  # {'category_id': (CategoryDAO, 'category_uuid'), ...}

    @classmethod
    async def find_all(cls, **filter_by):
        filters = filter_by.copy()
        # Универсальная обработка uuid для связанных моделей
        for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                # Если uuid_value не None, то ищем связанный объект
                if uuid_value is not None:
                    related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                    if related_obj:
                        filters[fk_field] = related_obj.id
                    else:
                        return []
                # Если uuid_value None, то не добавляем фильтр (позволяет искать записи без связанного объекта)
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filters)
            
            # Добавляем сортировку по полю order, если оно существует в модели
            if hasattr(cls.model, 'order'):
                query = query.order_by(cls.model.order.asc())
            
            result = await session.execute(query)
            objects = result.scalars().all()
            return objects

    @classmethod
    async def find_in(cls, field: str, values: list):
        """Универсальный метод для поиска по списку значений с оператором IN"""
        if not values:
            return []
        async with async_session_maker() as session:
            model_field = getattr(cls.model, field)
            query = select(cls.model).where(model_field.in_(values))
            
            # Добавляем сортировку по полю order, если оно существует в модели
            if hasattr(cls.model, 'order'):
                query = query.order_by(cls.model.order.asc())
            
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def find_full_data(cls, object_uuid: UUID):
        print(f"find_full_data: Начинаем поиск {cls.model.__name__} с UUID {object_uuid}")
        async with async_session_maker() as session:
            print(f"find_full_data: Сессия создана")
            query = select(cls.model).filter_by(uuid=object_uuid)
            print(f"find_full_data: Запрос создан")
            result = await session.execute(query)
            print(f"find_full_data: Запрос выполнен")
            object_info = result.scalar_one_or_none()
            print(f"find_full_data: Результат получен: {object_info}")

            # Если объект не найден, возвращаем None
            if not object_info:
                print(f"find_full_data: Объект не найден")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Объект {cls.model.__name__} с ID {object_uuid} не найден"
                )
            print(f"find_full_data: Объект найден, возвращаем")
            return object_info

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @classmethod
    async def find_by_uuid(cls, uuid: str):
        """Поиск объекта по UUID"""
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(uuid=uuid)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    @lru_cache
    def _get_unique_columns(cls):
        """Возвращает список уникальных колонок модели"""
        print(f"_get_unique_columns: Начинаем поиск уникальных колонок для {cls.model.__name__}")
        mapper = inspect(cls.model)
        unique_columns = set()

        # Получаем таблицу из маппера
        table = mapper.persist_selectable
        print(f"_get_unique_columns: Таблица получена: {table.name}")

        # 1. Проверяем ограничения уровня таблицы
        print(f"_get_unique_columns: Проверяем ограничения таблицы...")
        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraint):
                print(f"_get_unique_columns: Найдено ограничение уникальности: {constraint}")
                for col in constraint.columns:
                    unique_columns.add(col.name)
                    print(f"_get_unique_columns: Добавлена колонка: {col.name}")

        # 2. Проверяем колонки с unique=True
        print(f"_get_unique_columns: Проверяем колонки с unique=True...")
        for column in table.columns:
            if column.unique and not column.foreign_keys:
                unique_columns.add(column.name)
                print(f"_get_unique_columns: Добавлена уникальная колонка: {column.name}")

        result = list(unique_columns)
        print(f"_get_unique_columns: Результат: {result}")
        return result

    @classmethod
    async def _check_uniqueness(cls, session: AsyncSession, values: dict, exclude_uuid: Optional[UUID] = None):
        """Предварительная проверка уникальных полей"""
        print(f"_check_uniqueness: Начинаем проверку уникальности для {cls.model.__name__}")
        unique_columns = cls._get_unique_columns()
        print(f"_check_uniqueness: Уникальные колонки: {unique_columns}")
        print(f"_check_uniqueness: Проверяемые значения: {list(values.keys())}")
        
        for col in unique_columns:
            if col in values:
                print(f"_check_uniqueness: Проверяем колонку {col} со значением {values[col]}")
                query = select(cls.model).where(
                    getattr(cls.model, col) == values[col]
                )
                if exclude_uuid:
                    query = query.where(cls.model.uuid != exclude_uuid)
                    print(f"_check_uniqueness: Исключаем UUID {exclude_uuid}")
                
                print(f"_check_uniqueness: Выполняем запрос...")
                exists = await session.execute(query)
                print(f"_check_uniqueness: Запрос выполнен")
                
                if exists.scalar():
                    print(f"_check_uniqueness: Найдено дублирование для {col}")
                    raise ValueError(f"Объект с {col}='{values[col]}' уже существует")
                else:
                    print(f"_check_uniqueness: Уникальность для {col} подтверждена")
        
        print(f"_check_uniqueness: Проверка уникальности завершена")

    @classmethod
    def _parse_db_error(cls, error):
        """Анализирует ошибку БД и возвращает понятное сообщение"""
        orig = getattr(error, 'orig', None)
        msg = str(orig) if orig else str(error)
        
        # Ошибка уникальности
        if isinstance(orig, UniqueViolationError):
            import re
            m = re.search(r'duplicate key value violates unique constraint "([^"]+)"', msg)
            if m:
                return f"Запись с такими данными уже существует (ограничение: {m.group(1)})"
            return "Запись с такими данными уже существует"
        
        # Ошибка NOT NULL
        if 'null value in column' in msg and 'violates not-null constraint' in msg:
            import re
            m = re.search(r'null value in column "([^"]+)"', msg)
            if m:
                return f"Поле '{m.group(1)}' обязательно для заполнения"
            return "Не указано обязательное поле"
        
        # Ошибка внешнего ключа
        if 'violates foreign key constraint' in msg:
            import re
            m = re.search(r'Key \(([^)]+)\)=\([^)]+\) is not present in table', msg)
            if m:
                return f"Некорректное значение внешнего ключа для поля '{m.group(1)}'"
            return "Некорректное значение внешнего ключа"
        
        # Ошибка JSON
        if 'invalid input syntax for type json' in msg:
            return "Некорректный формат JSON данных"
        
        # Ошибка типа данных
        if 'invalid input syntax for type' in msg:
            import re
            m = re.search(r'invalid input syntax for type ([^:]+)', msg)
            if m:
                return f"Некорректный формат данных для типа {m.group(1)}"
            return "Некорректный формат данных"
        
        # Ошибка длины строки
        if 'value too long for type' in msg:
            import re
            m = re.search(r'value too long for type ([^(]+)\(([^)]+)\)', msg)
            if m:
                return f"Значение слишком длинное для поля типа {m.group(1)}({m.group(2)})"
            return "Значение слишком длинное"
        
        # Ошибка диапазона
        if 'numeric field overflow' in msg:
            return "Числовое значение слишком большое"
        
        # Ошибка UUID
        if 'invalid input syntax for uuid' in msg:
            return "Некорректный формат UUID"
        
        # Ошибка подключения к БД
        if 'connection' in msg.lower() and ('failed' in msg.lower() or 'refused' in msg.lower()):
            return "Ошибка подключения к базе данных"
        
        # Ошибка транзакции
        if 'transaction' in msg.lower():
            return "Ошибка транзакции базы данных"
        
        # Общая ошибка SQL
        if 'syntax error' in msg.lower():
            return "Ошибка синтаксиса SQL"
        
        # Если ничего не подошло, возвращаем оригинальное сообщение
        return msg

    @classmethod
    async def add(cls, **values):
        print(f"add: Начинаем добавление {cls.model.__name__} с данными: {values}")
        async with async_session_maker() as session:
            try:
                async with session.begin():
                    print(f"add: Транзакция начата")
                    prepared_values = {}
                    
                    # Обрабатываем uuid_fk_map для связанных моделей
                    for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
                        if uuid_field in values:
                            uuid_value = values.pop(uuid_field)
                            # Если uuid_value не None, то ищем связанный объект
                            if uuid_value is not None:
                                related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                                if related_obj:
                                    prepared_values[fk_field] = related_obj.id
                                else:
                                    raise ValueError(f"Связанный объект {uuid_field} с UUID {uuid_value} не найден")
                            # Если uuid_value None, то не добавляем поле (позволяет создавать записи без связанного объекта)
                    
                    # Обрабатываем остальные поля
                    for key, value in values.items():
                        if hasattr(value, 'id'):  # Если значение - объект модели
                            prepared_values[f"{key}_id"] = value.id
                        else:
                            prepared_values[key] = value
                    
                    print(f"add: Подготовленные значения: {prepared_values}")

                    # 2. Проверка уникальности перед вставкой
                    print(f"add: Проверяем уникальность...")
                    await cls._check_uniqueness(session, prepared_values, exclude_uuid=None)
                    print(f"add: Уникальность проверена")

                    # 3. Создание и сохранение объекта
                    print(f"add: Создаем экземпляр модели...")
                    new_instance = cls.model(**prepared_values)
                    print(f"add: Экземпляр создан: {new_instance}")
                    
                    print(f"add: Добавляем в сессию...")
                    session.add(new_instance)
                    print(f"add: Добавлено в сессию")
                    
                    print(f"add: Выполняем flush...")
                    await session.flush()
                    print(f"add: Flush выполнен")
                    
                    print(f"add: Обновляем объект...")
                    await session.refresh(new_instance)
                    print(f"add: Объект обновлен")
                    
                    print(f"add: Возвращаем UUID: {new_instance.uuid}")
                    return new_instance.uuid

            except IntegrityError as e:
                print(f"add: IntegrityError: {e}")
                await session.rollback()
                detail = cls._parse_db_error(e)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"message": "Ошибка при добавлении объекта", "detail": detail}
                )
            except (ValueError, KeyError) as e:
                print(f"add: ValueError/KeyError: {e}")
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": str(e)}
                )
            except SQLAlchemyError as e:
                print(f"add: SQLAlchemyError: {e}")
                await session.rollback()
                detail = cls._parse_db_error(e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"message": "Database error", "detail": detail}
                )


    @classmethod
    async def update(cls, object_uuid: UUID, **values):
        # Фильтруем None значения
        values = {k: v for k, v in values.items() if v is not None}
        if not values:  # Если ничего не передали для обновления
            return 0
        async with async_session_maker() as session:
            try:
                async with session.begin():
                    prepared_values = {}
                    
                    # Обрабатываем uuid_fk_map для связанных моделей
                    for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
                        if uuid_field in values:
                            uuid_value = values.pop(uuid_field)
                            # Если uuid_value не None, то ищем связанный объект
                            if uuid_value is not None:
                                related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                                if related_obj:
                                    prepared_values[fk_field] = related_obj.id
                                else:
                                    raise ValueError(f"Связанный объект {uuid_field} с UUID {uuid_value} не найден")
                            # Если uuid_value None, то устанавливаем поле в None
                            else:
                                prepared_values[fk_field] = None
                    
                    # Обрабатываем остальные поля
                    for key, value in values.items():
                        if hasattr(value, 'id'):  # Если значение - объект модели
                            prepared_values[f"{key}_id"] = value.id
                        else:
                            prepared_values[key] = value
                    
                    # Проверка уникальности полей (исключаем текущий объект)
                    await cls._check_uniqueness(session, prepared_values, exclude_uuid=object_uuid)

                    query = (
                        sqlalchemy_update(cls.model)
                        .where(cls.model.uuid == object_uuid)
                        .values(**prepared_values)
                        .execution_options(synchronize_session="fetch")
                    )
                    result = await session.execute(query)
                    try:
                        await session.commit()
                    except SQLAlchemyError as e:
                        await session.rollback()
                        raise e
                    return result.rowcount
            except IntegrityError as e:
                await session.rollback()
                detail = cls._parse_db_error(e)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"message": "Ошибка при обновлении объекта", "detail": detail}
                )
            except (ValueError, KeyError) as e:
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": str(e)}
                )
            except SQLAlchemyError as e:
                await session.rollback()
                detail = cls._parse_db_error(e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"message": "Database error", "detail": detail}
                )

    @classmethod
    async def delete_by_id(cls, object_uuid: UUID):
        async with async_session_maker() as session:
            async with session.begin():
                query = select(cls.model).filter_by(uuid=object_uuid)
                result = await session.execute(query)
                object_to_delete = result.scalar_one_or_none()

                if not object_to_delete:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Объект {cls.model.__name__} с ID {object_uuid} не найден"
                    )


                await session.execute(
                    delete(cls.model).filter_by(uuid=object_uuid)
                )

                await session.commit()
                return object_uuid