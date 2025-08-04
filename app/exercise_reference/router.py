from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from app.exercise_reference.dao import ExerciseReferenceDAO
from app.exercise_reference.rb import RBExerciseReference
from app.exercise_reference.schemas import SExerciseReference, SExerciseReferenceAdd, SExerciseReferenceUpdate
from app.users.dependencies import get_current_admin_user, get_current_user_user
from app.files.dao import FilesDAO
from app.files.service import FileService
from app.users.dao import UsersDAO

router = APIRouter(prefix='/exercise_reference', tags=['Справочник упражнений'])

@router.get('/', summary='Получить все упражнения справочника')
async def get_all_exercise_references(request_body: RBExerciseReference = Depends(), user_data = Depends(get_current_user_user)) -> list[dict]:
    exercises = await ExerciseReferenceDAO.find_all(**request_body.to_dict())
    return [e.to_dict() for e in exercises]

@router.get('/search/by-caption', summary='Поиск справочника упражнений по части названия (caption)')
async def search_exercise_reference_by_caption(
    caption: str = Query(..., description="Часть названия упражнения (поиск без учета регистра)"),
    request_body: RBExerciseReference = Depends(),
    user_data = Depends(get_current_user_user)
) -> list[dict]:
    filters = request_body.to_dict()
    results = await ExerciseReferenceDAO.find_by_caption(caption=caption, **filters)
    return [e.to_dict() for e in results]

@router.get('/available/{user_uuid}', summary='Получить все доступные упражнения для пользователя')
async def get_available_exercises(
    user_uuid: UUID,
    user_data = Depends(get_current_user_user)
) -> list[dict]:
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
    
    # Получаем все доступные упражнения
    exercises = await ExerciseReferenceDAO.search_by_caption(
        search_query="",  # Пустая строка для получения всех упражнений
        user_id=user.id
    )
    
    return [e.to_dict() for e in exercises]

@router.get('/{exercise_reference_uuid}', summary='Получить упражнение справочника по uuid')
async def get_exercise_reference_by_id(exercise_reference_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    rez = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
    if rez is None:
        return {'message': f'Упражнение справочника с ID {exercise_reference_uuid} не найдено!'}
    return rez.to_dict()

@router.post('/add/', summary='Создать упражнение справочника')
async def add_exercise_reference(exercise: SExerciseReferenceAdd, user_data = Depends(get_current_admin_user)) -> dict:
    values = exercise.model_dump()
    # Обработка image_uuid
    if values.get('image_uuid'):
        image = await FilesDAO.find_one_or_none(uuid=values['image_uuid'])
        if not image:
            raise HTTPException(status_code=404, detail="Изображение не найдено")
        values['image_id'] = image.id
    values.pop('image_uuid', None)
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
async def update_exercise_reference(exercise_reference_uuid: UUID, exercise: SExerciseReferenceUpdate, user_data = Depends(get_current_admin_user)) -> dict:
    update_data = exercise.model_dump(exclude_unset=True)
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
    if check:
        updated_exercise = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
        return updated_exercise.to_dict()
    else:
        return {'message': 'Ошибка при обновлении упражнения справочника!'}

@router.delete('/delete/{exercise_reference_uuid}', summary='Удалить упражнение справочника')
async def delete_exercise_reference_by_id(exercise_reference_uuid: UUID, user_data = Depends(get_current_admin_user)) -> dict:
    check = await ExerciseReferenceDAO.delete_by_id(exercise_reference_uuid)
    if check:
        return {'message': f'Упражнение справочника с ID {exercise_reference_uuid} удалено!'}
    else:
        return {'message': 'Ошибка при удалении упражнения справочника!'}

@router.post('/{exercise_reference_uuid}/upload-image', summary='Загрузить изображение для справочника упражнения')
async def upload_exercise_reference_image(
    exercise_reference_uuid: UUID,
    file: UploadFile = File(...),
    user_data = Depends(get_current_admin_user)
):
    exercise_reference = await ExerciseReferenceDAO.find_full_data(exercise_reference_uuid)
    if not exercise_reference:
        raise HTTPException(status_code=404, detail="Справочник упражнения не найден")
    old_file_uuid = getattr(exercise_reference.image, 'uuid', None)
    saved_file = await FileService.save_file(
        file=file,
        entity_type="exercise_reference",
        entity_id=exercise_reference.id,
        old_file_uuid=str(old_file_uuid) if old_file_uuid else None
    )
    await ExerciseReferenceDAO.update(exercise_reference_uuid, image_id=saved_file.id)
    return {"message": "Изображение успешно загружено", "image_uuid": saved_file.uuid} 