"""
Роутер для работы с логами приложения
Позволяет администраторам скачивать файлы логов
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
import os
from app.users.dependencies import get_current_admin_user
from app.users.models import User
from app.logger import logger
from typing import Optional

router = APIRouter(prefix='/logs', tags=['Logs'])


def _get_safe_headers(filename: str, media_type: str) -> dict:
    """
    Создает безопасные заголовки для скачивания файла
    """
    # Для .log файлов используем .txt расширение при скачивании, чтобы избежать блокировки антивирусом
    download_filename = filename
    if filename.endswith('.log'):
        download_filename = filename.replace('.log', '.txt')
    
    # Экранируем имя файла для Content-Disposition (RFC 5987)
    from urllib.parse import quote
    encoded_filename = quote(download_filename, safe='')
    
    return {
        "Content-Disposition": f'attachment; filename="{download_filename}"; filename*=UTF-8\'\'{encoded_filename}',
        "Content-Type": media_type,
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'",
        "X-Download-Options": "noopen"
    }


@router.get('/list', summary='Получить список доступных логов')
async def get_logs_list(admin: User = Depends(get_current_admin_user)):
    """
    Возвращает список всех доступных файлов логов
    """
    try:
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return {"logs": [], "message": "Директория логов не найдена"}
        
        log_files = []
        for file_path in sorted(logs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if file_path.is_file() and (file_path.suffix == '.log' or file_path.suffix == '.zip'):
                stat = file_path.stat()
                log_files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "type": "archive" if file_path.suffix == '.zip' else "log"
                })
        
        return {"logs": log_files}
    except Exception as e:
        logger.error(f"Ошибка при получении списка логов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка логов: {str(e)}")


@router.get('/download/{filename}', summary='Скачать файл лога')
async def download_log(
    filename: str,
    admin: User = Depends(get_current_admin_user)
):
    """
    Скачивает файл лога по имени файла
    Безопасно обрабатывает кодировку UTF-8 и передает файл с правильными заголовками
    """
    try:
        # Проверяем безопасность имени файла (предотвращаем path traversal)
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Недопустимое имя файла")
        
        logs_dir = Path("logs")
        file_path = logs_dir / filename
        
        # Проверяем существование файла
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Файл лога не найден")
        
        # Проверяем, что файл находится в директории logs (дополнительная проверка безопасности)
        try:
            file_path.resolve().relative_to(logs_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Определяем media_type в зависимости от расширения
        if filename.endswith('.zip'):
            media_type = 'application/zip'
        elif filename.endswith('.log'):
            media_type = 'text/plain; charset=utf-8'
        else:
            media_type = 'application/octet-stream'
        
        # Для .log файлов используем .txt расширение при скачивании, чтобы избежать блокировки антивирусом
        download_filename = filename
        if filename.endswith('.log'):
            download_filename = filename.replace('.log', '.txt')
        
        # Возвращаем файл с правильной кодировкой и безопасными заголовками
        return FileResponse(
            path=str(file_path),
            filename=download_filename,
            media_type=media_type,
            headers=_get_safe_headers(filename, media_type)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при скачивании лога {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при скачивании лога: {str(e)}")


@router.get('/download-stream/{filename}', summary='Скачать файл лога (streaming)')
async def download_log_stream(
    filename: str,
    admin: User = Depends(get_current_admin_user)
):
    """
    Скачивает файл лога через streaming (для больших файлов)
    Гарантирует правильную передачу UTF-8 кодировки
    """
    try:
        # Проверяем безопасность имени файла
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Недопустимое имя файла")
        
        logs_dir = Path("logs")
        file_path = logs_dir / filename
        
        # Проверяем существование файла
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Файл лога не найден")
        
        # Проверяем, что файл находится в директории logs
        try:
            file_path.resolve().relative_to(logs_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Определяем media_type
        if filename.endswith('.zip'):
            media_type = 'application/zip'
        elif filename.endswith('.log'):
            media_type = 'text/plain; charset=utf-8'
        else:
            media_type = 'application/octet-stream'
        
        # Функция для чтения файла с правильной кодировкой
        def generate():
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)  # Читаем по 8KB
                    if not chunk:
                        break
                    yield chunk
        
        return StreamingResponse(
            generate(),
            media_type=media_type,
            headers=_get_safe_headers(filename, media_type)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при скачивании лога {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при скачивании лога: {str(e)}")

