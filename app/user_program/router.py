from uuid import UUID
from datetime import datetime, timezone, date, timedelta
import json

from fastapi import APIRouter, Depends, HTTPException
from app.user_program.dao import UserProgramDAO
from app.user_program.rb import RBUserProgram
from app.user_program.schemas import SUserProgram, SUserProgramAdd, SUserProgramUpdate
from app.users.dependencies import get_current_admin_user, get_current_user_user
from app.programs.dao import ProgramDAO
from app.users.dao import UsersDAO
from app.trainings.dao import TrainingDAO
from app.user_training.dao import UserTrainingDAO
from app.services.schedule_generator import ScheduleGenerator

router = APIRouter(prefix='/user_programs', tags=['Работа с пользовательскими программами'])


@router.get("/", summary="Получить все пользовательские программы")
async def get_all_user_programs(request_body: RBUserProgram = Depends(), user_data = Depends(get_current_user_user)) -> list[dict]:
    # Используем оптимизированный метод вместо find_all + N+1 запросов
    result = await UserProgramDAO.find_all_with_programs_and_users(**request_body.to_dict())
    return result


@router.get("/{user_program_uuid}", summary="Получить одну пользовательскую программу по id")
async def get_user_program_by_id(user_program_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    rez = await UserProgramDAO.find_full_data(user_program_uuid)
    if rez is None:
        return {'message': f'Пользовательская программа с ID {user_program_uuid} не найдена!'}
    # Используем оптимизированный метод для получения программы
    program = await ProgramDAO.find_by_id_with_image(rez.program_id) if rez.program_id else None
    user = await UsersDAO.find_one_or_none(id=rez.user_id) if rez.user_id else None
    data = {
        "uuid": str(rez.uuid),
        "caption": rez.caption,
        "status": rez.status,
        "stopped_at": rez.stopped_at.isoformat() if rez.stopped_at else None,
        "stage": rez.stage,
        "schedule_type": rez.schedule_type,
        "training_days": rez.training_days,
        "start_date": rez.start_date.isoformat() if rez.start_date else None,
        "program": program.to_dict() if program else None,
        "user": await user.to_dict() if user else None
    }
    return data


@router.post("/add/")
async def add_user_program(user_program: SUserProgramAdd, user_data = Depends(get_current_user_user)) -> dict:
    values = user_program.model_dump()
    
    # Получаем program_id по program_uuid
    program = await ProgramDAO.find_one_or_none(uuid=values.pop('program_uuid'))
    if not program:
        raise HTTPException(status_code=404, detail="Программа не найдена")
    values['program_id'] = program.id

    # Аналогично для user_uuid, если нужно
    user_id = None
    if values.get('user_uuid'):
        user = await UsersDAO.find_one_or_none(uuid=values.pop('user_uuid'))
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        user_id = user.id
    values['user_id'] = user_id
    
    # Удаляем user_uuid из values если он остался
    values.pop('user_uuid', None)
    
    # Используем расписание из программы
    values['schedule_type'] = program.schedule_type
    values['training_days'] = program.training_days
    
    # Фильтруем только те поля, которые есть в модели UserProgram
    valid_fields = {'program_id', 'user_id', 'caption', 'status', 'stage', 'schedule_type', 'training_days'}
    filtered_values = {k: v for k, v in values.items() if k in valid_fields}

    user_program_uuid = await UserProgramDAO.add(**filtered_values)
    user_program_obj = await UserProgramDAO.find_full_data(user_program_uuid)
    
    # Создаем user_trainings на основе расписания программы
    try:
        # Получаем дни тренировок из программы (теперь это дни программы, а не дни недели)
        training_days = ScheduleGenerator.parse_training_days(program.training_days)
        from datetime import date, timedelta
        today = date.today()
        # Начинаем с текущего дня
        start_date = today
        # Получаем тренировки программы только с stage=1
        trainings = await TrainingDAO.find_all(program_id=program.id, stage=1)
        if trainings:
            # Генерируем даты тренировок на ближайшие 28 дней
            total_days = 28
            created_count = 0
            trainings_count = 0
            for day_offset in range(total_days):
                current_date = start_date + timedelta(days=day_offset)
                # Вычисляем день программы (1-7, циклически)
                program_day = ((day_offset % 7) + 1)
                week = (day_offset // 7) + 1
                # weekday теперь содержит день программы, а не день недели
                weekday = program_day
                
                if program_day in training_days:
                    training = trainings[trainings_count % len(trainings)]
                    # Статус: 'active' если дата совпадает с today, иначе 'blocked_yet'
                    status = 'active' if current_date == today else 'blocked_yet'
                    user_training_data = {
                        'user_program_id': user_program_obj.id,
                        'program_id': program.id,
                        'training_id': training.id,
                        'user_id': user_program_obj.user_id,
                        'training_date': current_date,
                        'status': status,
                        'week': week,
                        'weekday': weekday,
                        'is_rest_day': False
                    }
                    trainings_count += 1
                else:
                    # Статус: 'active' если дата совпадает с today (даже для дней отдыха), иначе 'blocked_yet'
                    status = 'active' if current_date == today else 'blocked_yet'
                    user_training_data = {
                        'user_program_id': user_program_obj.id,
                        'program_id': program.id,
                        'training_id': None,
                        'user_id': user_program_obj.user_id,
                        'training_date': current_date,
                        'status': status,
                        'week': week,
                        'weekday': weekday,
                        'is_rest_day': True
                    }
                await UserTrainingDAO.add(**user_training_data)
                created_count += 1
            # Добавляем информацию о созданном расписании в ответ
            schedule_created = True
            schedule_count = created_count
        else:
            schedule_created = False
            schedule_count = 0
            
    except Exception as e:
        # Логируем ошибку, но не прерываем создание программы
        print(f"Ошибка при создании расписания: {e}")
        schedule_created = False
        schedule_count = 0
    
    # Формируем ответ вручную
    # Используем оптимизированный метод для получения программы
    program = await ProgramDAO.find_by_id_with_image(user_program_obj.program_id) if user_program_obj.program_id else None
    user = await UsersDAO.find_one_or_none(id=user_program_obj.user_id) if user_program_obj.user_id else None
    data = {
        "uuid": str(user_program_obj.uuid),
        "caption": user_program_obj.caption,
        "status": user_program_obj.status,
        "stopped_at": user_program_obj.stopped_at.isoformat() if user_program_obj.stopped_at else None,
        "stage": user_program_obj.stage,
        "schedule_type": user_program_obj.schedule_type,
        "training_days": user_program_obj.training_days,
        "start_date": user_program_obj.start_date.isoformat() if user_program_obj.start_date else None,
        "program": program.to_dict() if program else None,
        "user": await user.to_dict() if user else None,
        "schedule_created": schedule_created if 'schedule_created' in locals() else False,
        "schedule_count": schedule_count if 'schedule_count' in locals() else 0
    }
    
    return data


@router.put("/update/{user_program_uuid}")
async def update_user_program(user_program_uuid: UUID, user_program: SUserProgramUpdate, user_data = Depends(get_current_admin_user)) -> dict:
    update_data = user_program.model_dump(exclude_unset=True)
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

    # Обрабатываем training_days
    if 'training_days' in update_data:
        update_data['training_days'] = json.dumps(update_data['training_days'])

    check = await UserProgramDAO.update(user_program_uuid, **update_data)
    if check:
        updated_user_program = await UserProgramDAO.find_full_data(user_program_uuid)
        # Используем оптимизированный метод для получения программы
        program = await ProgramDAO.find_by_id_with_image(updated_user_program.program_id) if updated_user_program.program_id else None
        user = await UsersDAO.find_one_or_none(id=updated_user_program.user_id) if updated_user_program.user_id else None
        data = updated_user_program.to_dict()
        data.pop('program_id', None)
        data.pop('user_id', None)
        data.pop('program_uuid', None)
        data.pop('user_uuid', None)
        data['program'] = await program.to_dict() if program else None
        data['user'] = await user.to_dict() if user else None
        return data
    else:
        return {"message": "Ошибка при обновлении пользовательской программы!"}


@router.delete("/delete/{user_program_uuid}")
async def delete_user_program_by_id(user_program_uuid: UUID, user_data = Depends(get_current_admin_user)) -> dict:
    check = await UserProgramDAO.delete_by_id(user_program_uuid)
    if check:
        return {"message": f"Пользовательская программа с ID {user_program_uuid} удалена!"}
    else:
        return {"message": "Ошибка при удалении пользовательской программы!"}


@router.post("/finish/{user_program_uuid}")
async def finish_user_program(user_program_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    """
    Завершить пользовательскую программу:
    1) Проставить статус 'finished'
    2) Проставить stopped_at текущей датой
    3) Удалить все user_trainings для этой программы
    """
    # Получаем user_program
    user_program = await UserProgramDAO.find_full_data(user_program_uuid)
    if not user_program:
        raise HTTPException(status_code=404, detail="Пользовательская программа не найдена")
    
    # Обновляем статус и stopped_at
    update_data = {
        'status': 'finished',
        'stopped_at': datetime.now()
    }
    
    check = await UserProgramDAO.update(user_program_uuid, **update_data)
    if not check:
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса программы")
    
    # Удаляем все user_trainings для этой программы
    try:
        # Получаем все user_trainings для этой программы
        user_trainings = await UserTrainingDAO.find_all(user_program_id=user_program.id)
        
        deleted_count = 0
        for user_training in user_trainings:
            deleted = await UserTrainingDAO.delete_by_id(user_training.uuid)
            if deleted:
                deleted_count += 1
        
        return {
            "message": f"Программа {user_program.caption} успешно завершена!",
            "status": "finished",
            "stopped_at": update_data['stopped_at'].isoformat(),
            "deleted_trainings": deleted_count
        }
        
    except Exception as e:
        # Если не удалось удалить тренировки, все равно возвращаем успех
        # так как основная задача (завершение программы) выполнена
        print(f"Ошибка при удалении тренировок: {e}")
        return {
            "message": f"Программа {user_program.caption} завершена, но возникли проблемы с удалением расписания",
            "status": "finished",
            "stopped_at": update_data['stopped_at'].isoformat(),
            "warning": "Не все тренировки были удалены"
        }
