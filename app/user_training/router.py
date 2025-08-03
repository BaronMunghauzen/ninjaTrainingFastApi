from uuid import UUID
from datetime import datetime, timezone
import traceback

from fastapi import APIRouter, Depends, HTTPException, Query
from app.user_training.dao import UserTrainingDAO
from app.user_training.rb import RBUserTraining
from app.user_training.schemas import SUserTraining, SUserTrainingAdd, SUserTrainingUpdate
from app.users.dependencies import get_current_admin_user, get_current_user_user
from app.user_program.dao import UserProgramDAO
from app.programs.dao import ProgramDAO
from app.trainings.dao import TrainingDAO
from app.users.dao import UsersDAO
from app.services.schedule_generator import ScheduleGenerator

router = APIRouter(prefix='/user_trainings', tags=['Работа с пользовательскими тренировками'])


async def activate_next_training(user_training):
    """Активирует следующую тренировку по дате для той же программы"""
    try:
        # Получаем все тренировки для той же программы, отсортированные по дате
        all_trainings = await UserTrainingDAO.find_all(
            user_program_id=user_training.user_program_id
        )
        
        # Сортируем по дате
        sorted_trainings = sorted(all_trainings, key=lambda x: x.training_date)
        
        # Находим текущую тренировку в списке
        current_index = None
        for i, training in enumerate(sorted_trainings):
            if training.uuid == user_training.uuid:
                current_index = i
                break
        
        if current_index is not None and current_index + 1 < len(sorted_trainings):
            # Берем следующую тренировку
            next_training = sorted_trainings[current_index + 1]
            
            # Проверяем, что следующая тренировка в статусе BLOCKED_YET
            if next_training.status.value == 'blocked_yet':
                # Активируем следующую тренировку
                await UserTrainingDAO.update(next_training.uuid, status='active')
                return True, next_training
        
        return False, None
        
    except Exception as e:
        print(f"Ошибка при активации следующей тренировки: {e}")
        return False, None


