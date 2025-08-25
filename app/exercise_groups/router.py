from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from app.exercise_groups.dao import ExerciseGroupDAO
from app.exercise_groups.rb import RBExerciseGroup
from app.exercise_groups.schemas import SExerciseGroup, SExerciseGroupAdd, SExerciseGroupUpdate
from app.users.dependencies import get_current_admin_user, get_current_user_user
from app.trainings.dao import TrainingDAO
from app.exercises.dao import ExerciseDAO
from app.files.dao import FilesDAO
from app.files.service import FileService

router = APIRouter(prefix='/exercise-groups', tags=['Работа с группами упражнений'])


@router.get("/", summary="Получить все группы упражнений")
async def get_all_exercise_groups(request_body: RBExerciseGroup = Depends(), user_data = Depends(get_current_user_user)) -> list[dict]:
    exercise_groups = await ExerciseGroupDAO.find_all(**request_body.to_dict())
    result = []
    for eg in exercise_groups:
        # Безопасно формируем ответ, не обращаясь к связанным объектам
        data = {
            "uuid": str(eg.uuid),
            "caption": eg.caption,
            "description": eg.description,
            "exercises": eg.get_exercises(),
            "difficulty_level": eg.difficulty_level,
            "order": eg.order,
            "muscle_group": eg.muscle_group,
            "stage": eg.stage,
            "image_uuid": str(eg.image.uuid) if hasattr(eg, 'image') and eg.image else None
        }
        
        # Безопасно добавляем данные тренировки
        if eg.training:
            try:
                data['training'] = {
                    "uuid": str(eg.training.uuid),
                    "training_type": eg.training.training_type,
                    "caption": eg.training.caption,
                    "description": eg.training.description,
                    "difficulty_level": eg.training.difficulty_level,
                    "duration": eg.training.duration,
                    "order": eg.training.order,
                    "muscle_group": eg.training.muscle_group,
                    "stage": eg.training.stage,
                    "image_uuid": str(eg.training.image.uuid) if hasattr(eg.training, 'image') and eg.training.image else None,
                    "actual": eg.training.actual
                }
            except Exception:
                data['training'] = None
        else:
            data['training'] = None
        
        result.append(data)
    return result


