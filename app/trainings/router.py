from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.trainings.dao import TrainingDAO
from app.trainings.rb import RBTraining
from app.trainings.schemas import STraining, STrainingAdd, STrainingUpdate, STrainingArchiveResponse, STrainingRestoreResponse
from app.users.dependencies import get_current_admin_user, get_current_user_user
from app.programs.dao import ProgramDAO
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO
from app.files.service import FileService

router = APIRouter(prefix='/trainings', tags=['Работа с тренировками'])


@router.get("/", summary="Получить все тренировки")
async def get_all_trainings(request_body: RBTraining = Depends(), user_data = Depends(get_current_user_user)) -> list[dict]:
    filters = request_body.to_dict()
    # Исправление: если есть user_uuid, ищем user_id и подставляем его вместо user_uuid
    user_uuid = filters.pop('user_uuid', None)
    if user_uuid:
        user = await UsersDAO.find_one_or_none(uuid=user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        filters['user_id'] = user.id
    trainings = await TrainingDAO.find_all(**filters)
    result = []
    for t in trainings:
        data = {
            "uuid": str(t.uuid),
            "training_type": t.training_type,
            "caption": t.caption,
            "description": t.description,
            "difficulty_level": t.difficulty_level,
            "duration": t.duration,
            "order": t.order,
            "muscle_group": t.muscle_group,
            "stage": t.stage,
            "image_uuid": str(t.image.uuid) if hasattr(t, 'image') and t.image else None,
            "actual": t.actual,
        }
        # Безопасно получаем данные программы
        if hasattr(t, 'program') and t.program:
            try:
                data['program'] = {
                    "uuid": str(t.program.uuid),
                    "actual": t.program.actual,
                    "program_type": t.program.program_type,
                    "caption": t.program.caption,
                    "description": t.program.description,
                    "difficulty_level": t.program.difficulty_level,
                    "order": t.program.order,
                    "training_days": t.program.training_days,
                    "image_uuid": str(t.program.image.uuid) if hasattr(t.program, 'image') and t.program.image else None
                }
            except Exception:
                data['program'] = None
        else:
            data['program'] = None
            
        # Безопасно получаем данные пользователя
        if hasattr(t, 'user') and t.user:
            try:
                data['user'] = await t.user.to_dict()
            except Exception:
                data['user'] = None
        else:
            data['user'] = None
            
        result.append(data)
    return result


@router.get("/{training_uuid}", summary="Получить одну тренировку по id")
async def get_training_by_id(training_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    rez = await TrainingDAO.find_full_data(training_uuid)
    if rez is None:
        return {'message': f'Тренировка с ID {training_uuid} не найдена!'}
    # Используем предзагруженные данные вместо дополнительных запросов
    data = rez.to_dict()
    data.pop('program_id', None)
    data.pop('user_id', None)
    data.pop('program_uuid', None)
    data.pop('user_uuid', None)
    
    # Безопасно получаем данные программы
    if hasattr(rez, 'program') and rez.program:
        try:
            data['program'] = {
                "uuid": str(rez.program.uuid),
                "actual": rez.program.actual,
                "program_type": rez.program.program_type,
                "caption": rez.program.caption,
                "description": rez.program.description,
                "difficulty_level": rez.program.difficulty_level,
                "order": rez.program.order,
                "training_days": rez.program.training_days,
                "image_uuid": str(rez.program.image.uuid) if hasattr(rez.program, 'image') and rez.program.image else None
            }
        except Exception:
            data['program'] = None
    else:
        data['program'] = None
        
    # Безопасно получаем данные пользователя
    if hasattr(rez, 'user') and rez.user:
        try:
            data['user'] = await rez.user.to_dict()
        except Exception:
            data['user'] = None
    else:
        data['user'] = None
        
    return data


@router.post("/add/")
async def add_training(training: STrainingAdd, user_data = Depends(get_current_user_user)) -> dict:
    values = training.model_dump()
    # Получаем program_id по program_uuid
    program_uuid = values.pop('program_uuid', None)
    if program_uuid:
        program = await ProgramDAO.find_one_or_none(uuid=program_uuid)
        if not program:
            raise HTTPException(status_code=404, detail="Программа не найдена")
        values['program_id'] = program.id
    # если не передан, не добавляем program_id

    # Аналогично для user_uuid, если нужно
    user_uuid = values.pop('user_uuid', None)
    if user_uuid:
        user = await UsersDAO.find_one_or_none(uuid=user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        values['user_id'] = user.id
    # если не передан, не добавляем user_id

    # Обработка image_uuid
    if values.get('image_uuid'):
        image = await FilesDAO.find_one_or_none(uuid=values.pop('image_uuid'))
        if not image:
            raise HTTPException(status_code=404, detail="Изображение не найдено")
        values['image_id'] = image.id
    # Удаляю image_uuid если вдруг остался
    values.pop('image_uuid', None)

    training_uuid = await TrainingDAO.add(**values)
    training_obj = await TrainingDAO.find_full_data(training_uuid)
    # Формируем ответ как в get_training_by_id
    data = training_obj.to_dict()
    data.pop('program_id', None)
    data.pop('user_id', None)
    data.pop('program_uuid', None)
    data.pop('user_uuid', None)
    
    # Безопасно получаем данные программы
    if hasattr(training_obj, 'program') and training_obj.program:
        try:
            data['program'] = {
                "uuid": str(training_obj.program.uuid),
                "actual": training_obj.program.actual,
                "program_type": training_obj.program.program_type,
                "caption": training_obj.program.caption,
                "description": training_obj.program.description,
                "difficulty_level": training_obj.program.difficulty_level,
                "order": training_obj.program.order,
                "training_days": training_obj.program.training_days,
                "image_uuid": str(training_obj.program.image.uuid) if hasattr(training_obj.program, 'image') and training_obj.program.image else None
            }
        except Exception:
            data['program'] = None
    else:
        data['program'] = None
        
    # Безопасно получаем данные пользователя
    if hasattr(training_obj, 'user') and training_obj.user:
        try:
            data['user'] = await training_obj.user.to_dict()
        except Exception:
            data['user'] = None
    else:
        data['user'] = None
        
    return data


@router.put("/update/{training_uuid}")
async def update_training(training_uuid: UUID, training: STrainingUpdate, user_data = Depends(get_current_user_user)) -> dict:
    # Проверяем права доступа
    existing_training = await TrainingDAO.find_one_or_none(uuid=training_uuid)
    if not existing_training:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    
    # Если тренировка пользовательская (user), проверяем, что это его тренировка
    if existing_training.training_type == "user":
        if not existing_training.user_id or existing_training.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Вы можете редактировать только свои тренировки")
    # Если тренировка системная (system), разрешаем редактировать только админам
    elif existing_training.training_type == "system":
        if not user_data.is_admin:
            raise HTTPException(status_code=403, detail="Только администраторы могут редактировать системные тренировки")
    
    update_data = training.model_dump(exclude_unset=True)
    # Преобразуем program_uuid и user_uuid в id, если они есть
    if 'program_uuid' in update_data:
        program = await ProgramDAO.find_one_or_none(uuid=update_data.pop('program_uuid'))
        if not program:
            raise HTTPException(status_code=404, detail="Программа не найдена")
        update_data['program_id'] = program.id
    if 'user_uuid' in update_data:
        user = await UsersDAO.find_one_or_none(uuid=update_data.pop('user_uuid'))
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        update_data['user_id'] = user.id

    # Обработка image_uuid
    if 'image_uuid' in update_data:
        image_uuid = update_data.pop('image_uuid')
        if image_uuid:
            image = await FilesDAO.find_one_or_none(uuid=image_uuid)
            if not image:
                raise HTTPException(status_code=404, detail="Изображение не найдено")
            update_data['image_id'] = image.id
        else:
            update_data['image_id'] = None

    check = await TrainingDAO.update(training_uuid, **update_data)
    if check:
        updated_training = await TrainingDAO.find_full_data(training_uuid)
        data = updated_training.to_dict()
        data.pop('program_id', None)
        data.pop('user_id', None)
        data.pop('program_uuid', None)
        data.pop('user_uuid', None)
        
        # Безопасно получаем данные программы
        if hasattr(updated_training, 'program') and updated_training.program:
            try:
                data['program'] = {
                    "uuid": str(updated_training.program.uuid),
                    "actual": updated_training.program.actual,
                    "program_type": updated_training.program.program_type,
                    "caption": updated_training.program.caption,
                    "description": updated_training.program.description,
                    "difficulty_level": updated_training.program.difficulty_level,
                    "order": updated_training.program.order,
                    "training_days": updated_training.program.training_days,
                    "image_uuid": str(updated_training.program.image.uuid) if hasattr(updated_training.program, 'image') and updated_training.program.image else None
                }
            except Exception:
                data['program'] = None
        else:
            data['program'] = None
            
        # Безопасно получаем данные пользователя
        if hasattr(updated_training, 'user') and updated_training.user:
            try:
                data['user'] = await updated_training.user.to_dict()
            except Exception:
                data['user'] = None
        else:
            data['user'] = None
            
        return data
    else:
        return {"message": "Ошибка при обновлении тренировки!"}


@router.delete("/delete/{training_uuid}")
async def delete_training_by_id(training_uuid: UUID, user_data = Depends(get_current_admin_user)) -> dict:
    check = await TrainingDAO.delete_by_id(training_uuid)
    if check:
        return {"message": f"Тренировка с ID {training_uuid} удалена!"}
    else:
        return {"message": "Ошибка при удалении тренировки!"}


@router.post("/{training_uuid}/upload-image", summary="Загрузить изображение для тренировки")
async def upload_training_image(
    training_uuid: UUID,
    file: UploadFile = File(...),
    user_data = Depends(get_current_admin_user)
):
    training = await TrainingDAO.find_full_data(training_uuid)
    if not training:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    old_file_uuid = getattr(training.image, 'uuid', None)
    saved_file = await FileService.save_file(
        file=file,
        entity_type="training",
        entity_id=training.id,
        old_file_uuid=str(old_file_uuid) if old_file_uuid else None
    )
    await TrainingDAO.update(training_uuid, image_id=saved_file.id)
    return {"message": "Изображение успешно загружено", "image_uuid": saved_file.uuid}


@router.delete("/{training_uuid}/delete-image", summary="Удалить изображение тренировки")
async def delete_training_image(
    training_uuid: UUID,
    user_data = Depends(get_current_admin_user)
):
    training = await TrainingDAO.find_full_data(training_uuid)
    if not training:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    
    if not training.image:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    
    image_uuid = training.image.uuid
    # Удаляем файл (это автоматически очистит image_id в trainings и запись в files)
    try:
        await FileService.delete_file_by_uuid(str(image_uuid))
    except Exception as e:
        # Если удаление файла не удалось, возвращаем ошибку
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении файла: {str(e)}")
    
    return {"message": "Изображение успешно удалено"}


@router.post("/{training_uuid}/archive", summary="Архивировать тренировку", response_model=STrainingArchiveResponse)
async def archive_training(
    training_uuid: UUID,
    user_data = Depends(get_current_admin_user)
) -> STrainingArchiveResponse:
    """
    Архивировать тренировку (установить actual = False)
    """
    archived_training = await TrainingDAO.archive_training(training_uuid)
    
    return STrainingArchiveResponse(
        message=f"Тренировка {training_uuid} успешно заархивирована",
        training_uuid=str(archived_training.uuid),
        actual=archived_training.actual
    )


@router.post("/{training_uuid}/restore", summary="Восстановить тренировку из архива", response_model=STrainingRestoreResponse)
async def restore_training(
    training_uuid: UUID,
    user_data = Depends(get_current_admin_user)
) -> STrainingRestoreResponse:
    """
    Восстановить тренировку из архива (установить actual = True)
    """
    restored_training = await TrainingDAO.restore_training(training_uuid)
    
    return STrainingRestoreResponse(
        message=f"Тренировка {training_uuid} успешно восстановлена из архива",
        training_uuid=str(restored_training.uuid),
        actual=restored_training.actual
    )