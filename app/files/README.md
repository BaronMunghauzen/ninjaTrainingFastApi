# Система загрузки файлов

## Описание

Универсальная система загрузки файлов для приложения. Позволяет загружать, хранить и управлять файлами для различных сущностей (пользователи, программы и т.д.).

## Структура

- `models.py` - Модель File для хранения информации о файлах
- `dao.py` - Data Access Object для работы с файлами
- `service.py` - Сервис для загрузки и управления файлами
- `router.py` - API эндпоинты для работы с файлами
- `schemas.py` - Pydantic схемы для валидации данных

## API Эндпоинты

### Загрузка аватара пользователя
```
POST /files/upload/avatar/{user_uuid}
```

**Параметры:**
- `user_uuid` - UUID пользователя
- `file` - Файл изображения (multipart/form-data)

**Поддерживаемые форматы:**
- JPEG/JPG
- PNG
- GIF
- WebP

**Максимальный размер:** 10MB

**Ответ:**
```json
{
  "message": "Аватар успешно загружен",
  "file": {
    "uuid": "file-uuid",
    "filename": "original_name.jpg",
    "file_size": 1024,
    "mime_type": "image/jpeg",
    "entity_type": "user",
    "entity_id": 1,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

### Получение аватара пользователя
```
GET /files/avatar/{user_uuid}
```

**Параметры:**
- `user_uuid` - UUID пользователя

**Ответ:** Файл изображения

### Удаление аватара пользователя
```
DELETE /files/avatar/{user_uuid}
```

**Параметры:**
- `user_uuid` - UUID пользователя

**Ответ:**
```json
{
  "message": "Аватар успешно удален"
}
```

## Использование в коде

### Загрузка файла
```python
from app.files.service import FileService

# Загрузка аватара
saved_file = await FileService.save_file(
    file=upload_file,
    entity_type="user",
    entity_id=user.id,
    old_file_uuid=existing_avatar_uuid  # опционально
)
```

### Получение файла
```python
from app.files.dao import FilesDAO

# Поиск аватара пользователя
avatar = await FilesDAO.find_avatar_by_user_id(user_id)

# Поиск файлов по типу сущности
files = await FilesDAO.find_by_entity("user", user_id)
```

### Удаление файла
```python
from app.files.service import FileService

# Удаление файла по UUID
success = await FileService.delete_file_by_uuid(file_uuid)
```

## Расширение для других сущностей

Для добавления поддержки файлов для других сущностей (например, программ):

1. Создайте новый эндпоинт в `router.py`:
```python
@router.post("/upload/program/{program_uuid}")
async def upload_program_image(
    program_uuid: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_user)
):
    # Логика загрузки изображения программы
    saved_file = await FileService.save_file(
        file=file,
        entity_type="program",
        entity_id=program.id
    )
    return FileUploadResponse(message="Изображение программы загружено", file=saved_file)
```

2. Добавьте связь в модель Program:
```python
# В app/programs/models.py
program_images: Mapped[list["File"]] = relationship("File", back_populates="program")
```

3. Обновите модель File для поддержки связи:
```python
# В app/files/models.py
program = relationship("Program", back_populates="program_images")
```

## Безопасность

- Проверка типов файлов
- Ограничение размера файлов
- Авторизация пользователей
- Валидация прав доступа
- Безопасное хранение файлов с уникальными именами

## Хранение файлов

Файлы сохраняются в директории `uploads/` с уникальными именами, основанными на UUID. Информация о файлах хранится в таблице `files` в базе данных. 