@router.get("/{exercise_group_uuid}", summary="Получить одну группу упражнений по id")
async def get_exercise_group_by_id(exercise_group_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    rez = await ExerciseGroupDAO.find_full_data(exercise_group_uuid)
    if rez is None:
        return {'message': f'Группа упражнений с ID {exercise_group_uuid} не найдена!'}
    
    # Безопасно формируем ответ, не обращаясь к связанным объектам
    data = {
        "uuid": str(rez.uuid),
        "caption": rez.caption,
        "description": rez.description,
        "exercises": rez.get_exercises(),
        "difficulty_level": rez.difficulty_level,
        "order": rez.order,
        "muscle_group": rez.muscle_group,
        "stage": rez.stage,
        "image_uuid": str(rez.image.uuid) if hasattr(rez, 'image') and rez.image else None
    }
    
    # Безопасно добавляем данные тренировки
    if rez.training:
        try:
            data['training'] = {
                "uuid": str(rez.training.uuid),
                "training_type": rez.training.training_type,
                "caption": rez.training.caption,
                "description": rez.training.description,
                "difficulty_level": rez.training.difficulty_level,
                "duration": rez.training.duration,
                "order": rez.training.order,
                "muscle_group": rez.training.muscle_group,
                "stage": rez.training.stage,
                "image_uuid": str(rez.training.image.uuid) if hasattr(rez.training, 'image') and rez.training.image else None,
                "actual": rez.training.actual
            }
        except Exception:
            data['training'] = None
    else:
        data['training'] = None
    
    return data


@router.post("/add/")
async def add_exercise_group(exercise_group: SExerciseGroupAdd, user_data = Depends(get_current_admin_user)) -> dict:
    values = exercise_group.model_dump()
    # Получаем training_id по training_uuid, если передан
    if values.get('training_uuid'):
        training = await TrainingDAO.find_one_or_none(uuid=values.pop('training_uuid'))
        if not training:
            raise HTTPException(status_code=404, detail="Тренировка не найдена")
        values['training_id'] = training.id
    else:
        # Удаляем training_uuid из values, если оно None
        values.pop('training_uuid', None)

    # Обработка image_uuid
    if values.get('image_uuid'):
        image = await FilesDAO.find_one_or_none(uuid=values.pop('image_uuid'))
        if not image:
            raise HTTPException(status_code=404, detail="Изображение не найдено")
        values['image_id'] = image.id
    # Удаляю image_uuid если вдруг остался
    values.pop('image_uuid', None)

    # Сохраняем exercises как JSON строку сразу
    exercises_list = values.pop('exercises', None)
    values['exercises'] = json.dumps(exercises_list) if exercises_list else '[]'

    # muscle_group и stage делаем необязательными
    if 'muscle_group' in values and values['muscle_group'] is None:
        values.pop('muscle_group')
    if 'stage' in values and values['stage'] is None:
        values.pop('stage')

    exercise_group_uuid = await ExerciseGroupDAO.add(**values)
    exercise_group_obj = await ExerciseGroupDAO.find_full_data(exercise_group_uuid)
    
    # Безопасно формируем ответ, не обращаясь к связанным объектам
    data = {
        "uuid": str(exercise_group_obj.uuid),
        "caption": exercise_group_obj.caption,
        "description": exercise_group_obj.description,
        "exercises": exercise_group_obj.get_exercises(),
        "difficulty_level": exercise_group_obj.difficulty_level,
        "order": exercise_group_obj.order,
        "muscle_group": exercise_group_obj.muscle_group,
        "stage": exercise_group_obj.stage,
        "image_uuid": str(exercise_group_obj.image.uuid) if hasattr(exercise_group_obj, 'image') and exercise_group_obj.image else None
    }
    
    # Безопасно добавляем данные тренировки
    if exercise_group_obj.training:
        try:
            data['training'] = {
                "uuid": str(exercise_group_obj.training.uuid),
                "training_type": exercise_group_obj.training.training_type,
                "caption": exercise_group_obj.training.caption,
                "description": exercise_group_obj.training.description,
                "difficulty_level": exercise_group_obj.training.difficulty_level,
                "duration": exercise_group_obj.training.duration,
                "order": exercise_group_obj.training.order,
                "muscle_group": exercise_group_obj.training.muscle_group,
                "stage": exercise_group_obj.training.stage,
                "image_uuid": str(exercise_group_obj.training.image.uuid) if hasattr(exercise_group_obj.training, 'image') and exercise_group_obj.training.image else None,
                "actual": exercise_group_obj.training.actual
            }
        except Exception:
            data['training'] = None
    else:
        data['training'] = None
    
    return data


@router.put("/update/{exercise_group_uuid}")
async def update_exercise_group(exercise_group_uuid: UUID, exercise_group: SExerciseGroupUpdate, user_data = Depends(get_current_admin_user)) -> dict:
    update_data = exercise_group.model_dump(exclude_unset=True)
    # Преобразуем training_uuid в training_id, если оно есть
    if 'training_uuid' in update_data:
        training = await TrainingDAO.find_one_or_none(uuid=update_data.pop('training_uuid'))
        if not training:
            raise HTTPException(status_code=404, detail="Тренировка не найдена")
        update_data['training_id'] = training.id

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

    # Обрабатываем exercises отдельно
    exercises_list = update_data.pop('exercises', None)
    if exercises_list is not None:
        update_data['exercises'] = json.dumps(exercises_list) if exercises_list else '[]'
    # Если exercises не передан вообще, ничего не делаем

    check = await ExerciseGroupDAO.update(exercise_group_uuid, **update_data)
    if check:
        updated_exercise_group = await ExerciseGroupDAO.find_full_data(exercise_group_uuid)
        
        # Безопасно формируем ответ, не обращаясь к связанным объектам
        data = {
            "uuid": str(updated_exercise_group.uuid),
            "caption": updated_exercise_group.caption,
            "description": updated_exercise_group.description,
            "exercises": updated_exercise_group.get_exercises(),
            "difficulty_level": updated_exercise_group.difficulty_level,
            "order": updated_exercise_group.order,
            "muscle_group": updated_exercise_group.muscle_group,
            "stage": updated_exercise_group.stage,
            "image_uuid": str(updated_exercise_group.image.uuid) if hasattr(updated_exercise_group, 'image') and updated_exercise_group.image else None
        }
        
        # Безопасно добавляем данные тренировки
        if updated_exercise_group.training:
            try:
                data['training'] = {
                    "uuid": str(updated_exercise_group.training.uuid),
                    "training_type": updated_exercise_group.training.training_type,
                    "caption": updated_exercise_group.training.caption,
                    "description": updated_exercise_group.training.description,
                    "difficulty_level": updated_exercise_group.training.difficulty_level,
                    "duration": updated_exercise_group.training.duration,
                    "order": updated_exercise_group.training.order,
                    "muscle_group": updated_exercise_group.training.muscle_group,
                    "stage": updated_exercise_group.training.stage,
                    "image_uuid": str(updated_exercise_group.training.image.uuid) if hasattr(updated_exercise_group.training, 'image') and updated_exercise_group.training.image else None,
                    "actual": updated_exercise_group.training.actual
                }
            except Exception:
                data['training'] = None
        else:
            data['training'] = None
        
        return data
    else:
        return {"message": "Ошибка при обновлении группы упражнений!"}


@router.delete("/delete/{exercise_group_uuid}")
async def delete_exercise_group_by_id(exercise_group_uuid: UUID, user_data = Depends(get_current_admin_user)) -> dict:
    check = await ExerciseGroupDAO.delete_by_id(exercise_group_uuid)
    if check:
        return {"message": f"Группа упражнений с ID {exercise_group_uuid} удалена!"}
    else:
        return {"message": "Ошибка при удалении группы упражнений!"} 


@router.post("/{exercise_group_uuid}/upload-image", summary="Загрузить изображение для группы упражнений")
async def upload_exercise_group_image(
    exercise_group_uuid: UUID,
    file: UploadFile = File(...),
    user_data = Depends(get_current_admin_user)
):
    exercise_group = await ExerciseGroupDAO.find_full_data(exercise_group_uuid)
    if not exercise_group:
        raise HTTPException(status_code=404, detail="Группа упражнений не найдена")
    old_file_uuid = getattr(exercise_group.image, 'uuid', None)
    saved_file = await FileService.save_file(
        file=file,
        entity_type="exercise_group",
        entity_id=exercise_group.id,
        old_file_uuid=str(old_file_uuid) if old_file_uuid else None
    )
    await ExerciseGroupDAO.update(exercise_group_uuid, image_id=saved_file.id)
    return {"message": "Изображение успешно загружено", "image_uuid": saved_file.uuid}


@router.delete("/{exercise_group_uuid}/delete-image", summary="Удалить изображение группы упражнений")
async def delete_exercise_group_image(
    exercise_group_uuid: UUID,
    user_data = Depends(get_current_admin_user)
):
    exercise_group = await ExerciseGroupDAO.find_full_data(exercise_group_uuid)
    if not exercise_group:
        raise HTTPException(status_code=404, detail="Группа упражнений не найдена")
    
    if not exercise_group.image:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    
    image_uuid = exercise_group.image.uuid
    # Удаляем файл (это автоматически очистит image_id в exercise_groups и запись в files)
    try:
        await FileService.delete_file_by_uuid(str(image_uuid))
    except Exception as e:
        # Если удаление файла не удалось, возвращаем ошибку
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении файла: {str(e)}")
    
    return {"message": "Изображение успешно удалено"} 


@router.post("/{exercise_group_uuid}/add-exercise", summary="Добавить упражнение в группу упражнений")
async def add_exercise_to_group(
    exercise_group_uuid: UUID,
    exercise_uuid: UUID = Body(..., embed=True),
    user_data = Depends(get_current_admin_user)
):
    group = await ExerciseGroupDAO.find_full_data(exercise_group_uuid)
    if not group:
        raise HTTPException(status_code=404, detail="Группа упражнений не найдена")
    exercises = group.get_exercises() if hasattr(group, 'get_exercises') else []
    if str(exercise_uuid) in exercises:
        return {"message": "Упражнение уже есть в группе"}
    exercises.append(str(exercise_uuid))
    await ExerciseGroupDAO.update(exercise_group_uuid, exercises=json.dumps(exercises))
    return {"message": "Упражнение добавлено в группу", "exercises": exercises}

@router.post("/{exercise_group_uuid}/remove-exercise", summary="Удалить упражнение из группы упражнений")
async def remove_exercise_from_group(
    exercise_group_uuid: UUID,
    exercise_uuid: UUID = Body(..., embed=True),
    user_data = Depends(get_current_admin_user)
):
    group = await ExerciseGroupDAO.find_full_data(exercise_group_uuid)
    if not group:
        raise HTTPException(status_code=404, detail="Группа упражнений не найдена")
    exercises = group.get_exercises() if hasattr(group, 'get_exercises') else []
    if str(exercise_uuid) not in exercises:
        return {"message": "Упражнения нет в группе"}
    exercises = [e for e in exercises if e != str(exercise_uuid)]
    await ExerciseGroupDAO.update(exercise_group_uuid, exercises=json.dumps(exercises))
    return {"message": "Упражнение удалено из группы", "exercises": exercises} 