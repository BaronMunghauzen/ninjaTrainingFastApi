from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.trainings.dao import TrainingDAO
from app.trainings.rb import RBTraining
from app.trainings.schemas import STraining, STrainingAdd, STrainingUpdate
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
        # Используем предзагруженные данные вместо дополнительных запросов
        data['program'] = t.program.to_dict() if hasattr(t, 'program') and t.program else None
        data['user'] = await t.user.to_dict() if hasattr(t, 'user') and t.user else None
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
    data['program'] = rez.program.to_dict() if hasattr(rez, 'program') and rez.program else None
    data['user'] = await rez.user.to_dict() if hasattr(rez, 'user') and rez.user else None
    return data


@router.post("/add/")
async def add_training(training: STrainingAdd, user_data = Depends(get_current_admin_user)) -> dict:
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
    program = await ProgramDAO.find_full_data(training_obj.program.uuid) if training_obj.program else None
    user = await UsersDAO.find_one_or_none(id=training_obj.user_id) if training_obj.user_id else None
    data = training_obj.to_dict()
    data.pop('program_id', None)
    data.pop('user_id', None)
    data.pop('program_uuid', None)
    data.pop('user_uuid', None)
    data['program'] = program.to_dict() if program else None
    data['user'] = await user.to_dict() if user else None
    return data


@router.put("/update/{training_uuid}")
async def update_training(training_uuid: UUID, training: STrainingUpdate, user_data = Depends(get_current_admin_user)) -> dict:
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
        program = await ProgramDAO.find_full_data(updated_training.program.uuid) if updated_training.program else None
        user = await UsersDAO.find_one_or_none(id=updated_training.user_id) if updated_training.user_id else None
        data = updated_training.to_dict()
        data.pop('program_id', None)
        data.pop('user_id', None)
        data.pop('program_uuid', None)
        data.pop('user_uuid', None)
        data['program'] = program.to_dict() if program else None
        data['user'] = await user.to_dict() if user else None
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
