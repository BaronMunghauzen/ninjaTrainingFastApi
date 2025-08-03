from uuid import UUID
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import FileResponse
from app.users.dependencies import get_current_user_user
from app.users.models import User
from app.files.service import FileService
from app.files.schemas import FileUploadResponse, FileResponse as FileResponseSchema
from app.files.dao import FilesDAO
from app.users.dao import UsersDAO
import os

router = APIRouter(prefix='/files', tags=['Files'])





@router.get("/file/{file_uuid}")
async def get_file(file_uuid: UUID):
    """Получение файла по UUID из таблицы files"""
    try:
        print(f"Ищем файл с UUID: {file_uuid}")
        
        # Получаем файл по UUID используя специальный метод
        file_record = await FilesDAO.find_by_uuid(str(file_uuid))
        print(f"Результат поиска файла: {file_record}")
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Файл не найден в базе данных"
            )
        
        print(f"Путь к файлу: {file_record.file_path}")
        
        # Проверяем, что файл существует на диске
        if not os.path.exists(file_record.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Файл не найден на сервере по пути: {file_record.file_path}"
            )
        
        print(f"Файл найден на диске, возвращаем...")
        
        # Возвращаем файл
        try:
            return FileResponse(
                path=file_record.file_path,
                media_type=file_record.mime_type,
                filename=file_record.filename
            )
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка кодировки при чтении файла: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при получении файла: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ошибка при получении файла: {str(e)}"
        )





@router.delete("/file/{file_uuid}")
async def delete_file(
    file_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
):
    """Удаление файла по UUID"""
    print(f"=== НАЧАЛО УДАЛЕНИЯ ФАЙЛА ===")
    print(f"UUID файла: {file_uuid}")
    print(f"Пользователь: {current_user.id}")
    try:
        # Получаем файл по UUID для проверки прав доступа
        print(f"Ищем файл в базе данных...")
        file_record = await FilesDAO.find_by_uuid(str(file_uuid))
        print(f"Результат поиска файла: {file_record}")
        print(f"Тип результата: {type(file_record)}")
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Файл не найден"
            )
        
        # Проверяем права доступа (пользователь может удалять только свои файлы)
        if file_record.entity_type == "user" and file_record.entity_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы можете удалять только свои файлы"
            )
        
        # Удаляем файл (включая очистку ссылок в FileService)
        success = await FileService.delete_file_by_uuid(str(file_uuid))
        if success:
            return {"message": "Файл успешно удален"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при удалении файла"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при удалении файла: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении файла: {str(e)}"
        ) 