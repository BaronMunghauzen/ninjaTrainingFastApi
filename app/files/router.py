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


@router.post("/upload/avatar/{user_uuid}", response_model=FileUploadResponse)
async def upload_avatar(
    user_uuid: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_user)
):
    """Загрузка аватара пользователя"""
    # Проверяем, что пользователь загружает свой аватар
    if str(current_user.uuid) != str(user_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете загружать только свой аватар"
        )
    
    # Проверяем, что пользователь имеет права
    if not current_user.is_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    # Ищем существующий аватар
    existing_avatar = await FilesDAO.find_avatar_by_user_id(current_user.id)
    old_file_uuid = str(existing_avatar.uuid) if existing_avatar else None
    
    # Сохраняем новый файл
    saved_file = await FileService.save_file(
        file=file,
        entity_type="user",
        entity_id=current_user.id,
        old_file_uuid=old_file_uuid
    )
    
    # Обновляем поле avatar_id у пользователя
    await UsersDAO.update(current_user.uuid, avatar_id=saved_file.id)
    
    # Удаляем старые аватары пользователя (оставляем только новый)
    if existing_avatar:
        await FilesDAO.delete_old_avatars_for_user(current_user.id, keep_latest=True)
    
    return FileUploadResponse(
        message="Аватар успешно загружен",
        file=FileResponseSchema.model_validate(saved_file)
    )


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
        return FileResponse(
            path=file_record.file_path,
            media_type=file_record.mime_type,
            filename=file_record.filename
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