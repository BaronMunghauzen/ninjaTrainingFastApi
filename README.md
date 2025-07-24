# Ninja Training Python Project

## Описание

Этот проект — backend для системы тренировок на Python с использованием FastAPI, SQLAlchemy, Alembic и Docker. Поддерживает работу с пользователями, программами тренировок, файлами и т.д.

---

## Быстрый старт

### 1. Клонируйте репозиторий
```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ>
cd pythonProject
```

### 2. Создайте и настройте файл окружения (я скину)
Скопируйте пример и заполните своими значениями:
```bash
cp .env.example .env
```

**Пример .env:**
```
POSTGRES_USER=admin
POSTGRES_PASSWORD=secret
POSTGRES_DB=ninja_training
# Добавьте другие переменные, если нужно
```

### 3. Установите зависимости (если не используете Docker)
```bash
pip install -r req.txt
```

### 4. Запустите проект через Docker Compose
```bash
docker-compose up --build
```

---

## API: Сущности и роуты

### Пользователь (User)
- **/auth/register/** — регистрация пользователя
- **/auth/login/** — авторизация, получение токенов
- **/auth/refresh/** — обновление токена
- **/auth/me/** — информация о текущем пользователе
- **/auth/update/** — обновление профиля

### Категории (Category)
- **/categories/** — получить все категории
- **/categories/{category_uuid}** — получить категорию по id
- **/categories/add/** — добавить категорию (админ)
- **/categories/update/{category_uuid}** — обновить категорию (админ)
- **/categories/delete/{category_uuid}** — удалить категорию (админ)

### Программы тренировок (Program)
- **/programs/** — получить все программы
- **/programs/{program_uuid}** — получить программу по id
- **/programs/add/** — добавить программу (админ)
- **/programs/update/{program_uuid}** — обновить программу (админ)
- **/programs/delete/{program_uuid}** — удалить программу (админ)

### Тренировки (Training)
- **/trainings/** — получить все тренировки
- **/trainings/{training_uuid}** — получить тренировку по id
- **/trainings/add/** — добавить тренировку (админ)
- **/trainings/update/{training_uuid}** — обновить тренировку (админ)
- **/trainings/delete/{training_uuid}** — удалить тренировку (админ)
- **/trainings/{training_uuid}/upload-image** — загрузить изображение для тренировки

### Группы упражнений (ExerciseGroup)
- **/exercise-groups/** — получить все группы упражнений
- **/exercise-groups/{group_uuid}** — получить группу по id
- **/exercise-groups/add/** — добавить группу (админ)
- **/exercise-groups/update/{group_uuid}** — обновить группу (админ)
- **/exercise-groups/delete/{group_uuid}** — удалить группу (админ)

### Упражнения (Exercise)
- **/exercises/** — получить все упражнения
- **/exercises/{exercise_uuid}** — получить упражнение по id
- **/exercises/add/** — добавить упражнение (админ)
- **/exercises/update/{exercise_uuid}** — обновить упражнение (админ)
- **/exercises/delete/{exercise_uuid}** — удалить упражнение (админ)

### Пользовательские программы (UserProgram)
- **/user_programs/** — получить все пользовательские программы
- **/user_programs/{user_program_uuid}** — получить пользовательскую программу по id
- **/user_programs/add/** — добавить пользовательскую программу
- **/user_programs/update/{user_program_uuid}** — обновить пользовательскую программу
- **/user_programs/delete/{user_program_uuid}** — удалить пользовательскую программу

### Пользовательские тренировки (UserTraining)
- **/user_trainings/** — получить все пользовательские тренировки
- **/user_trainings/{user_training_uuid}** — получить пользовательскую тренировку по id
- **/user_trainings/add/** — добавить пользовательскую тренировку
- **/user_trainings/update/{user_training_uuid}** — обновить пользовательскую тренировку
- **/user_trainings/delete/{user_training_uuid}** — удалить пользовательскую тренировку

### Пользовательские упражнения (UserExercise)
- **/user_exercises/** — получить все пользовательские упражнения
- **/user_exercises/{user_exercise_uuid}** — получить пользовательское упражнение по id
- **/user_exercises/add/** — добавить пользовательское упражнение
- **/user_exercises/update/{user_exercise_uuid}** — обновить пользовательское упражнение
- **/user_exercises/delete/{user_exercise_uuid}** — удалить пользовательское упражнение

### Файлы (Files)
- **/files/upload/** — загрузить файл
- **/files/{file_uuid}** — получить файл по id
- **/files/delete/{file_uuid}** — удалить файл

---

## Запуск через Docker

1. Убедитесь, что у вас есть `.env` с нужными переменными.
2. Запустите:
   ```bash
   docker-compose up --build
   ```
   Это поднимет контейнер с Postgres и ваше приложение (если добавлен сервис приложения).

3. Для остановки:
   ```bash
   docker-compose down
   ```

---

## Миграции и работа с БД

### Как применить все миграции:
1. Убедитесь, что переменные окружения для БД прописаны в `.env`.
2. Выполните:
   ```bash
   alembic upgrade head
   ```
   Это применит все миграции к вашей локальной базе.

### Как создать новую миграцию:
```bash
alembic revision --autogenerate -m "описание изменений"
```
После этого примените миграцию командой выше.

### Как подключить локальную БД:
- В `.env` укажите параметры вашей локальной базы:
  ```
  DB_HOST=localhost
  DB_PORT=5432
  DB_NAME=ninja_training
  DB_USER=admin
  DB_PASSWORD=secret
  ```
- Убедитесь, что база существует и доступна.

---

## Swagger/OpenAPI

После запуска приложения перейдите по адресу:
```
http://localhost:8000/docs
```
Там будет интерактивная документация по всем роутам.

---

## Структура проекта
- `app/` — основной код приложения
- `tests/` — тесты
- `uploads/` — пользовательские файлы (игнорируется в git)
- `.env` — переменные окружения (не хранится в git)
- `.env.example` — пример для настройки окружения
- `docker-compose.yml` — инфраструктура для запуска через Docker

---

## Миграции базы данных
Для работы с миграциями используется Alembic:
```bash
alembic upgrade head
```

---

## Запуск тестов
```bash
pytest
```

---

## Важно
- **Не храните реальные секреты в .env.example и других публичных файлах!**
- Все чувствительные данные должны быть только в `.env`, который не попадает в git.

---
