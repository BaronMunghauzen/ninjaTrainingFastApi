from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from app.user_exercises.dao import UserExerciseDAO
from app.user_exercises.rb import RBUserExercise
from app.user_exercises.schemas import SUserExercise, SUserExerciseAdd, SUserExerciseUpdate, SBatchSetPassedRequest, SBatchSetPassedResponse, SGetLastUserExercisesRequest
from app.users.dependencies import get_current_admin_user, get_current_user_user
from app.programs.dao import ProgramDAO
from app.trainings.dao import TrainingDAO
from app.users.dao import UsersDAO
from app.exercises.dao import ExerciseDAO
from app.user_exercises.models import ExerciseStatus

router = APIRouter(prefix='/user_exercises', tags=['Работа с пользовательскими упражнениями'])


@router.get("/", summary="Получить все пользовательские упражнения")
async def get_all_user_exercises(request_body: RBUserExercise = Depends(), user_data = Depends(get_current_user_user)) -> list[dict]:
    # Используем оптимизированный метод с предзагруженными связанными данными
    user_exercises = await UserExerciseDAO.find_all_with_relations(**request_body.to_dict())
    
    result = []
    for ue in user_exercises:
        data = ue.to_dict()
        # Удаляем id поля
        data.pop('program_id', None)
        data.pop('training_id', None)
        data.pop('user_id', None)
        data.pop('exercise_id', None)
        
        # Используем предзагруженные данные вместо дополнительных запросов
        # Добавляем дополнительные проверки для избежания ошибок
        try:
            data['program'] = ue.program.to_dict() if hasattr(ue, 'program') and ue.program else None
        except Exception:
            data['program'] = None
            
        try:
            data['training'] = ue.training.to_dict() if hasattr(ue, 'training') and ue.training else None
        except Exception:
            data['training'] = None
            
        try:
            data['user'] = await ue.user.to_dict() if hasattr(ue, 'user') and ue.user else None
        except Exception:
            data['user'] = None
            
        try:
            data['exercise'] = ue.exercise.to_dict() if hasattr(ue, 'exercise') and ue.exercise else None
        except Exception:
            data['exercise'] = None
        
        result.append(data)
    
    return result