async def create_next_stage_if_needed(user_training):
    """Создать следующий этап, если все тренировки текущего этапа завершены"""
    try:
        print(f"[DEBUG] Проверка завершения этапа для user_program_id={user_training.user_program_id}")
        # 1. Проверяем, есть ли активные тренировочные дни (is_rest_day=False)
        active_trainings = await UserTrainingDAO.find_all(user_program_id=user_training.user_program_id, status='active', is_rest_day=False)
        print(f"[DEBUG] Найдено активных тренировочных дней (is_rest_day=False): {len(active_trainings)}")
        # 2. Проверяем, есть ли вообще активные user_training (включая rest day)
        active_any = await UserTrainingDAO.find_all(user_program_id=user_training.user_program_id, status='active')
        print(f"[DEBUG] Найдено всех активных user_training: {len(active_any)}")
        # Если нет ни одной активной тренировки (is_rest_day=False) и ни одной вообще активной user_training (rest day), создаём следующий этап
        if not active_trainings and not active_any:
            from datetime import datetime
            print(f"[DEBUG] Пытаюсь получить user_program id={user_training.user_program_id}")
            user_program = await UserProgramDAO.find_one_or_none(id=user_training.user_program_id)
            print(f"[DEBUG] user_program найден: {user_program is not None}")
            if not user_program:
                print(f"[DEBUG] user_program не найден, выход")
                return False, None
            # Переводим все blocked_yet тренировки (только не rest day) в passed
            print(f"[DEBUG] Пытаюсь найти blocked_yet тренировки для user_program_id={user_training.user_program_id}")
            blocked_trainings = await UserTrainingDAO.find_all(user_program_id=user_training.user_program_id, status='blocked_yet', is_rest_day=False)
            print(f"[DEBUG] blocked_yet тренировок для завершения (is_rest_day=False): {len(blocked_trainings)}")
            for bt in blocked_trainings:
                print(f"[DEBUG] Перевожу тренировку {bt.uuid} в passed")
                await UserTrainingDAO.update(bt.uuid, status='passed')
            print(f"[DEBUG] Перевожу user_program {user_program.uuid} в finished")
            await UserProgramDAO.update(user_program.uuid, status='finished', stopped_at=datetime.now())
            current_stage = user_program.stage
            print(f"[DEBUG] Пытаюсь найти тренировки для stage+1 ({current_stage+1})")
            trainings_next_stage = await TrainingDAO.find_by_program_and_stage(program_id=user_program.program_id, stage=current_stage+1)
            print(f"[DEBUG] Тренировки для stage+1 ({current_stage+1}): {len(trainings_next_stage) if trainings_next_stage else 0}")
            if trainings_next_stage:
                new_stage = current_stage + 1
            else:
                new_stage = current_stage
            new_user_program_data = {
                'program_id': user_program.program_id,
                'user_id': user_program.user_id,
                'caption': user_program.caption,
                'status': 'active',
                'stage': new_stage,
                'schedule_type': user_program.schedule_type,
                'training_days': user_program.training_days,
                'start_date': datetime.now().date()
            }
            print(f"[DEBUG] Данные для новой user_program: {new_user_program_data}")
            new_user_program_id = await UserProgramDAO.add(**new_user_program_data)
            new_user_program = await UserProgramDAO.find_one_or_none(uuid=new_user_program_id)
            print(f"[DEBUG] Новая user_program создана: {new_user_program is not None}, id={getattr(new_user_program, 'id', None)}")
            if not new_user_program:
                print(f"[DEBUG] Не удалось создать новую user_program")
                return False, {"message": "Не удалось создать новую user_program"}
            training_days = ScheduleGenerator.parse_training_days(user_program.training_days)
            print(f"[DEBUG] Дни тренировок для расписания: {training_days}")
            next_stage_info = await ScheduleGenerator.create_next_stage_schedule(
                user_program_id=new_user_program.id,
                program_id=user_program.program_id,
                user_id=user_program.user_id,
                current_stage=current_stage,
                training_days=training_days,
                training_dao=TrainingDAO,
                user_training_dao=UserTrainingDAO
            )
            print(f"[DEBUG] Информация о создании расписания: {next_stage_info}")
            first_training = None
            user_trainings_new = await UserTrainingDAO.find_all(user_program_id=new_user_program.id)
            print(f"[DEBUG] Количество тренировок в новом расписании: {len(user_trainings_new)}")
            for ut in sorted(user_trainings_new, key=lambda x: x.training_date):
                if hasattr(ut, 'status') and ut.status.value.lower() == 'active' and not getattr(ut, 'is_rest_day', False):
                    first_training = ut
                    break
            print(f"[DEBUG] Первая активная тренировка: {getattr(first_training, 'uuid', None)}")
            return next_stage_info.get("created", False), {
                **next_stage_info,
                "new_user_program_uuid": str(new_user_program.uuid) if new_user_program else None,
                "first_training_uuid": str(first_training.uuid) if first_training else None
            }
        print(f"[DEBUG] Этап не завершён, есть ещё активные user_training")
        return False, None
    except Exception as e:
        print(f"[DEBUG] Ошибка при создании следующего этапа: {e}")
        print(traceback.format_exc())
        return False, None


@router.get("/", summary="Получить все пользовательские тренировки")
async def get_all_user_trainings(
    request_body: RBUserTraining = Depends(), 
    user_data = Depends(get_current_user_user),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=100, description="Размер страницы")
) -> dict:
    # Используем оптимизированный метод с пагинацией на уровне БД
    user_trainings, total_count = await UserTrainingDAO.find_all_with_relations_paginated(
        page=page, 
        page_size=page_size, 
        **request_body.to_dict()
    )
    
    # Получаем все связанные ID для batch загрузки
    user_program_ids = {ut.user_program_id for ut in user_trainings}
    user_ids = {ut.user_id for ut in user_trainings}
    program_ids = {ut.program_id for ut in user_trainings if ut.program_id}
    training_ids = {ut.training_id for ut in user_trainings if ut.training_id}
    
    # Batch загрузка всех связанных данных с полной информацией
    user_programs = await UserProgramDAO.find_in('id', list(user_program_ids)) if user_program_ids else []
    users = await UsersDAO.find_in('id', list(user_ids)) if user_ids else []
    
    # Загружаем программы с полной информацией (включая image)
    programs = []
    for program_id in program_ids:
        try:
            program = await ProgramDAO.find_full_data_by_id(program_id)
            programs.append(program)
        except:
            # Если программа не найдена, пропускаем
            pass
    
    # Загружаем тренировки с полной информацией (включая image)
    trainings = []
    for training_id in training_ids:
        try:
            training = await TrainingDAO.find_full_data_by_id(training_id)
            trainings.append(training)
        except:
            # Если тренировка не найдена, пропускаем
            pass
    
    # Создаем словари для быстрого поиска
    id_to_user_program = {up.id: up.to_dict() for up in user_programs}
    id_to_program = {p.id: p.to_dict() for p in programs}
    id_to_training = {t.id: t.to_dict() for t in trainings}
    
    # Обрабатываем пользователей отдельно, так как to_dict() асинхронный
    id_to_user = {}
    for u in users:
        id_to_user[u.id] = await u.to_dict()
    
    result = []
    for ut in user_trainings:
        data = {
            "uuid": str(ut.uuid),
            "status": ut.status.value,
            "training_date": ut.training_date.isoformat() if ut.training_date else None,
            "week": ut.week,
            "weekday": ut.weekday,
            "is_rest_day": ut.is_rest_day,
            "stage": ut.stage
        }
        
        # Используем предзагруженные связанные данные
        data['user_program'] = id_to_user_program.get(ut.user_program_id)
        data['program'] = id_to_program.get(ut.program_id)
        data['training'] = id_to_training.get(ut.training_id)
        data['user'] = id_to_user.get(ut.user_id)
        
        result.append(data)
    
    return {
        "data": result,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count or 0,
            "total_pages": ((total_count or 0) + page_size - 1) // page_size,
            "has_next": page * page_size < (total_count or 0),
            "has_prev": page > 1
        }
    }


