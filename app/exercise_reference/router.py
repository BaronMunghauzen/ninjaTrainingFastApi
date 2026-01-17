from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from app.exercise_reference.dao import ExerciseReferenceDAO
from app.exercise_reference.models import ExerciseReference
from app.exercise_reference.rb import RBExerciseReference
from app.exercise_reference.schemas import SExerciseReference, SExerciseReferenceAdd, SExerciseReferenceUpdate, SPaginationResponse, SExerciseStatistics, SExerciseFilters
from app.users.dependencies import get_current_admin_user, get_current_user_user
from app.files.dao import FilesDAO
from app.files.service import FileService
from app.users.dao import UsersDAO
from app.user_favorite_exercises.dao import UserFavoriteExerciseDAO
from app.logger import logger

router = APIRouter(prefix='/exercise_reference', tags=['Справочник упражнений'])

@router.get('/', summary='Получить все упражнения справочника')
async def get_all_exercise_references(
    page: int = Query(1, ge=0, description="Номер страницы (0 для получения всех элементов)"),
    size: int = Query(20, ge=0, description="Размер страницы (0 для получения всех элементов)"),
    request_body: RBExerciseReference = Depends(), 
    user_data = Depends(get_current_user_user)
) -> SPaginationResponse:
    filters = request_body.to_dict()
    
    # Если пагинация не нужна (page=0 или size=0), используем старый метод
    if page == 0 or size == 0:
        exercises = await ExerciseReferenceDAO.find_all(favorite_user_id=user_data.id, **filters)
        items = [e.to_dict() for e in exercises]
        # Добавляем is_favorite к каждому упражнению
        favorite_ids = await UserFavoriteExerciseDAO.get_user_favorite_exercise_ids(user_data.id)
        for exercise, item in zip(exercises, items):
            item['is_favorite'] = exercise.id in favorite_ids
        
        return SPaginationResponse(
            items=items,
            total=len(items),
            page=0,
            size=0,
            pages=1
        )
    
    # Используем новый метод с пагинацией
    result = await ExerciseReferenceDAO.find_all_paginated(
        page=page,
        size=size,
        favorite_user_id=user_data.id,
        **filters
    )
    
    # Преобразуем объекты в словари для ответа
    items = [e.to_dict() for e in result["items"]]
    # Добавляем is_favorite к каждому упражнению
    favorite_ids = await UserFavoriteExerciseDAO.get_user_favorite_exercise_ids(user_data.id)
    for exercise, item in zip(result["items"], items):
        item['is_favorite'] = exercise.id in favorite_ids
    
    return SPaginationResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        size=result["size"],
        pages=result["pages"]
    )

@router.get('/search/by-caption', summary='Поиск справочника упражнений по части названия (caption)')
async def search_exercise_reference_by_caption(
    caption: Optional[str] = Query(None, description="Часть названия упражнения (поиск без учета регистра)"),
    muscle_groups: Optional[str] = Query(None, description="Фильтр по группам мышц (список через запятую, поиск в muscle_group и auxiliary_muscle_groups)"),
    equipment_names: Optional[str] = Query(None, description="Фильтр по названиям оборудования (список через запятую)"),
    page: int = Query(1, ge=0, description="Номер страницы (0 для получения всех элементов)"),
    size: int = Query(20, ge=0, description="Размер страницы (0 для получения всех элементов)"),
    request_body: RBExerciseReference = Depends(),
    user_data = Depends(get_current_user_user)
) -> SPaginationResponse:
    filters = request_body.to_dict()
    
    # Обрабатываем списки фильтров
    muscle_groups_list = None
    if muscle_groups and muscle_groups.strip():
        muscle_groups_list = [mg.strip() for mg in muscle_groups.split(',') if mg.strip()]
    
    equipment_names_list = None
    if equipment_names and equipment_names.strip():
        equipment_names_list = [en.strip() for en in equipment_names.split(',') if en.strip()]
    
    result = await ExerciseReferenceDAO.find_by_caption_paginated(
        caption=caption or "", 
        page=page, 
        size=size,
        muscle_groups_filter=muscle_groups_list,
        equipment_names_filter=equipment_names_list,
        favorite_user_id=user_data.id,
        **filters
    )
    
    # Преобразуем объекты в словари для ответа
    items = [e.to_dict() for e in result["items"]]
    # Добавляем is_favorite к каждому упражнению
    favorite_ids = await UserFavoriteExerciseDAO.get_user_favorite_exercise_ids(user_data.id)
    for exercise, item in zip(result["items"], items):
        item['is_favorite'] = exercise.id in favorite_ids
    
    return SPaginationResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        size=result["size"],
        pages=result["pages"]
    )

