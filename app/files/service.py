import os
import shutil
from pathlib import Path
from uuid import uuid4, UUID
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.files.dao import FilesDAO
from app.files.models import File


class FileService:
    UPLOAD_DIR = "uploads"
    MAX_FILE_SIZE = 60 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES = {
        "image/jpeg",
        "image/jpg", 
        "image/png",
        "image/gif",
        "image/webp"
    }
    ALLOWED_VIDEO_TYPES = {
        "video/mp4",
        "video/avi",
        "video/mpeg",
        "video/quicktime",
        "video/x-matroska",
        "video/webm"
    }
    
    @classmethod
    def ensure_upload_dir(cls):
        """Создает директорию для загрузок если её нет"""
        upload_path = Path(cls.UPLOAD_DIR)
        upload_path.mkdir(exist_ok=True)
        return upload_path
    
    @classmethod
    def validate_image_file(cls, file: UploadFile) -> None:
        """Проверяет валидность изображения"""
        if not file.content_type or file.content_type not in cls.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(cls.ALLOWED_IMAGE_TYPES)}"
            )

    @classmethod
    def validate_video_file(cls, file: UploadFile) -> None:
        """Проверяет валидность видео"""
        if not file.content_type or file.content_type not in cls.ALLOWED_VIDEO_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неподдерживаемый тип видео. Разрешены: {', '.join(cls.ALLOWED_VIDEO_TYPES)}"
            )

    @classmethod
    async def save_file(
        cls, 
        file: UploadFile, 
        entity_type: str, 
        entity_id: int,
        old_file_uuid: Optional[str] = None
    ) -> File:
        """Сохраняет файл и создает запись в БД (только для изображений)"""
        print(f"Начинаем загрузку изображения: {file.filename}, тип: {file.content_type}")
        
        # Валидация файла
        cls.validate_image_file(file)
        print("Валидация изображения пройдена")
        
        # Проверка размера файла
        file_size = 0
        content = b""
        chunk_count = 0
        while chunk := await file.read(8192):
            content += chunk
            file_size += len(chunk)
            chunk_count += 1
            if chunk_count % 100 == 0:  # Логируем каждые 100 чанков
                print(f"Прочитано чанков: {chunk_count}, размер: {file_size} байт")
            if file_size > cls.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Файл слишком большой. Максимальный размер: {cls.MAX_FILE_SIZE // (1024*1024)}MB"
                )
        
        print(f"Файл полностью прочитан. Размер: {file_size} байт, чанков: {chunk_count}")
        
        # Создаем директорию если нужно
        upload_dir = cls.ensure_upload_dir()
        print(f"Директория для загрузки: {upload_dir}")
        
        # Генерируем уникальное имя файла
        generated_uuid = str(uuid4())
        file_extension = Path(file.filename).suffix if file.filename else ".jpg"
        new_filename = f"{generated_uuid}{file_extension}"
        file_path = upload_dir / new_filename
        print(f"Путь к файлу: {file_path}")
        
        # Сохраняем файл
        try:
            with open(file_path, "wb") as f:
                f.write(content)
            print("Файл успешно сохранен на диск")
        except UnicodeEncodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка кодировки при сохранении файла: {str(e)}"
            )
        
        # Удаляем старый файл если есть
        if old_file_uuid:
            print(f"Удаляем старый файл: {old_file_uuid}")
            await cls.delete_file_by_uuid(old_file_uuid)
        
        # Создаем запись в БД
        file_data = {
            "filename": file.filename or "unknown",
            "file_path": str(file_path),
            "file_size": file_size,
            "mime_type": file.content_type or "image/jpeg",
            "entity_type": entity_type,
            "entity_id": entity_id
        }
        print(f"Создаем запись в БД: filename={file_data['filename']}, size={file_data['file_size']}, type={file_data['mime_type']}")
        
        saved_file_uuid = await FilesDAO.add(**file_data)
        print(f"Запись создана в БД, UUID: {saved_file_uuid}")
        
        result = await FilesDAO.find_full_data(saved_file_uuid)
        print("Загружен файл")
        return result

    @classmethod
    async def save_video_file(
        cls, 
        file: UploadFile, 
        entity_type: str, 
        entity_id: int,
        old_file_uuid: Optional[str] = None
    ) -> File:
        """Сохраняет видео и создает запись в БД (только для видео)"""
        print(f"Начинаем загрузку видео: {file.filename}, тип: {file.content_type}")
        
        cls.validate_video_file(file)
        print("Валидация видео пройдена")
        
        file_size = 0
        content = b""
        chunk_count = 0
        while chunk := await file.read(8192):
            content += chunk
            file_size += len(chunk)
            chunk_count += 1
            if chunk_count % 100 == 0:  # Логируем каждые 100 чанков
                print(f"Прочитано чанков: {chunk_count}, размер: {file_size} байт")
            if file_size > cls.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Файл слишком большой. Максимальный размер: {cls.MAX_FILE_SIZE // (1024*1024)}MB"
                )
        
        print(f"Видео полностью прочитано. Размер: {file_size} байт, чанков: {chunk_count}")
        
        upload_dir = cls.ensure_upload_dir()
        print(f"Директория для загрузки: {upload_dir}")
        
        generated_uuid = str(uuid4())
        file_extension = Path(file.filename).suffix if file.filename else ".mp4"
        new_filename = f"{generated_uuid}{file_extension}"
        file_path = upload_dir / new_filename
        print(f"Путь к файлу: {file_path}")
        
        with open(file_path, "wb") as f:
            f.write(content)
        print("Видео успешно сохранено на диск")
        
        if old_file_uuid:
            print(f"Удаляем старое видео: {old_file_uuid}")
            await cls.delete_file_by_uuid(old_file_uuid)
        
        file_data = {
            "filename": file.filename or "unknown",
            "file_path": str(file_path),
            "file_size": file_size,
            "mime_type": file.content_type or "video/mp4",
            "entity_type": entity_type,
            "entity_id": entity_id
        }
        print(f"Создаем запись в БД: filename={file_data['filename']}, size={file_data['file_size']}, type={file_data['mime_type']}")
        
        saved_file_uuid = await FilesDAO.add(**file_data)
        print(f"Запись создана в БД, UUID: {saved_file_uuid}")
        
        result = await FilesDAO.find_full_data(saved_file_uuid)
        print("Загружен файл")
        return result
    
    @classmethod
    async def delete_file_by_uuid(cls, file_uuid: str) -> bool:
        """Удаляет файл по UUID"""
        print(f"Удаляем файл с UUID: {file_uuid}")
        file_record = await FilesDAO.find_by_uuid(file_uuid)
        print(f"Найден файл: ID={file_record.id if file_record else None}, UUID={file_record.uuid if file_record else None}")
        
        if not file_record:
            print("Файл не найден в БД")
            return True  # Файл уже удален
        
        # Удаляем файл с диска
        file_path = str(file_record.file_path)
        print(f"Путь к файлу: {file_path}")
        
        if os.path.exists(file_path):
            print(f"Удаляем файл с диска: {file_path}")
            os.remove(file_path)
            print("Файл удален с диска")
        else:
            print(f"Файл не найден на диске: {file_path}")
        
        # Удаляем запись из БД с очисткой ссылок в одной транзакции
        await FilesDAO.delete_file_with_cleanup(file_uuid)
        print("Запись удалена из БД с очисткой ссылок")
        return True
    
    @classmethod
    def get_file_path(cls, file_uuid: str) -> Optional[str]:
        """Получает путь к файлу по UUID"""
        # В реальном приложении здесь нужно получить из БД
        # Пока возвращаем None
        return None 