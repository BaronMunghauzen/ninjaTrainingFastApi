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





@router.get('/file/{file_uuid}', summary='Получить файл по UUID')
async def get_file_by_uuid(file_uuid: str, user_data = Depends(get_current_user_user)):
    print(f"Поиск файла с UUID: {file_uuid}")
    file_record = await FilesDAO.find_by_uuid(file_uuid)
    print(f"Результат поиска файла: ID={file_record.id if file_record else None}, UUID={file_record.uuid if file_record else None}")
    
    if not file_record:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Проверяем права доступа
    if file_record.entity_type == "user" and file_record.entity_id != user_data.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому файлу")
    
    # Проверяем существование файла на диске
    if not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    
    print(f"Путь к файлу: {file_record.file_path}")
    
    # Возвращаем файл
    return FileResponse(
        path=file_record.file_path,
        filename=file_record.filename,
        media_type=file_record.mime_type
    )

@router.delete('/file/{file_uuid}', summary='Удалить файл по UUID')
async def delete_file_by_uuid(file_uuid: str, user_data = Depends(get_current_user_user)):
    print(f"Удаление файла с UUID: {file_uuid}")
    file_record = await FilesDAO.find_by_uuid(file_uuid)
    print(f"Результат поиска файла: ID={file_record.id if file_record else None}, UUID={file_record.uuid if file_record else None}")
    print(f"Тип результата: {type(file_record)}")
    
    if not file_record:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Проверяем права доступа
    if file_record.entity_type == "user" and file_record.entity_id != user_data.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому файлу")
    
    # Удаляем файл
    try:
        await FileService.delete_file_by_uuid(file_uuid)
        return {"message": "Файл успешно удален"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении файла: {str(e)}") 


