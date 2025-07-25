from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from app.user_exercises.dao import UserExerciseDAO
from app.user_exercises.rb import RBUserExercise
from app.user_exercises.schemas import SUserExercise, SUserExerciseAdd, SUserExerciseUpdate
from app.users.dependencies import get_current_admin_user, get_current_user_user
from app.programs.dao import ProgramDAO
from app.trainings.dao import TrainingDAO
from app.users.dao import UsersDAO
from app.exercises.dao import ExerciseDAO
from app.user_exercises.models import ExerciseStatus

router = APIRouter(prefix='/user_exercises', tags=['Работа с пользовательскими упражнениями'])


@router.get("/", summary="Получить все пользовательские упражнения")
async def get_all_user_exercises(request_body: RBUserExercise = Depends(), user_data = Depends(get_current_user_user)) -> list[dict]:
    user_exercises = await UserExerciseDAO.find_all(**request_body.to_dict())
    # Получаем все связанные ID
    program_ids = {ue.program_id for ue in user_exercises}
    training_ids = {ue.training_id for ue in user_exercises}
    user_ids = {ue.user_id for ue in user_exercises}
    exercise_ids = {ue.exercise_id for ue in user_exercises}
    
    # Загружаем программы с полной информацией (включая image)
    programs = []
    for program_id in program_ids:
        if program_id is not None:
            try:
                program = await ProgramDAO.find_full_data_by_id(program_id)
                programs.append(program)
            except:
                pass
    # Загружаем тренировки с полной информацией (включая image)
    trainings = []
    for training_id in training_ids:
        try:
            training = await TrainingDAO.find_full_data_by_id(training_id)
            trainings.append(training)
        except:
            pass
    users = await UsersDAO.find_in('id', list(user_ids)) if user_ids else []
    # Загружаем упражнения с полной информацией (включая image)
    exercises = []
    for exercise_id in exercise_ids:
        try:
            exercise = await ExerciseDAO.find_full_data_by_id(exercise_id)
            exercises.append(exercise)
        except:
            pass
    
    id_to_program = {p.id: p.to_dict() for p in programs}
    id_to_training = {t.id: t.to_dict() for t in trainings}
    id_to_user = {u.id: await u.to_dict() for u in users}
    id_to_exercise = {e.id: e.to_dict() for e in exercises}
    
    result = []
    for ue in user_exercises:
        data = ue.to_dict()
        # Удаляем id поля
        data.pop('program_id', None)
        data.pop('training_id', None)
        data.pop('user_id', None)
        data.pop('exercise_id', None)
        # Добавляем вложенные объекты
        data['program'] = id_to_program.get(ue.program_id) if ue.program_id else None
        data['training'] = id_to_training.get(ue.training_id)
        data['user'] = id_to_user.get(ue.user_id)
        data['exercise'] = id_to_exercise.get(ue.exercise_id)
        result.append(data)
    return result