@router.get('/available/{user_uuid}', summary='Получить все доступные упражнения для пользователя')
async def get_available_exercises(
    user_uuid: UUID,
    page: int = Query(1, ge=0, description="Номер страницы (0 для получения всех элементов)"),
    size: int = Query(20, ge=0, description="Размер страницы (0 для получения всех элементов)"),
    user_data = Depends(get_current_user_user)
) -> SPaginationResponse:
    """
    Получить все доступные упражнения для пользователя:
    - Все системные упражнения (exercise_type = "system")
    - Все пользовательские упражнения, созданные этим пользователем (exercise_type = "user" и user_id = id пользователя)
    """
    # Проверяем права доступа - пользователь может получить упражнения только для себя
    if str(user_uuid) != str(user_data.uuid):
        raise HTTPException(status_code=403, detail="Вы можете получить упражнения только для своего профиля")
    
    # Получаем ID пользователя
    user = await UsersDAO.find_one_or_none(uuid=user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем все доступные упражнения с пагинацией
    result = await ExerciseReferenceDAO.search_by_caption_paginated(
        search_query="",  # Пустая строка для получения всех упражнений
        user_id=user.id,
        page=page,
        size=size,
        favorite_user_id=user.id
    )
    
    # Преобразуем объекты в словари для ответа
    items = [e.to_dict() for e in result["items"]]
    # Добавляем is_favorite к каждому упражнению
    favorite_ids = await UserFavoriteExerciseDAO.get_user_favorite_exercise_ids(user.id)
    for exercise, item in zip(result["items"], items):
        item['is_favorite'] = exercise.id in favorite_ids
    
    return SPaginationResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        size=result["size"],
        pages=result["pages"]
    )

@router.get('/available/{user_uuid}/search/by-caption', summary='Поиск доступных упражнений по части названия (caption)')
async def search_available_exercises_by_caption(
    user_uuid: UUID,
    caption: Optional[str] = Query(None, description="Часть названия упражнения (поиск без учета регистра)"),
    muscle_groups: Optional[str] = Query(None, description="Фильтр по группам мышц (список через запятую, поиск в muscle_group и auxiliary_muscle_groups)"),
    equipment_names: Optional[str] = Query(None, description="Фильтр по названиям оборудования (список через запятую)"),
    page: int = Query(1, ge=0, description="Номер страницы (0 для получения всех элементов)"),
    size: int = Query(20, ge=0, description="Размер страницы (0 для получения всех элементов)"),
    user_data = Depends(get_current_user_user)
) -> SPaginationResponse:
    """
    Поиск доступных упражнений для пользователя по части названия:
    - Все системные упражнения (exercise_type = "system"), содержащие caption
    - Все пользовательские упражнения, созданные этим пользователем (exercise_type = "user" и user_id = id пользователя), содержащие caption
    """
    # Проверяем права доступа - пользователь может получить упражнения только для себя
    if str(user_uuid) != str(user_data.uuid):
        raise HTTPException(status_code=403, detail="Вы можете получить упражнения только для своего профиля")
    
    # Получаем ID пользователя
    user = await UsersDAO.find_one_or_none(uuid=user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Обрабатываем списки фильтров
    muscle_groups_list = None
    if muscle_groups and muscle_groups.strip():
        muscle_groups_list = [mg.strip() for mg in muscle_groups.split(',') if mg.strip()]
    
    equipment_names_list = None
    if equipment_names and equipment_names.strip():
        equipment_names_list = [en.strip() for en in equipment_names.split(',') if en.strip()]
    
    # Получаем доступные упражнения по caption с пагинацией
    result = await ExerciseReferenceDAO.search_by_caption_paginated(
        search_query=caption or "",
        user_id=user.id,
        page=page,
        size=size,
        muscle_groups_filter=muscle_groups_list,
        equipment_names_filter=equipment_names_list,
        favorite_user_id=user.id
    )
    
    # Преобразуем объекты в словари для ответа
    items = [e.to_dict() for e in result["items"]]
    # Добавляем is_favorite к каждому упражнению
    favorite_ids = await UserFavoriteExerciseDAO.get_user_favorite_exercise_ids(user.id)
    for exercise, item in zip(result["items"], items):
        item['is_favorite'] = exercise.id in favorite_ids
    
    return SPaginationResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        size=result["size"],
        pages=result["pages"]
    )

