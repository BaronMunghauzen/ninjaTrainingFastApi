# 🏆 Система Достижений - Руководство пользователя

## 📋 Обзор

Система достижений автоматически отслеживает прогресс пользователей и выдает достижения за различные активности в приложении для тренировок.

## 🗄️ Структура базы данных

### Таблица `achievements`

```sql
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    uuid UUID NOT NULL UNIQUE,
    name VARCHAR NOT NULL,                    -- Название достижения
    user_id INTEGER NOT NULL,                -- ID пользователя
    status VARCHAR NOT NULL,                 -- Статус (active, inactive)
    user_training_id INTEGER,                -- Связь с тренировкой
    user_program_id INTEGER,                 -- Связь с программой пользователя
    program_id INTEGER,                      -- Связь с программой
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

## 🎯 Типы достижений

### 1. Временные достижения (2 типа)
- **Ранняя пташка** - 5 тренировок с 5 до 8 утра
- **Сова** - 5 тренировок с 21 до 00 (полночь)

### 2. Праздничные достижения (3 типа)
- **С Новым годом {год}** - тренировка в новогоднюю ночь
- **Международный женский день {год}** - тренировка 8 марта  
- **Мужской день {год}** - тренировка 23 февраля

### 3. Достижения за количество тренировок (13 типов)
- 1, 3, 5, 7, 10, 15, 20, 25, 30, 40, 50, 75, 100 тренировок

### 4. Достижения за тренировки в неделю (5 типов)
- 3, 4, 5, 6, 7 раза в неделю

### 5. Достижения за непрерывные недели (6 типов)
- 2, 3, 4, 5, 6, 7 недели подряд

### 6. Достижения за непрерывные месяцы (10 типов)
- 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 месяцев подряд

### 7. Достижения за длительные периоды (1 тип)
- **1 год без перерывов** - минимум 1 тренировка в неделю в течение года

### 8. Специальные достижения (1 тип)
- **Мощь и сила** - за выполнение силовых упражнений

**Всего: 47 типов достижений**

## 🚀 Как увидеть таблицу в базе данных

### Вариант 1: Через готовые скрипты (рекомендуется)

#### 1. Создать тестовое достижение
```bash
python create_test_achievement.py
```

#### 2. Просмотреть таблицу через SQL
```bash
python view_achievements_sql.py
```

#### 3. Проверить общее состояние
```bash
python check_achievements.py
```

#### 4. Создать демонстрационные достижения
```bash
python demo_achievements.py
```

### Вариант 2: Через прямые SQL запросы

#### Подключиться к базе данных
```bash
# Если используете psql
psql -h localhost -U your_username -d your_database

# Если используете Docker
docker exec -it your_postgres_container psql -U your_username -d your_database
```

#### Просмотреть структуру таблицы
```sql
-- Показать структуру
\d achievements

-- Или через information_schema
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'achievements' 
ORDER BY ordinal_position;
```

#### Просмотреть содержимое
```sql
-- Количество записей
SELECT COUNT(*) FROM achievements;

-- Все записи
SELECT * FROM achievements ORDER BY created_at DESC;

-- Достижения конкретного пользователя
SELECT * FROM achievements WHERE user_id = 1;

-- Статистика по статусам
SELECT status, COUNT(*) as count 
FROM achievements 
GROUP BY status;
```

#### Создать тестовое достижение
```sql
INSERT INTO achievements (uuid, name, user_id, status, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'Тестовое достижение',
    1,
    'active',
    NOW(),
    NOW()
);
```

### Вариант 3: Через графические инструменты

#### pgAdmin
1. Откройте pgAdmin
2. Подключитесь к вашей базе данных
3. В левом дереве найдите: Databases → your_database → Schemas → public → Tables → achievements
4. Правый клик на таблице → View/Edit Data → All Rows

#### DBeaver
1. Откройте DBeaver
2. Подключитесь к вашей базе данных
3. В левом дереве найдите: your_database → Schemas → public → Tables → achievements
4. Двойной клик на таблице для просмотра данных

#### DataGrip
1. Откройте DataGrip
2. Подключитесь к вашей базе данных
3. В левом дереве найдите: your_database → public → achievements
4. Двойной клик на таблице для просмотра данных

## 🔧 API эндпоинты

### Получить все достижения
```bash
GET /achievements/
```

### Получить достижение по UUID
```bash
GET /achievements/{achievement_uuid}
```

### Получить достижения пользователя
```bash
GET /achievements/user/{user_uuid}/achievements
```

### Создать достижение
```bash
POST /achievements/
```

### Обновить достижение
```bash
PUT /achievements/{achievement_uuid}
```

### Удалить достижение
```bash
DELETE /achievements/{achievement_uuid}
```

### Проверить конкретные достижения
```bash
POST /achievements/check-early-bird/{user_uuid}
POST /achievements/check-night-owl/{user_uuid}
POST /achievements/check-new-year/{user_uuid}
POST /achievements/check-womens-day/{user_uuid}
POST /achievements/check-mens-day/{user_uuid}
POST /achievements/check-power-and-strength/{user_uuid}
POST /achievements/check-training-count/{user_uuid}
POST /achievements/check-weekly-training/{user_uuid}
POST /achievements/check-consecutive-weeks/{user_uuid}
POST /achievements/check-consecutive-months/{user_uuid}
POST /achievements/check-year-without-breaks/{user_uuid}
POST /achievements/check-all/{user_uuid}
```

## 📊 Примеры данных

### Структура записи достижения
```json
{
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Ранняя пташка",
    "user_id": 1,
    "status": "active",
    "user_training_id": 5,
    "user_program_id": 2,
    "program_id": 1,
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T10:30:00"
}
```

## 🎯 Логика выдачи достижений

1. **Автоматическая проверка** - система проверяет условия при каждой тренировке
2. **Уникальность** - каждое достижение выдается только один раз
3. **Привязка к тренировкам** - достижения связаны с конкретными тренировками
4. **Статусы** - достижения могут быть активными или неактивными

## 🔍 Отладка и мониторинг

### Проверить состояние системы
```bash
python check_all_tables.py
```

### Просмотреть логи
```bash
# В FastAPI приложении
uvicorn app.main:app --reload --log-level debug
```

### Мониторинг производительности
```bash
# Проверить индексы
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'achievements';

# Проверить статистику
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables 
WHERE tablename = 'achievements';
```

## 🚨 Устранение неполадок

### Таблица не существует
```bash
# Проверить миграции
alembic current
alembic upgrade head
```

### Ошибки подключения
```bash
# Проверить настройки базы данных
python -c "from app.database import engine; print(engine.url)"
```

### Пустая таблица
```bash
# Создать тестовые данные
python create_test_achievement.py
```

## 📚 Дополнительные ресурсы

- [Документация SQLAlchemy](https://docs.sqlalchemy.org/)
- [Документация PostgreSQL](https://www.postgresql.org/docs/)
- [Документация FastAPI](https://fastapi.tiangolo.com/)
- [Документация Alembic](https://alembic.sqlalchemy.org/)

## 🤝 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте логи приложения
2. Убедитесь, что база данных запущена
3. Проверьте настройки подключения
4. Запустите диагностические скрипты

---

**Удачного использования системы достижений! 🎉**





