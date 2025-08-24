# 🏆 Таблица Типов Достижений - Руководство пользователя

## 📋 Обзор

Таблица `achievement_types` содержит полный справочник всех возможных достижений в системе тренировок. Это централизованное место для управления типами достижений, их описаниями, требованиями и очками.

## 🗄️ Структура таблицы

### Таблица `achievement_types`

```sql
CREATE TABLE achievement_types (
    id SERIAL PRIMARY KEY,
    uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL UNIQUE,                    -- Название достижения
    description TEXT NOT NULL,                       -- Краткое описание
    category VARCHAR NOT NULL,                       -- Основная категория
    subcategory VARCHAR,                             -- Подкатегория
    requirements TEXT,                               -- Требования для получения
    icon VARCHAR,                                    -- Эмодзи иконка
    points INTEGER DEFAULT 0,                        -- Количество очков
    is_active BOOLEAN DEFAULT true,                  -- Активно ли достижение
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),     -- Дата создания
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()      -- Дата обновления
);
```

### Индексы для производительности

```sql
CREATE INDEX idx_achievement_types_category ON achievement_types(category);
CREATE INDEX idx_achievement_types_name ON achievement_types(name);
CREATE INDEX idx_achievement_types_active ON achievement_types(is_active);
```

## 🎯 Категории достижений

### 1. **Временные** (2 типа)
- **Ранняя пташка** - 5 тренировок с 5 до 8 утра (50 очков)
- **Сова** - 5 тренировок с 21 до 00 (50 очков)

### 2. **Праздничные** (3 типа)
- **С Новым годом** - тренировка 1 января (100 очков)
- **Международный женский день** - тренировка 8 марта (100 очков)
- **Мужской день** - тренировка 23 февраля (100 очков)

### 3. **Количество тренировок** (13 типов)
- **1 тренировка** - первая тренировка (10 очков)
- **3 тренировки** - третья тренировка (20 очков)
- **5 тренировок** - пятая тренировка (30 очков)
- **7 тренировок** - седьмая тренировка (40 очков)
- **10 тренировок** - десятая тренировка (50 очков)
- **15 тренировок** - пятнадцатая тренировка (60 очков)
- **20 тренировок** - двадцатая тренировка (70 очков)
- **25 тренировок** - двадцать пятая тренировка (80 очков)
- **30 тренировок** - тридцатая тренировка (90 очков)
- **40 тренировок** - сороковая тренировка (100 очков)
- **50 тренировок** - пятидесятая тренировка (120 очков)
- **75 тренировок** - семьдесят пятая тренировка (150 очков)
- **100 тренировок** - сотая тренировка (200 очков)

### 4. **Недельные** (5 типов)
- **3 раза в неделю** - 3 тренировки за неделю (40 очков)
- **4 раза в неделю** - 4 тренировки за неделю (50 очков)
- **5 раза в неделю** - 5 тренировок за неделю (60 очков)
- **6 раза в неделю** - 6 тренировок за неделю (70 очков)
- **7 раза в неделю** - 7 тренировок за неделю (80 очков)

### 5. **Непрерывные недели** (6 типов)
- **2 недели подряд** - минимум 1 тренировка в неделю 2 недели подряд (60 очков)
- **3 недели подряд** - минимум 1 тренировка в неделю 3 недели подряд (80 очков)
- **4 недели подряд** - минимум 1 тренировка в неделю 4 недели подряд (100 очков)
- **5 недель подряд** - минимум 1 тренировка в неделю 5 недель подряд (120 очков)
- **6 недель подряд** - минимум 1 тренировка в неделю 6 недель подряд (140 очков)
- **7 недель подряд** - минимум 1 тренировка в неделю 7 недель подряд (160 очков)

### 6. **Непрерывные месяцы** (10 типов)
- **2 месяца подряд** - минимум 1 тренировка в неделю 2 месяца подряд (200 очков)
- **3 месяца подряд** - минимум 1 тренировка в неделю 3 месяца подряд (250 очков)
- **4 месяца подряд** - минимум 1 тренировка в неделю 4 месяца подряд (300 очков)
- **5 месяцев подряд** - минимум 1 тренировка в неделю 5 месяцев подряд (350 очков)
- **6 месяцев подряд** - минимум 1 тренировка в неделю 6 месяцев подряд (400 очков)
- **7 месяцев подряд** - минимум 1 тренировка в неделю 7 месяцев подряд (450 очков)
- **8 месяцев подряд** - минимум 1 тренировка в неделю 8 месяцев подряд (500 очков)
- **9 месяцев подряд** - минимум 1 тренировка в неделю 9 месяцев подряд (550 очков)
- **10 месяцев подряд** - минимум 1 тренировка в неделю 10 месяцев подряд (600 очков)
- **11 месяцев подряд** - минимум 1 тренировка в неделю 11 месяцев подряд (650 очков)

### 7. **Долгосрочные** (1 тип)
- **1 год без перерывов** - минимум 1 тренировка в неделю в течение года (1000 очков)

### 8. **Специальные** (1 тип)
- **Мощь и сила** - за выполнение силовых упражнений (300 очков)

**Всего: 41 тип достижений**

## 🚀 Как работать с таблицей

### Вариант 1: Через готовые скрипты (рекомендуется)

#### 1. Создать таблицу и заполнить данными
```bash
python create_achievement_types_table.py
```

#### 2. Просмотреть таблицу детально
```bash
python view_achievement_types.py
```

#### 3. Быстрый просмотр
```bash
python quick_view_achievement_types.py
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
\d achievement_types

-- Или через information_schema
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'achievement_types' 
ORDER BY ordinal_position;
```