@router.get("/{user_exercise_uuid}", summary="Получить одно пользовательское упражнение по id")
async def get_user_exercise_by_id(user_exercise_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    # Используем оптимизированный метод с предзагруженными связанными данными
    rez = await UserExerciseDAO.find_full_data_with_relations(user_exercise_uuid)
    if rez is None:
        return {'message': f'Пользовательское упражнение с ID {user_exercise_uuid} не найдено!'}
    
    # Используем предзагруженные данные вместо дополнительных запросов
    data = rez.to_dict()
    data.pop('program_id', None)
    data.pop('training_id', None)
    data.pop('user_id', None)
    data.pop('exercise_id', None)
    
    # Добавляем дополнительные проверки для избежания ошибок
    try:
        data['program'] = rez.program.to_dict() if hasattr(rez, 'program') and rez.program else None
    except Exception:
        data['program'] = None
        
    try:
        data['training'] = rez.training.to_dict() if hasattr(rez, 'training') and rez.training else None
    except Exception:
        data['training'] = None
        
    try:
        data['user'] = await rez.user.to_dict() if hasattr(rez, 'user') and rez.user else None
    except Exception:
        data['user'] = None
        
    try:
        data['exercise'] = rez.exercise.to_dict() if hasattr(rez, 'exercise') and rez.exercise else None
    except Exception:
        data['exercise'] = None
    
    return data


@router.post("/add/")
async def add_user_exercise(user_exercise: SUserExerciseAdd, user_data = Depends(get_current_user_user)) -> dict:
    values = user_exercise.model_dump()
    
    # Получаем program_id по program_uuid, если передан
    program_uuid = values.pop('program_uuid', None)
    if program_uuid:
        program = await ProgramDAO.find_one_or_none(uuid=program_uuid)
        if not program:
            raise HTTPException(status_code=404, detail="Программа не найдена")
        values['program_id'] = program.id
    # если не передан, не добавляем program_id
    
    # Получаем training_id по training_uuid
    training = await TrainingDAO.find_one_or_none(uuid=values.pop('training_uuid'))
    if not training:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    values['training_id'] = training.id
    
    # Получаем user_id по user_uuid
    user = await UsersDAO.find_one_or_none(uuid=values.pop('user_uuid'))
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    values['user_id'] = user.id
    
    # Получаем exercise_id по exercise_uuid
    exercise = await ExerciseDAO.find_one_or_none(uuid=values.pop('exercise_uuid'))
    if not exercise:
        raise HTTPException(status_code=404, detail="Упражнение не найдено")
    values['exercise_id'] = exercise.id
    
    # Фильтруем только те поля, которые есть в модели UserExercise
    valid_fields = {'program_id', 'training_id', 'user_id', 'exercise_id', 'training_date', 'status', 'set_number', 'weight', 'reps'}
    filtered_values = {k: v for k, v in values.items() if k in valid_fields}

    user_exercise_uuid = await UserExerciseDAO.add(**filtered_values)
    
    # Используем оптимизированный метод с предзагруженными связанными данными
    user_exercise_obj = await UserExerciseDAO.find_full_data_with_relations(user_exercise_uuid)
    
    # Формируем ответ используя предзагруженные данные
    data = user_exercise_obj.to_dict()
    data.pop('program_id', None)
    data.pop('training_id', None)
    data.pop('user_id', None)
    data.pop('exercise_id', None)
    
    # Используем предзагруженные данные вместо дополнительных запросов
    try:
        data['program'] = user_exercise_obj.program.to_dict() if hasattr(user_exercise_obj, 'program') and user_exercise_obj.program else None
    except Exception:
        data['program'] = None
        
    try:
        data['training'] = user_exercise_obj.training.to_dict() if hasattr(user_exercise_obj, 'training') and user_exercise_obj.training else None
    except Exception:
        data['training'] = None
        
    try:
        data['user'] = await user_exercise_obj.user.to_dict() if hasattr(user_exercise_obj, 'user') and user_exercise_obj.user else None
    except Exception:
        data['user'] = None
        
    try:
        data['exercise'] = user_exercise_obj.exercise.to_dict() if hasattr(user_exercise_obj, 'exercise') and user_exercise_obj.exercise else None
    except Exception:
        data['exercise'] = None
    
    return data


@router.put("/update/{user_exercise_uuid}")
async def update_user_exercise(user_exercise_uuid: UUID, user_exercise: SUserExerciseUpdate, user_data = Depends(get_current_user_user)) -> dict:
    update_data = user_exercise.model_dump(exclude_unset=True)
    
    # Преобразуем UUID в ID, если они есть
    if 'program_uuid' in update_data:
        program = await ProgramDAO.find_one_or_none(uuid=update_data.pop('program_uuid'))
        if not program:
            raise HTTPException(status_code=404, detail="Программа не найдена")
        update_data['program_id'] = program.id
    
    if 'training_uuid' in update_data:
        training = await TrainingDAO.find_one_or_none(uuid=update_data.pop('training_uuid'))
        if not training:
            raise HTTPException(status_code=404, detail="Тренировка не найдена")
        update_data['training_id'] = training.id
    
    if 'user_uuid' in update_data:
        user = await UsersDAO.find_one_or_none(uuid=update_data.pop('user_uuid'))
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        update_data['user_id'] = user.id
    
    if 'exercise_uuid' in update_data:
        exercise = await ExerciseDAO.find_one_or_none(uuid=update_data.pop('exercise_uuid'))
        if not exercise:
            raise HTTPException(status_code=404, detail="Упражнение не найдено")
        update_data['exercise_id'] = exercise.id

    check = await UserExerciseDAO.update(user_exercise_uuid, **update_data)
    if check:
        # Используем оптимизированный метод с предзагруженными связанными данными
        updated_user_exercise = await UserExerciseDAO.find_full_data_with_relations(user_exercise_uuid)
        
        data = updated_user_exercise.to_dict()
        data.pop('program_id', None)
        data.pop('training_id', None)
        data.pop('user_id', None)
        data.pop('exercise_id', None)
        
        # Используем предзагруженные данные вместо дополнительных запросов
        try:
            data['program'] = updated_user_exercise.program.to_dict() if hasattr(updated_user_exercise, 'program') and updated_user_exercise.program else None
        except Exception:
            data['program'] = None
            
        try:
            data['training'] = updated_user_exercise.training.to_dict() if hasattr(updated_user_exercise, 'training') and updated_user_exercise.training else None
        except Exception:
            data['training'] = None
            
        try:
            data['user'] = await updated_user_exercise.user.to_dict() if hasattr(updated_user_exercise, 'user') and updated_user_exercise.user else None
        except Exception:
            data['user'] = None
            
        try:
            data['exercise'] = updated_user_exercise.exercise.to_dict() if hasattr(updated_user_exercise, 'exercise') and updated_user_exercise.exercise else None
        except Exception:
            data['exercise'] = None
        
        return data
    else:
        return {"message": "Ошибка при обновлении пользовательского упражнения!"}


@router.delete("/delete/{user_exercise_uuid}")
async def delete_user_exercise_by_id(user_exercise_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    check = await UserExerciseDAO.delete_by_id(user_exercise_uuid)
    if check:
        return {"message": f"Пользовательское упражнение с ID {user_exercise_uuid} удалено!"}
    else:
        return {"message": "Ошибка при удалении пользовательского упражнения!"}


@router.patch("/set_passed/{user_exercise_uuid}", summary="Перевести статус user_exercise в PASSED")
async def set_user_exercise_passed(user_exercise_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    # Получаем текущий объект с предзагруженными связанными данными
    user_exercise = await UserExerciseDAO.find_full_data_with_relations(user_exercise_uuid)
    if user_exercise.status == ExerciseStatus.PASSED:
        updated_user_exercise = user_exercise
        check = 1  # имитируем успешное обновление
    else:
        check = await UserExerciseDAO.update(user_exercise_uuid, status=ExerciseStatus.PASSED)
        updated_user_exercise = await UserExerciseDAO.find_full_data_with_relations(user_exercise_uuid) if check else None
    if check and updated_user_exercise:
        # Данные уже предзагружены через find_full_data_with_relations
        data = updated_user_exercise.to_dict()
        data.pop('program_id', None)
        data.pop('training_id', None)
        data.pop('user_id', None)
        data.pop('exercise_id', None)
        
        # Используем предзагруженные данные (без дополнительных запросов)
        data['program'] = updated_user_exercise.program.to_dict() if updated_user_exercise.program else None
        data['training'] = updated_user_exercise.training.to_dict() if updated_user_exercise.training else None
        data['user'] = updated_user_exercise.user.to_dict() if updated_user_exercise.user else None
        data['exercise'] = updated_user_exercise.exercise.to_dict() if updated_user_exercise.exercise else None
        
        return data
    else:
        return {"message": "Ошибка при обновлении статуса!"}


@router.get("/utils/getLastUserExercises", summary="Получить предыдущую тренировку по параметрам")
async def get_last_user_exercises(
    request: SGetLastUserExercisesRequest = Depends(),
    user_data = Depends(get_current_user_user)
) -> dict:
    from datetime import datetime
    # Получаем id по uuid
    program = None
    if request.program_uuid:
        program = await ProgramDAO.find_one_or_none(uuid=request.program_uuid)
        if program is None:
            return {"message": "Программа не найдена"}
    training = None
    if request.training_uuid:
        training = await TrainingDAO.find_one_or_none(uuid=request.training_uuid)
        if training is None:
            return {"message": "Тренировка не найдена"}
    
    user = await UsersDAO.find_one_or_none(uuid=request.user_uuid)
    exercise = await ExerciseDAO.find_one_or_none(uuid=request.exercise_uuid)
    if user is None:
        return {"message": "Пользователь не найден"}
    if exercise is None:
        return {"message": "Упражнение не найдено"}
    
    # Получаем exercise_reference_id из упражнения
    exercise_reference_id = exercise.exercise_reference_id
    if exercise_reference_id is None:
        return {"message": "У упражнения не указан exercise_reference"}
    
    try:
        date_obj = datetime.fromisoformat(request.training_date).date()
    except Exception:
        return {"message": "Некорректный формат даты"}
    
    # Находим все упражнения с тем же exercise_reference_id
    exercises_with_same_reference = await ExerciseDAO.find_all(exercise_reference_id=exercise_reference_id)
    exercise_ids = [ex.id for ex in exercises_with_same_reference]
    
    if not exercise_ids:
        return {"message": "Не найдено упражнений с таким exercise_reference"}
    
    # Ищем предыдущие user_exercises по всем упражнениям с тем же exercise_reference
    search_params = {
        **({"program_id": program.id} if program else {}),
        **({"training_id": training.id} if training else {}),
        "user_id": user.id,
        "set_number": request.set_number
    }
    user_exercises = await UserExerciseDAO.find_all(**search_params)
    # Фильтруем по дате и по упражнениям с тем же exercise_reference
    prev_exs = [
        ue for ue in user_exercises 
        if ue.training_date < date_obj and ue.exercise_id in exercise_ids
    ]
    if not prev_exs:
        return {"message": "Нет предыдущей тренировки"}
    # Находим самую позднюю из предыдущих
    last_ex = max(prev_exs, key=lambda ue: ue.training_date)
    return last_ex.to_dict()


@router.patch("/batch_set_passed", summary="Batch установка статуса PASSED для множества упражнений")
async def batch_set_user_exercises_passed(
    request: SBatchSetPassedRequest,
    user_data = Depends(get_current_user_user)
) -> SBatchSetPassedResponse:
    """
    Batch установка статуса PASSED для множества пользовательских упражнений
    
    Позволяет установить статус PASSED для нескольких упражнений одним запросом.
    Полезно для массовых операций после завершения тренировки.
    
    Args:
        request: Список UUID пользовательских упражнений
        user_data: Данные текущего пользователя
        
    Returns:
        SBatchSetPassedResponse: Детальный результат операции
    """
    try:
        # Вызываем batch метод из DAO
        result = await UserExerciseDAO.batch_set_passed(request.user_exercise_uuids)
        
        return SBatchSetPassedResponse(**result)
        
    except Exception as e:
        # В случае общей ошибки возвращаем все как неудачные
        return SBatchSetPassedResponse(
            success_count=0,
            failed_count=len(request.user_exercise_uuids),
            total_count=len(request.user_exercise_uuids),
            success_uuids=[],
            failed_uuids=request.user_exercise_uuids,
            errors=[f"Общая ошибка batch операции: {str(e)}"]
        )