from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.exercises.dao import ExerciseDAO
from app.exercises.rb import RBExercise
from app.exercises.schemas import SExercise, SExerciseAdd, SExerciseUpdate
from app.users.dependencies import get_current_admin_user, get_current_user_user
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO
from app.files.service import FileService

router = APIRouter(prefix='/exercises', tags=['Работа с упражнениями'])


@router.get("/", summary="Получить все упражнения")
async def get_all_exercises(request_body: RBExercise = Depends(), user_data = Depends(get_current_user_user)) -> list[dict]:
    exercises = await ExerciseDAO.find_all(**request_body.to_dict())
    # Получаем все user_id из упражнений
    user_ids = {e.user_id for e in exercises if e.user_id is not None}
    users = await UsersDAO.find_in('id', list(user_ids)) if user_ids else []
    id_to_user = {u.id: await u.to_dict() for u in users}
    
    result = []
    for e in exercises:
        data = e.to_dict()
        # Удаляем id и uuid поля
        data.pop('user_id', None)
        data.pop('user_uuid', None)
        # Добавляем вложенные объекты
        data['user'] = id_to_user.get(e.user_id) if e.user_id else None
        data["exercise_reference_uuid"] = str(e.exercise_reference.uuid) if hasattr(e, 'exercise_reference') and e.exercise_reference else None
        result.append(data)
    return result