#### Просмотреть содержимое
```sql
-- Количество записей
SELECT COUNT(*) FROM achievement_types;

-- Все записи
SELECT * FROM achievement_types ORDER BY category, points DESC;

-- Достижения определенной категории
SELECT * FROM achievement_types WHERE category = 'Временные';

-- Достижения с высокими очками
SELECT * FROM achievement_types WHERE points >= 100 ORDER BY points DESC;

-- Поиск по названию
SELECT * FROM achievement_types WHERE name ILIKE '%неделя%';
```

#### Статистика и аналитика
```sql
-- Статистика по категориям
SELECT 
    category, 
    COUNT(*) as count, 
    AVG(points) as avg_points, 
    SUM(points) as total_points
FROM achievement_types 
GROUP BY category 
ORDER BY total_points DESC;

-- Статистика по подкатегориям
SELECT 
    subcategory, 
    COUNT(*) as count, 
    AVG(points) as avg_points
FROM achievement_types 
WHERE subcategory IS NOT NULL
GROUP BY subcategory 
ORDER BY count DESC;

-- Общая статистика по очкам
SELECT 
    MIN(points) as min_points,
    MAX(points) as max_points,
    AVG(points) as avg_points,
    SUM(points) as total_points
FROM achievement_types;
```

## 🔧 Добавление новых типов достижений

### Через SQL
```sql
INSERT INTO achievement_types (
    name, 
    description, 
    category, 
    subcategory, 
    requirements, 
    icon, 
    points
) VALUES (
    'Новое достижение',
    'Описание нового достижения',
    'Новая категория',
    'Новая подкатегория',
    'Требования для получения',
    '🎯',
    150
);
```

### Через Python
```python
from app.database import async_session_maker
from sqlalchemy import text

async def add_new_achievement_type():
    async with async_session_maker() as session:
        insert_query = text("""
            INSERT INTO achievement_types (
                name, description, category, subcategory, 
                requirements, icon, points
            ) VALUES (
                :name, :description, :category, :subcategory,
                :requirements, :icon, :points
            )
        """)
        
        await session.execute(insert_query, {
            "name": "Новое достижение",
            "description": "Описание",
            "category": "Категория",
            "subcategory": "Подкатегория",
            "requirements": "Требования",
            "icon": "🎯",
            "points": 150
        })
        
        await session.commit()
```

## 📊 Примеры использования

### 1. Получить все достижения для отображения в UI
```sql
SELECT 
    name, description, category, subcategory, 
    requirements, icon, points
FROM achievement_types 
WHERE is_active = true
ORDER BY category, points DESC;
```

### 2. Найти достижения определенного уровня сложности
```sql
SELECT * FROM achievement_types 
WHERE subcategory IN ('Начальный уровень', 'Средний уровень')
ORDER BY points;
```

### 3. Получить достижения для конкретной категории
```sql
SELECT * FROM achievement_types 
WHERE category = 'Временные'
ORDER BY points DESC;
```

### 4. Поиск по ключевым словам
```sql
SELECT * FROM achievement_types 
WHERE LOWER(name) LIKE LOWER('%неделя%')
   OR LOWER(description) LIKE LOWER('%неделя%')
   OR LOWER(requirements) LIKE LOWER('%неделя%')
ORDER BY points DESC;
```

### 5. Статистика для администратора
```sql
-- Общая статистика
SELECT 
    COUNT(*) as total_types,
    COUNT(CASE WHEN is_active THEN 1 END) as active_types,
    SUM(points) as total_points,
    AVG(points) as avg_points
FROM achievement_types;

-- Распределение по категориям
SELECT 
    category,
    COUNT(*) as types_count,
    AVG(points) as avg_points,
    SUM(points) as total_points
FROM achievement_types 
GROUP BY category 
ORDER BY total_points DESC;
```

## 🎯 Связь с таблицей achievements

Таблица `achievement_types` является справочной для таблицы `achievements`:

- `achievement_types` - содержит типы достижений (что можно получить)
- `achievements` - содержит выданные достижения пользователям (кто что получил)

### Пример JOIN запроса
```sql
SELECT 
    a.id,
    a.name as achievement_name,
    a.user_id,
    at.name as type_name,
    at.category,
    at.points,
    at.icon
FROM achievements a
JOIN achievement_types at ON a.name = at.name
WHERE a.user_id = 1
ORDER BY at.points DESC;
```

## 🔍 Отладка и мониторинг

### Проверить состояние таблицы
```bash
python quick_view_achievement_types.py
```

### Проверить структуру
```bash
python view_achievement_types.py
```

### Мониторинг производительности
```sql
-- Проверить индексы
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'achievement_types';

-- Проверить статистику
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables 
WHERE tablename = 'achievement_types';
```

## 🚨 Устранение неполадок

### Таблица не существует
```bash
# Создать таблицу заново
python create_achievement_types_table.py
```

### Пустая таблица
```bash
# Проверить, что скрипт создания выполнился успешно
python view_achievement_types.py
```

### Ошибки при вставке
```sql
-- Проверить ограничения
SELECT conname, contype, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'achievement_types'::regclass;
```

## 📚 Дополнительные ресурсы

- [Документация PostgreSQL](https://www.postgresql.org/docs/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/14/orm/)
- [PostgreSQL индексы](https://www.postgresql.org/docs/current/indexes.html)

## 🤝 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте логи приложения
2. Убедитесь, что база данных запущена
3. Проверьте настройки подключения
4. Запустите диагностические скрипты

---

**Удачного использования системы типов достижений! 🎉**





