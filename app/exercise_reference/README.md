# Справочник упражнений (Exercise Reference)

Данная папка содержит реализацию справочника упражнений, который служит для хранения базовой информации об упражнениях (id, uuid, created_at, updated_at, caption, description, muscle_group).

В папке реализованы:
- models.py — SQLAlchemy модель ExerciseReference
- schemas.py — Pydantic-схемы для CRUD-операций
- dao.py — DAO-слой для работы с БД
- rb.py — RB-класс для фильтрации и поиска
- router.py — FastAPI-роутер с CRUD-эндпоинтами

Сущность поддерживает все стандартные CRUD-операции и интегрируется с моделью Training через поле exercise_reference_id. 