@router.get("/{user_exercise_uuid}", summary="Получить одно пользовательское упражнение по id")
async def get_user_exercise_by_id(user_exercise_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    rez = await UserExerciseDAO.find_full_data(user_exercise_uuid)
    if rez is None:
        return {'message': f'Пользовательское упражнение с ID {user_exercise_uuid} не найдено!'}
    
    program = await ProgramDAO.find_one_or_none(id=rez.program_id)
    training = await TrainingDAO.find_one_or_none(id=rez.training_id)
    user = await UsersDAO.find_one_or_none(id=rez.user_id)
    exercise = await ExerciseDAO.find_one_or_none(id=rez.exercise_id)
    
    data = rez.to_dict()
    data.pop('program_id', None)
    data.pop('training_id', None)
    data.pop('user_id', None)
    data.pop('exercise_id', None)
    data['program'] = program.to_dict() if program else None
    data['training'] = training.to_dict() if training else None
    data['user'] = await user.to_dict() if user else None
    data['exercise'] = exercise.to_dict() if exercise else None
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
    user_exercise_obj = await UserExerciseDAO.find_full_data(user_exercise_uuid)
    
    # Формируем ответ как в get_user_exercise_by_id
    # Загружаем program, training, exercise с полной информацией
    program = await ProgramDAO.find_full_data_by_id(user_exercise_obj.program_id) if user_exercise_obj.program_id else None
    training = await TrainingDAO.find_full_data_by_id(user_exercise_obj.training_id)
    exercise_obj = await ExerciseDAO.find_one_or_none(id=user_exercise_obj.exercise_id)
    exercise = await ExerciseDAO.find_full_data(exercise_obj.uuid) if exercise_obj else None
    user = await UsersDAO.find_one_or_none(id=user_exercise_obj.user_id)
    
    data = user_exercise_obj.to_dict()
    data.pop('program_id', None)
    data.pop('training_id', None)
    data.pop('user_id', None)
    data.pop('exercise_id', None)
    data['program'] = program.to_dict() if program else None
    data['training'] = training.to_dict() if training else None
    data['user'] = await user.to_dict() if user else None
    data['exercise'] = exercise.to_dict() if exercise else None
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
        updated_user_exercise = await UserExerciseDAO.find_full_data(user_exercise_uuid)
        program = await ProgramDAO.find_one_or_none(id=updated_user_exercise.program_id)
        training = await TrainingDAO.find_one_or_none(id=updated_user_exercise.training_id)
        user = await UsersDAO.find_one_or_none(id=updated_user_exercise.user_id)
        exercise = await ExerciseDAO.find_one_or_none(id=updated_user_exercise.exercise_id)
        
        data = updated_user_exercise.to_dict()
        data.pop('program_id', None)
        data.pop('training_id', None)
        data.pop('user_id', None)
        data.pop('exercise_id', None)
        data['program'] = program.to_dict() if program else None
        data['training'] = training.to_dict() if training else None
        data['user'] = await user.to_dict() if user else None
        data['exercise'] = exercise.to_dict() if exercise else None
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
    # Получаем текущий объект
    user_exercise = await UserExerciseDAO.find_full_data(user_exercise_uuid)
    if user_exercise.status == ExerciseStatus.PASSED:
        updated_user_exercise = user_exercise
        check = 1  # имитируем успешное обновление
    else:
        check = await UserExerciseDAO.update(user_exercise_uuid, status=ExerciseStatus.PASSED)
        updated_user_exercise = await UserExerciseDAO.find_full_data(user_exercise_uuid) if check else None
    if check and updated_user_exercise:
        program = await ProgramDAO.find_full_data_by_id(updated_user_exercise.program_id)
        training = await TrainingDAO.find_full_data_by_id(updated_user_exercise.training_id)
        exercise_obj = await ExerciseDAO.find_one_or_none(id=updated_user_exercise.exercise_id)
        exercise = await ExerciseDAO.find_full_data(exercise_obj.uuid) if exercise_obj else None
        user = await UsersDAO.find_one_or_none(id=updated_user_exercise.user_id)
        data = updated_user_exercise.to_dict()
        data.pop('program_id', None)
        data.pop('training_id', None)
        data.pop('user_id', None)
        data.pop('exercise_id', None)
        data['program'] = program.to_dict() if program else None
        data['training'] = training.to_dict() if training else None
        data['user'] = await user.to_dict() if user else None
        data['exercise'] = exercise.to_dict() if exercise else None
        return data
    else:
        return {"message": "Ошибка при обновлении статуса!"}


@router.get("/utils/getLastUserExercises", summary="Получить предыдущую тренировку по параметрам")
async def get_last_user_exercises(
    program_uuid: UUID = Query(None),
    training_uuid: UUID = Query(...),
    user_uuid: UUID = Query(...),
    set_number: int = Query(...),
    exercise_uuid: UUID = Query(...),
    training_date: str = Query(...),
    user_data = Depends(get_current_user_user)
) -> dict:
    from datetime import datetime
    # Получаем id по uuid
    program = None
    if program_uuid:
        program = await ProgramDAO.find_one_or_none(uuid=program_uuid)
        if program is None:
            return {"message": "Программа не найдена"}
    training = await TrainingDAO.find_one_or_none(uuid=training_uuid)
    user = await UsersDAO.find_one_or_none(uuid=user_uuid)
    exercise = await ExerciseDAO.find_one_or_none(uuid=exercise_uuid)
    if training is None:
        return {"message": "Тренировка не найдена"}
    if user is None:
        return {"message": "Пользователь не найден"}
    if exercise is None:
        return {"message": "Упражнение не найдено"}
    try:
        date_obj = datetime.fromisoformat(training_date).date()
    except Exception:
        return {"message": "Некорректный формат даты"}
    # Ищем предыдущую user_exercise
    user_exercises = await UserExerciseDAO.find_all(
        **({"program_id": program.id} if program else {}),
        training_id=training.id,
        user_id=user.id,
        exercise_id=exercise.id,
        set_number=set_number
    )
    # Фильтруем по дате
    prev_exs = [ue for ue in user_exercises if ue.training_date < date_obj]
    if not prev_exs:
        return {"message": "Нет предыдущей тренировки"}
    # Находим самую позднюю из предыдущих
    last_ex = max(prev_exs, key=lambda ue: ue.training_date)
    return last_ex.to_dict()