@router.get("/{exercise_uuid}", summary="Получить одно упражнение по id")
async def get_exercise_by_id(exercise_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    rez = await ExerciseDAO.find_full_data(exercise_uuid)
    if rez is None:
        return {'message': f'Упражнение с ID {exercise_uuid} не найдено!'}
    
    user = await UsersDAO.find_one_or_none(id=rez.user_id) if rez.user_id else None
    
    data = rez.to_dict()
    data.pop('user_id', None)
    data.pop('user_uuid', None)
    data['user'] = await user.to_dict() if user else None
    data["exercise_reference_uuid"] = str(rez.exercise_reference.uuid) if hasattr(rez, 'exercise_reference') and rez.exercise_reference else None
    return data


@router.post("/add/")
async def add_exercise(exercise: SExerciseAdd, user_data = Depends(get_current_user_user)) -> dict:
    values = exercise.model_dump()
    # Получаем user_id по user_uuid, если передан
    user_id = None
    if values.get('user_uuid'):
        user = await UsersDAO.find_one_or_none(uuid=values.pop('user_uuid'))
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        user_id = user.id
    else:
        # Удаляем user_uuid из values, если оно None
        values.pop('user_uuid', None)
    values['user_id'] = user_id
    
    # Проверяем права доступа
    exercise_type = values.get('exercise_type', 'user')
    if exercise_type == "user":
        # Пользователь может создавать только свои упражнения
        if user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Вы можете создавать упражнения только для своего профиля")
    elif exercise_type == "system":
        # Только админы могут создавать системные упражнения
        if not user_data.is_admin:
            raise HTTPException(status_code=403, detail="Только администраторы могут создавать системные упражнения")

    # Обработка image_uuid
    if values.get('image_uuid'):
        image = await FilesDAO.find_one_or_none(uuid=values.pop('image_uuid'))
        if not image:
            raise HTTPException(status_code=404, detail="Изображение не найдено")
        values['image_id'] = image.id
    # Обработка video_uuid
    if values.get('video_uuid'):
        video = await FilesDAO.find_one_or_none(uuid=values.pop('video_uuid'))
        if not video:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        values['video_id'] = video.id
    # Обработка video_preview_uuid
    if values.get('video_preview_uuid'):
        preview = await FilesDAO.find_one_or_none(uuid=values.pop('video_preview_uuid'))
        if not preview:
            raise HTTPException(status_code=404, detail="Превью видео не найдено")
        values['video_preview_id'] = preview.id
    # Удаляю image_uuid, video_uuid, video_preview_uuid если вдруг остались
    values.pop('image_uuid', None)
    values.pop('video_uuid', None)
    values.pop('video_preview_uuid', None)

    # Обработка exercise_reference_uuid
    if values.get('exercise_reference_uuid'):
        from app.exercise_reference.dao import ExerciseReferenceDAO
        exercise_ref = await ExerciseReferenceDAO.find_one_or_none(uuid=values.pop('exercise_reference_uuid'))
        if exercise_ref:
            values['exercise_reference_id'] = exercise_ref.id
        else:
            values['exercise_reference_id'] = None

    exercise_uuid = await ExerciseDAO.add(**values)
    exercise_obj = await ExerciseDAO.find_full_data(exercise_uuid)
    
    # Формируем ответ как в get_exercise_by_id
    user = await UsersDAO.find_one_or_none(id=exercise_obj.user_id) if exercise_obj.user_id else None
    
    data = exercise_obj.to_dict()
    data.pop('user_id', None)
    data.pop('user_uuid', None)
    data['user'] = await user.to_dict() if user else None
    data["exercise_reference_uuid"] = str(exercise_obj.exercise_reference.uuid) if hasattr(exercise_obj, 'exercise_reference') and exercise_obj.exercise_reference else None
    return data


@router.put("/update/{exercise_uuid}")
async def update_exercise(exercise_uuid: UUID, exercise: SExerciseUpdate, user_data = Depends(get_current_user_user)) -> dict:
    # Проверяем права доступа
    existing_exercise = await ExerciseDAO.find_one_or_none(uuid=exercise_uuid)
    if not existing_exercise:
        raise HTTPException(status_code=404, detail="Упражнение не найдено")
    
    # Если упражнение пользовательское (user), проверяем, что это его упражнение
    if existing_exercise.exercise_type == "user":
        if not existing_exercise.user_id or existing_exercise.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Вы можете редактировать только свои упражнения")
    # Если упражнение системное (system), разрешаем редактировать только админам
    elif existing_exercise.exercise_type == "system":
        if not user_data.is_admin:
            raise HTTPException(status_code=403, detail="Только администраторы могут редактировать системные упражнения")
    
    update_data = exercise.model_dump(exclude_unset=True)
    # Преобразуем user_uuid в user_id, если оно есть
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

    # Обработка video_uuid
    if 'video_uuid' in update_data:
        video_uuid = update_data.pop('video_uuid')
        if video_uuid:
            video = await FilesDAO.find_one_or_none(uuid=video_uuid)
            if not video:
                raise HTTPException(status_code=404, detail="Видео не найдено")
            update_data['video_id'] = video.id
        else:
            update_data['video_id'] = None

    # Обработка exercise_reference_uuid
    if 'exercise_reference_uuid' in update_data:
        from app.exercise_reference.dao import ExerciseReferenceDAO
        exercise_ref = await ExerciseReferenceDAO.find_one_or_none(uuid=update_data.pop('exercise_reference_uuid'))
        if exercise_ref:
            update_data['exercise_reference_id'] = exercise_ref.id
        else:
            update_data['exercise_reference_id'] = None

    check = await ExerciseDAO.update(exercise_uuid, **update_data)
    if check:
        updated_exercise = await ExerciseDAO.find_full_data(exercise_uuid)
        user = await UsersDAO.find_one_or_none(id=updated_exercise.user_id) if updated_exercise.user_id else None
        
        data = updated_exercise.to_dict()
        data.pop('user_id', None)
        data.pop('user_uuid', None)
        data['user'] = await user.to_dict() if user else None
        data["exercise_reference_uuid"] = str(updated_exercise.exercise_reference.uuid) if hasattr(updated_exercise, 'exercise_reference') and updated_exercise.exercise_reference else None
        return data
    else:
        return {"message": "Ошибка при обновлении упражнения!"}


@router.delete("/delete/{exercise_uuid}")
async def delete_exercise_by_id(exercise_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    # Проверяем права доступа
    existing_exercise = await ExerciseDAO.find_one_or_none(uuid=exercise_uuid)
    if not existing_exercise:
        raise HTTPException(status_code=404, detail="Упражнение не найдено")
    
    # Если упражнение пользовательское (user), проверяем, что это его упражнение
    if existing_exercise.exercise_type == "user":
        if not existing_exercise.user_id or existing_exercise.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Вы можете удалять только свои упражнения")
    # Если упражнение системное (system), разрешаем удалять только админам
    elif existing_exercise.exercise_type == "system":
        if not user_data.is_admin:
            raise HTTPException(status_code=403, detail="Только администраторы могут удалять системные упражнения")
    
    check = await ExerciseDAO.delete_by_id(exercise_uuid)
    if check:
        return {"message": f"Упражнение с ID {exercise_uuid} удалено!"}
    else:
        return {"message": "Ошибка при удалении упражнения!"}


@router.post("/{exercise_uuid}/upload-image", summary="Загрузить изображение для упражнения")
async def upload_exercise_image(
    exercise_uuid: UUID,
    file: UploadFile = File(...),
    user_data = Depends(get_current_user_user)
):
    exercise = await ExerciseDAO.find_full_data(exercise_uuid)
    if not exercise:
        raise HTTPException(status_code=404, detail="Упражнение не найдено")
    
    # Проверяем права доступа
    if exercise.exercise_type == "user":
        if not exercise.user_id or exercise.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Вы можете загружать изображения только для своих упражнений")
    elif exercise.exercise_type == "system":
        if not user_data.is_admin:
            raise HTTPException(status_code=403, detail="Только администраторы могут загружать изображения для системных упражнений")
    # Сохраняем файл
    old_file_uuid = getattr(exercise.image, 'uuid', None)
    saved_file = await FileService.save_file(
        file=file,
        entity_type="exercise",
        entity_id=exercise.id,
        old_file_uuid=str(old_file_uuid) if old_file_uuid else None
    )
    # Обновляем image_id у упражнения
    await ExerciseDAO.update(exercise_uuid, image_id=saved_file.id)
    return {"message": "Изображение успешно загружено", "image_uuid": saved_file.uuid}

@router.post("/{exercise_uuid}/upload-video", summary="Загрузить видео для упражнения")
async def upload_exercise_video(
    exercise_uuid: UUID,
    file: UploadFile = File(...),
    user_data = Depends(get_current_user_user)
):
    exercise = await ExerciseDAO.find_full_data(exercise_uuid)
    if not exercise:
        raise HTTPException(status_code=404, detail="Упражнение не найдено")
    
    # Проверяем права доступа
    if exercise.exercise_type == "user":
        if not exercise.user_id or exercise.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Вы можете загружать видео только для своих упражнений")
    elif exercise.exercise_type == "system":
        if not user_data.is_admin:
            raise HTTPException(status_code=403, detail="Только администраторы могут загружать видео для системных упражнений")
    # Сохраняем видео
    old_file_uuid = getattr(exercise.video, 'uuid', None)
    old_preview_uuid = getattr(exercise.video_preview, 'uuid', None)
    video_file, preview_file = await FileService.save_video_file(
        file=file,
        entity_type="exercise",
        entity_id=exercise.id,
        old_file_uuid=str(old_file_uuid) if old_file_uuid else None
    )
    # Обновляем video_id и video_preview_id у упражнения
    await ExerciseDAO.update(
        exercise_uuid,
        video_id=video_file.id,
        video_preview_id=preview_file.id if preview_file else None
    )
    return {
        "message": "Видео успешно загружено",
        "video_uuid": video_file.uuid,
        "video_preview_uuid": preview_file.uuid if preview_file else None
    }