@router.get("/{user_training_uuid}", summary="Получить одну пользовательскую тренировку по id")
async def get_user_training_by_id(user_training_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    rez = await UserTrainingDAO.find_full_data(user_training_uuid)
    if rez is None:
        return {'message': f'Пользовательская тренировка с ID {user_training_uuid} не найдена!'}
    
    user_program = await UserProgramDAO.find_one_or_none(id=rez.user_program_id)
    program = await ProgramDAO.find_one_or_none(id=rez.program_id)
    training = await TrainingDAO.find_one_or_none(id=rez.training_id)
    user = await UsersDAO.find_one_or_none(id=rez.user_id)
    
    data = rez.to_dict()
    data.pop('user_program_id', None)
    data.pop('program_id', None)
    data.pop('training_id', None)
    data.pop('user_id', None)
    data['user_program'] = await user_program.to_dict() if user_program else None
    data['program'] = await program.to_dict() if program else None
    data['training'] = await training.to_dict() if training else None
    data['user'] = await user.to_dict() if user else None
    return data


@router.post("/add/")
async def add_user_training(user_training: SUserTrainingAdd, user_data = Depends(get_current_user_user)) -> dict:
    values = user_training.model_dump()
    
    # Проверяем права доступа - пользователь может добавлять тренировки только для себя
    user_uuid = values.get('user_uuid')
    if user_uuid and str(user_uuid) != str(user_data.uuid):
        raise HTTPException(status_code=403, detail="Вы можете добавлять тренировки только для своего профиля")
    
    # Получаем user_program_id по user_program_uuid, если передан
    user_program_uuid = values.pop('user_program_uuid', None)
    if user_program_uuid:
        user_program = await UserProgramDAO.find_one_or_none(uuid=user_program_uuid)
        if not user_program:
            raise HTTPException(status_code=404, detail="Пользовательская программа не найдена")
        # Проверяем, что программа принадлежит текущему пользователю
        if user_program.user_id != user_data.id:
            raise HTTPException(status_code=403, detail="Вы можете добавлять тренировки только для своих программ")
        values['user_program_id'] = user_program.id
    # если не передан, не добавляем user_program_id

    # Получаем program_id по program_uuid, если передан
    program_uuid = values.pop('program_uuid', None)
    if program_uuid:
        program = await ProgramDAO.find_one_or_none(uuid=program_uuid)
        if not program:
            raise HTTPException(status_code=404, detail="Программа не найдена")
        values['program_id'] = program.id
    # если не передан, не добавляем program_id

    # Получаем training_id по training_uuid
    training_uuid = values.pop('training_uuid', None)
    if training_uuid:
        training = await TrainingDAO.find_one_or_none(uuid=training_uuid)
        if not training:
            raise HTTPException(status_code=404, detail="Тренировка не найдена")
        values['training_id'] = training.id
    # если не передан, не добавляем training_id

    # Получаем user_id по user_uuid
    user_uuid = values.pop('user_uuid', None)
    if user_uuid:
        user = await UsersDAO.find_one_or_none(uuid=user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        values['user_id'] = user.id
    # если не передан, не добавляем user_id

    # Если stage не указан, пробуем взять из training
    if 'stage' not in values or values['stage'] is None:
        if 'training_id' in values:
            training = await TrainingDAO.find_full_data_by_id(values['training_id'])
            if training:
                values['stage'] = training.stage

    # Фильтруем только те поля, которые есть в модели UserTraining
    valid_fields = {'user_program_id', 'program_id', 'training_id', 'user_id', 'training_date', 'status', 'stage'}
    filtered_values = {k: v for k, v in values.items() if k in valid_fields}

    user_training_uuid = await UserTrainingDAO.add(**filtered_values)
    user_training_obj = await UserTrainingDAO.find_full_data(user_training_uuid)
    
    # Формируем ответ как в get_user_training_by_id
    user_program = await UserProgramDAO.find_one_or_none(id=user_training_obj.user_program_id) if user_training_obj.user_program_id else None
    program = await ProgramDAO.find_one_or_none(id=user_training_obj.program_id) if user_training_obj.program_id else None
    training = await TrainingDAO.find_full_data_by_id(user_training_obj.training_id) if user_training_obj.training_id else None
    user = await UsersDAO.find_one_or_none(id=user_training_obj.user_id) if user_training_obj.user_id else None
    
    data = user_training_obj.to_dict()
    data.pop('user_program_id', None)
    data.pop('program_id', None)
    data.pop('training_id', None)
    data.pop('user_id', None)
    data['user_program'] = user_program.to_dict() if user_program else None
    data['program'] = program.to_dict() if program else None
    data['training'] = training.to_dict() if training else None
    data['user'] = await user.to_dict() if user else None
    return data


@router.put("/update/{user_training_uuid}")
async def update_user_training(user_training_uuid: UUID, user_training: SUserTrainingUpdate, user_data = Depends(get_current_user_user)) -> dict:
    # Проверяем права доступа - пользователь может обновлять только свои тренировки
    existing_training = await UserTrainingDAO.find_full_data(user_training_uuid)
    if not existing_training:
        raise HTTPException(status_code=404, detail="Пользовательская тренировка не найдена")
    
    if existing_training.user_id != user_data.id:
        raise HTTPException(status_code=403, detail="Вы можете обновлять только свои тренировки")
    
    update_data = user_training.model_dump(exclude_unset=True)
    
    # Преобразуем UUID в ID, если они есть
    if 'user_program_uuid' in update_data:
        user_program = await UserProgramDAO.find_one_or_none(uuid=update_data.pop('user_program_uuid'))
        if not user_program:
            raise HTTPException(status_code=404, detail="Пользовательская программа не найдена")
        update_data['user_program_id'] = user_program.id
    
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

    check = await UserTrainingDAO.update(user_training_uuid, **update_data)
    if check:
        updated_user_training = await UserTrainingDAO.find_full_data(user_training_uuid)
        user_program = await UserProgramDAO.find_one_or_none(id=updated_user_training.user_program_id)
        program = await ProgramDAO.find_one_or_none(id=updated_user_training.program_id)
        training = await TrainingDAO.find_one_or_none(id=updated_user_training.training_id)
        user = await UsersDAO.find_one_or_none(id=updated_user_training.user_id)
        
        data = updated_user_training.to_dict()
        data.pop('user_program_id', None)
        data.pop('program_id', None)
        data.pop('training_id', None)
        data.pop('user_id', None)
        data['user_program'] = await user_program.to_dict() if user_program else None
        data['program'] = await program.to_dict() if program else None
        data['training'] = await training.to_dict() if training else None
        data['user'] = await user.to_dict() if user else None
        return data
    else:
        return {"message": "Ошибка при обновлении пользовательской тренировки!"}


@router.delete("/delete/{user_training_uuid}")
async def delete_user_training_by_id(user_training_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    # Проверяем права доступа - пользователь может удалять только свои тренировки
    existing_training = await UserTrainingDAO.find_full_data(user_training_uuid)
    if not existing_training:
        raise HTTPException(status_code=404, detail="Пользовательская тренировка не найдена")
    
    if existing_training.user_id != user_data.id:
        raise HTTPException(status_code=403, detail="Вы можете удалять только свои тренировки")
    
    check = await UserTrainingDAO.delete_by_id(user_training_uuid)
    if check:
        return {"message": f"Пользовательская тренировка с ID {user_training_uuid} удалена!"}
    else:
        return {"message": "Ошибка при удалении пользовательской тренировки!"}


@router.post("/{user_training_uuid}/pass")
async def pass_user_training(user_training_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    """
    Отметить пользовательскую тренировку как выполненную (PASSED)
    """
    # Получаем user_training
    user_training = await UserTrainingDAO.find_full_data(user_training_uuid)
    if not user_training:
        raise HTTPException(status_code=404, detail="Пользовательская тренировка не найдена")
    
    # Проверяем, что тренировка в активном статусе
    if user_training.status.value.lower() != 'active':
        raise HTTPException(status_code=400, detail=f"Тренировка уже имеет статус {user_training.status.value}")
    
    # Обновляем статус на PASSED и заполняем completed_at
    current_time = datetime.now()
    update_data = {
        'status': 'passed',
        'completed_at': current_time
    }
    
    check = await UserTrainingDAO.update(user_training_uuid, **update_data)
    if not check:
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса тренировки")
    
    # Получаем user_training заново с новым статусом
    user_training = await UserTrainingDAO.find_full_data(user_training_uuid)
    
    # Активируем следующую тренировку
    next_activated, next_training = await activate_next_training(user_training)
    
    # Проверяем, нужно ли создавать следующий этап
    next_stage_created, next_stage_info = await create_next_stage_if_needed(user_training)
    
    response = {
        "message": f"Тренировка {user_training.training_date} выполнена",
        "status": "passed",
        "training_date": user_training.training_date.isoformat(),
        "completed_at": current_time.isoformat(),
        "next_training_activated": next_activated
    }
    
    if next_activated and next_training:
        response["next_training_date"] = next_training.training_date.isoformat()
        response["next_training_uuid"] = str(next_training.uuid)
    
    if next_stage_created and next_stage_info:
        response["next_stage_created"] = True
        response["next_stage_info"] = next_stage_info
        if "new_user_program_uuid" in next_stage_info:
            response["new_user_program_uuid"] = next_stage_info["new_user_program_uuid"]
        if "first_training_uuid" in next_stage_info:
            response["first_training_uuid"] = next_stage_info["first_training_uuid"]
    else:
        response["next_stage_created"] = False
    
    return response


@router.post("/{user_training_uuid}/skip")
async def skip_user_training(user_training_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    """
    Отметить пользовательскую тренировку как пропущенную (SKIPPED)
    """
    # Получаем user_training
    user_training = await UserTrainingDAO.find_full_data(user_training_uuid)
    if not user_training:
        raise HTTPException(status_code=404, detail="Пользовательская тренировка не найдена")
    
    # Проверяем, что тренировка в активном статусе
    if user_training.status.value.lower() != 'active':
        raise HTTPException(status_code=400, detail=f"Тренировка уже имеет статус {user_training.status.value}")
    
    # Обновляем статус на SKIPPED и заполняем skipped_at
    current_time = datetime.now()
    update_data = {
        'status': 'skipped',
        'skipped_at': current_time
    }
    
    check = await UserTrainingDAO.update(user_training_uuid, **update_data)
    if not check:
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса тренировки")
    
    # Получаем user_training заново с новым статусом
    user_training = await UserTrainingDAO.find_full_data(user_training_uuid)
    
    # Активируем следующую тренировку
    next_activated, next_training = await activate_next_training(user_training)
    
    # Проверяем, нужно ли создавать следующий этап
    next_stage_created, next_stage_info = await create_next_stage_if_needed(user_training)
    
    response = {
        "message": f"Тренировка {user_training.training_date} пропущена",
        "status": "skipped",
        "training_date": user_training.training_date.isoformat(),
        "skipped_at": current_time.isoformat(),
        "next_training_activated": next_activated
    }
    
    if next_activated and next_training:
        response["next_training_date"] = next_training.training_date.isoformat()
        response["next_training_uuid"] = str(next_training.uuid)
    
    if next_stage_created and next_stage_info:
        response["next_stage_created"] = True
        response["next_stage_info"] = next_stage_info
        if "new_user_program_uuid" in next_stage_info:
            response["new_user_program_uuid"] = next_stage_info["new_user_program_uuid"]
        if "first_training_uuid" in next_stage_info:
            response["first_training_uuid"] = next_stage_info["first_training_uuid"]
    else:
        response["next_stage_created"] = False
    
    return response