@router.get('/filters/{user_uuid}', summary='Получить фильтры для упражнений пользователя')
async def get_exercise_filters(
    user_uuid: UUID,
    user_data = Depends(get_current_user_user)
) -> SExerciseFilters:
    """
    Получить фильтры для упражнений пользователя:
    - Список уникальных групп мышц
    - Список уникальных названий оборудования
    """
    # Проверяем права доступа - пользователь может получить фильтры только для себя
    if str(user_uuid) != str(user_data.uuid):
        raise HTTPException(status_code=403, detail="Вы можете получить фильтры только для своего профиля")
    
    # Получаем ID пользователя
    user = await UsersDAO.find_one_or_none(uuid=user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем фильтры
    filters = await ExerciseReferenceDAO.get_exercise_filters(user_id=user.id)
    
    return SExerciseFilters(
        muscle_groups=filters["muscle_groups"],
        equipment_names=filters["equipment_names"]
    )

@router.get('/system/filters', summary='Получить фильтры для системных упражнений')
async def get_system_exercise_filters(
    user_data = Depends(get_current_user_user)
) -> SExerciseFilters:
    """
    Получить фильтры для системных упражнений:
    - Список уникальных групп мышц
    - Список уникальных названий оборудования
    Только для упражнений с exercise_type = "system"
    """
    # Получаем фильтры только для системных упражнений
    filters = await ExerciseReferenceDAO.get_system_exercise_filters()
    
    return SExerciseFilters(
        muscle_groups=filters["muscle_groups"],
        equipment_names=filters["equipment_names"]
    )

@router.get('/{exercise_reference_uuid}', summary='Получить упражнение справочника по uuid')
async def get_exercise_reference_by_id(exercise_reference_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    rez = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
    if rez is None:
        return {'message': f'Упражнение справочника с ID {exercise_reference_uuid} не найдено!'}
    result = rez.to_dict()
    # Добавляем is_favorite
    is_fav = await UserFavoriteExerciseDAO.is_favorite(user_data.id, rez.id)
    result['is_favorite'] = is_fav
    return result

@router.post('/add/', summary='Создать упражнение справочника')
async def add_exercise_reference(exercise: SExerciseReferenceAdd, user_data = Depends(get_current_user_user)) -> dict:
    values = exercise.model_dump()
    # Обработка image_uuid
    if values.get('image_uuid'):
        image = await FilesDAO.find_one_or_none(uuid=values['image_uuid'])
        if not image:
            raise HTTPException(status_code=404, detail="Изображение не найдено")
        values['image_id'] = image.id
    values.pop('image_uuid', None)
    # Обработка video_uuid
    if values.get('video_uuid'):
        video = await FilesDAO.find_one_or_none(uuid=values['video_uuid'])
        if not video:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        values['video_id'] = video.id
    values.pop('video_uuid', None)
    # Обработка gif_uuid
    if values.get('gif_uuid'):
        gif = await FilesDAO.find_one_or_none(uuid=values['gif_uuid'])
        if not gif:
            raise HTTPException(status_code=404, detail="Гифка не найдена")
        values['gif_id'] = gif.id
    values.pop('gif_uuid', None)
    # Обработка user_uuid
    if values.get('user_uuid'):
        user = await UsersDAO.find_one_or_none(uuid=values['user_uuid'])
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        values['user_id'] = user.id
    values.pop('user_uuid', None)
    exercise_uuid = await ExerciseReferenceDAO.add(**values)
    exercise_obj = await ExerciseReferenceDAO.find_full_data(exercise_uuid)
    return exercise_obj.to_dict()

@router.put('/update/{exercise_reference_uuid}', summary='Обновить упражнение справочника')
async def update_exercise_reference(exercise_reference_uuid: UUID, exercise: SExerciseReferenceUpdate, user_data = Depends(get_current_user_user)) -> dict:
    # Проверяем права доступа
    existing_exercise = await ExerciseReferenceDAO.find_one_or_none(uuid=exercise_reference_uuid)
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
    
    # Специальная обработка для technique_description - фиксируем факт присутствия поля и его значение
    raw_data = exercise.model_dump()
    technique_description_present = 'technique_description' in raw_data
    technique_description_value = raw_data.get('technique_description', None)
    
    # Отладочная информация
    print(f"DEBUG: raw_data = {raw_data}")
    print(f"DEBUG: update_data before = {update_data}")
    print(f"DEBUG: technique_description_present = {technique_description_present}, value = {technique_description_value}")
    
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
    # Обработка gif_uuid
    if 'gif_uuid' in update_data:
        gif_uuid = update_data.pop('gif_uuid')
        if gif_uuid:
            gif = await FilesDAO.find_one_or_none(uuid=gif_uuid)
            if not gif:
                raise HTTPException(status_code=404, detail="Гифка не найдена")
            update_data['gif_id'] = gif.id
        else:
            update_data['gif_id'] = None
    # Обработка user_uuid
    if 'user_uuid' in update_data:
        user_uuid = update_data.pop('user_uuid')
        if user_uuid:
            user = await UsersDAO.find_one_or_none(uuid=user_uuid)
            if not user:
                raise HTTPException(status_code=404, detail="Пользователь не найден")
            update_data['user_id'] = user.id
        else:
            update_data['user_id'] = None
    check = await ExerciseReferenceDAO.update(exercise_reference_uuid, **update_data)
    
    # Специальная обработка для technique_description - обновляем напрямую в БД, если поле присутствовало в запросе
    if technique_description_present:
        from sqlalchemy import update as sqlalchemy_update
        from app.database import async_session_maker
        async with async_session_maker() as session:
            async with session.begin():
                query = (
                    sqlalchemy_update(ExerciseReference)
                    .where(ExerciseReference.uuid == exercise_reference_uuid)
                    .values(technique_description=technique_description_value)
                )
                await session.execute(query)
                await session.commit()
                print(f"DEBUG: technique_description обновлен напрямую в БД: {technique_description_value}")
    
    if check or technique_description_present:
        updated_exercise = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
        return updated_exercise.to_dict()
    else:
        return {'message': 'Ошибка при обновлении упражнения справочника!'}

@router.delete('/delete/{exercise_reference_uuid}', summary='Удалить упражнение справочника')
async def delete_exercise_reference_by_id(exercise_reference_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    # Проверяем права доступа
    existing_exercise = await ExerciseReferenceDAO.find_one_or_none(uuid=exercise_reference_uuid)
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
    
    check = await ExerciseReferenceDAO.delete_by_id(exercise_reference_uuid)
    if check:
        return {'message': f'Упражнение справочника с ID {exercise_reference_uuid} удалено!'}
    else:
        return {'message': 'Ошибка при удалении упражнения справочника!'}

@router.post('/{exercise_reference_uuid}/upload-image', summary='Загрузить изображение для справочника упражнения')
async def upload_exercise_reference_image(
    exercise_reference_uuid: UUID,
    file: UploadFile = File(...),
    user_data = Depends(get_current_user_user)
):
    print(f"Начинаем загрузку изображения для exercise_reference: {exercise_reference_uuid}")
    
    exercise_reference = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
    if not exercise_reference:
        raise HTTPException(status_code=404, detail="Справочник упражнения не найден")
    
    # Проверяем права доступа
    if exercise_reference.exercise_type == "user":
        if not exercise_reference.user_id or exercise_reference.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Вы можете загружать изображения только для своих упражнений")
    elif exercise_reference.exercise_type == "system":
        if not user_data.is_admin:
            raise HTTPException(status_code=403, detail="Только администраторы могут загружать изображения для системных упражнений")
    
    print(f"Найден exercise_reference: {exercise_reference.id}")
    old_file_uuid = getattr(exercise_reference.image, 'uuid', None)
    print(f"Старый файл UUID: {old_file_uuid}")
    
    print("Вызываем FileService.save_file...")
    saved_file = await FileService.save_file(
        file=file,
        entity_type="exercise_reference",
        entity_id=exercise_reference.id,
        old_file_uuid=str(old_file_uuid) if old_file_uuid else None
    )
    print(f"Файл сохранен, UUID: {saved_file.uuid}")
    
    print("Обновляем exercise_reference...")
    await ExerciseReferenceDAO.update(exercise_reference_uuid, image_id=saved_file.id)
    print("Exercise_reference обновлен")
    
    return {"message": "Изображение успешно загружено", "image_uuid": saved_file.uuid}

@router.delete('/{exercise_reference_uuid}/delete-image', summary='Удалить изображение справочника упражнения')
async def delete_exercise_reference_image(
    exercise_reference_uuid: UUID,
    user_data = Depends(get_current_user_user)
):
    exercise_reference = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
    if not exercise_reference:
        raise HTTPException(status_code=404, detail="Справочник упражнения не найден")
    
    # Проверяем права доступа
    if exercise_reference.exercise_type == "user":
        if not exercise_reference.user_id or exercise_reference.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Вы можете удалять изображения только для своих упражнений")
    elif exercise_reference.exercise_type == "system":
        if not user_data.is_admin:
            raise HTTPException(status_code=403, detail="Только администраторы могут удалять изображения для системных упражнений")
    
    if not exercise_reference.image:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    
    image_uuid = exercise_reference.image.uuid
    # Сначала обновляем ссылку в exercise_reference
    await ExerciseReferenceDAO.update(exercise_reference_uuid, image_id=None)
    # Потом удаляем файл
    try:
        await FileService.delete_file_by_uuid(str(image_uuid))
    except Exception as e:
        # Если удаление файла не удалось, возвращаем ошибку
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении файла: {str(e)}")
    
    return {"message": "Изображение успешно удалено"}

@router.post('/{exercise_reference_uuid}/upload-video', summary='Загрузить видео для справочника упражнения')
async def upload_exercise_reference_video(
    exercise_reference_uuid: UUID,
    file: UploadFile = File(...),
    user_data = Depends(get_current_admin_user)
):
    print(f"Начинаем загрузку видео для exercise_reference: {exercise_reference_uuid}")
    
    exercise_reference = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
    if not exercise_reference:
        raise HTTPException(status_code=404, detail="Справочник упражнения не найден")
    
    print(f"Найден exercise_reference: {exercise_reference.id}")
    old_file_uuid = getattr(exercise_reference.video, 'uuid', None)
    print(f"Старый файл UUID: {old_file_uuid}")
    
    print("Вызываем FileService.save_video_file...")
    saved_file = await FileService.save_video_file(
        file=file,
        entity_type="exercise_reference",
        entity_id=exercise_reference.id,
        old_file_uuid=str(old_file_uuid) if old_file_uuid else None
    )
    print(f"Видео сохранено, UUID: {saved_file.uuid}")
    
    print("Обновляем exercise_reference...")
    await ExerciseReferenceDAO.update(exercise_reference_uuid, video_id=saved_file.id)
    print("Exercise_reference обновлен")
    
    return {"message": "Видео успешно загружено", "video_uuid": saved_file.uuid}

@router.delete('/{exercise_reference_uuid}/delete-video', summary='Удалить видео справочника упражнения')
async def delete_exercise_reference_video(
    exercise_reference_uuid: UUID,
    user_data = Depends(get_current_admin_user)
):
    exercise_reference = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
    if not exercise_reference:
        raise HTTPException(status_code=404, detail="Справочник упражнения не найден")
    
    if not exercise_reference.video:
        raise HTTPException(status_code=404, detail="Видео не найдено")
    
    video_uuid = exercise_reference.video.uuid
    # Сначала обновляем ссылку в exercise_reference
    await ExerciseReferenceDAO.update(exercise_reference_uuid, video_id=None)
    # Потом удаляем файл
    try:
        await FileService.delete_file_by_uuid(str(video_uuid))
    except Exception as e:
        # Если удаление файла не удалось, возвращаем ошибку
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении файла: {str(e)}")
    
    return {"message": "Видео успешно удалено"}

@router.post('/{exercise_reference_uuid}/upload-gif', summary='Загрузить гифку для справочника упражнения')
async def upload_exercise_reference_gif(
    exercise_reference_uuid: UUID,
    file: UploadFile = File(...),
    user_data = Depends(get_current_admin_user)
):
    print(f"Начинаем загрузку гифки для exercise_reference: {exercise_reference_uuid}")
    
    exercise_reference = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
    if not exercise_reference:
        raise HTTPException(status_code=404, detail="Справочник упражнения не найден")
    
    print(f"Найден exercise_reference: {exercise_reference.id}")
    old_file_uuid = getattr(exercise_reference.gif, 'uuid', None)
    print(f"Старый файл UUID: {old_file_uuid}")
    
    print("Вызываем FileService.save_file...")
    saved_file = await FileService.save_file(
        file=file,
        entity_type="exercise_reference",
        entity_id=exercise_reference.id,
        old_file_uuid=str(old_file_uuid) if old_file_uuid else None
    )
    print(f"Файл сохранен, UUID: {saved_file.uuid}")
    
    print("Обновляем exercise_reference...")
    await ExerciseReferenceDAO.update(exercise_reference_uuid, gif_id=saved_file.id)
    print("Exercise_reference обновлен")
    
    return {"message": "Гифка успешно загружена", "gif_uuid": saved_file.uuid}

@router.delete('/{exercise_reference_uuid}/delete-gif', summary='Удалить гифку справочника упражнения')
async def delete_exercise_reference_gif(
    exercise_reference_uuid: UUID,
    user_data = Depends(get_current_admin_user)
):
    exercise_reference = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
    if not exercise_reference:
        raise HTTPException(status_code=404, detail="Справочник упражнения не найден")
    
    if not exercise_reference.gif:
        raise HTTPException(status_code=404, detail="Гифка не найдена")
    
    gif_uuid = exercise_reference.gif.uuid
    # Сначала обновляем ссылку в exercise_reference напрямую в БД
    from sqlalchemy import update as sqlalchemy_update
    from app.database import async_session_maker
    async with async_session_maker() as session:
        async with session.begin():
            query = (
                sqlalchemy_update(ExerciseReference)
                .where(ExerciseReference.uuid == exercise_reference_uuid)
                .values(gif_id=None)
            )
            await session.execute(query)
            await session.commit()
            print(f"DEBUG: gif_id обновлен на NULL в БД")
    
    # Потом удаляем файл
    try:
        await FileService.delete_file_by_uuid(str(gif_uuid))
    except Exception as e:
        # Если удаление файла не удалось, возвращаем ошибку
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении файла: {str(e)}")
    
    return {"message": "Гифка успешно удалена"}

@router.get('/{exercise_reference_uuid}/statistics/{user_uuid}', summary='Получить статистику выполнения упражнения для пользователя')
async def get_exercise_statistics(
    exercise_reference_uuid: UUID,
    user_uuid: UUID,
    user_data = Depends(get_current_user_user)
) -> SExerciseStatistics:
    """
    Получить статистику выполнения упражнения для конкретного пользователя.
    Возвращает историю выполнения упражнения с записями из таблицы user_exercise,
    где status = PASSED, сгруппированную по дням в порядке от новых к старым.
    """
    # Проверяем права доступа - пользователь может получить статистику только для себя
    if str(user_uuid) != str(user_data.uuid):
        raise HTTPException(status_code=403, detail="Вы можете получить статистику только для своего профиля")
    
    statistics = await ExerciseReferenceDAO.get_exercise_statistics(exercise_reference_uuid, user_uuid)
    if statistics is None:
        raise HTTPException(status_code=404, detail="Упражнение или пользователь не найдены")
    
    return SExerciseStatistics(**statistics)


@router.get('/passed/', summary='Получить упражнения с выполненными записями')
async def get_passed_exercise_references(
    caption: str = Query(None, description="Поиск по названию упражнения (без учета регистра, частичное совпадение)"),
    user_data = Depends(get_current_user_user)
) -> list[dict]:
    """
    Получить уникальные упражнения из exercise_reference, 
    по которым у текущего пользователя есть записи в user_exercise со статусом PASSED
    """
    try:
        exercises = await ExerciseReferenceDAO.find_passed_exercises(user_uuid=user_data.uuid, caption=caption)
        
        if not exercises:
            return []
        
        # Получаем все избранные ID для оптимизации
        favorite_ids = await UserFavoriteExerciseDAO.get_user_favorite_exercise_ids(user_data.id)
        
        result = []
        for exercise in exercises:
            try:
                # Формируем упрощенный ответ с только нужными полями
                data = {
                    'uuid': str(exercise.uuid),
                    'caption': exercise.caption,
                    'description': exercise.description,
                    'muscle_group': exercise.muscle_group,
                    'gif_uuid': str(exercise.gif.uuid) if exercise.gif else None,
                    'is_favorite': exercise.id in favorite_ids
                }
                
                result.append(data)
            except Exception as ex:
                print(f"Ошибка при обработке упражнения {exercise.id}: {ex}")
                continue
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении упражнений: {str(e)}"
        )


@router.post('/{exercise_reference_uuid}/favorite', summary='Добавить упражнение в избранное')
async def add_exercise_to_favorites(
    exercise_reference_uuid: UUID,
    user_data = Depends(get_current_user_user)
) -> dict:
    """Добавляет упражнение в избранное текущего пользователя"""
    try:
        # Получаем упражнение
        exercise = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
        if not exercise:
            raise HTTPException(status_code=404, detail="Упражнение не найдено")
        
        # Добавляем в избранное
        favorite_uuid = await UserFavoriteExerciseDAO.add_to_favorites(
            user_id=user_data.id,
            exercise_reference_id=exercise.id
        )
        
        return {
            "message": "Упражнение добавлено в избранное",
            "exercise_reference_uuid": str(exercise_reference_uuid),
            "favorite_uuid": str(favorite_uuid)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при добавлении упражнения в избранное {exercise_reference_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при добавлении упражнения в избранное: {str(e)}"
        )


@router.delete('/{exercise_reference_uuid}/favorite', summary='Удалить упражнение из избранного')
async def remove_exercise_from_favorites(
    exercise_reference_uuid: UUID,
    user_data = Depends(get_current_user_user)
) -> dict:
    """Удаляет упражнение из избранного текущего пользователя"""
    try:
        # Получаем упражнение
        exercise = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
        if not exercise:
            raise HTTPException(status_code=404, detail="Упражнение не найдено")
        
        # Удаляем из избранного
        removed = await UserFavoriteExerciseDAO.remove_from_favorites(
            user_id=user_data.id,
            exercise_reference_id=exercise.id
        )
        
        if not removed:
            raise HTTPException(status_code=404, detail="Упражнение не найдено в избранном")
        
        return {
            "message": "Упражнение удалено из избранного",
            "exercise_reference_uuid": str(exercise_reference_uuid)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении упражнения из избранного {exercise_reference_uuid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении упражнения из избранного: {str(e)}"
        ) 