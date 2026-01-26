from uuid import UUID
from datetime import datetime, timezone
import traceback
import asyncio
import threading

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from app.user_training.dao import UserTrainingDAO
from app.user_training.rb import RBUserTraining
from app.user_training.schemas import SUserTraining, SUserTrainingAdd, SUserTrainingUpdate
from app.users.dependencies import get_current_admin_user, get_current_user_user
from app.user_program.dao import UserProgramDAO
from app.programs.dao import ProgramDAO
from app.trainings.dao import TrainingDAO
from app.users.dao import UsersDAO
from app.user_exercises.dao import UserExerciseDAO
from app.user_exercises.models import ExerciseStatus
from app.services.schedule_generator import ScheduleGenerator
from app.logger import logger

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
            if next_training.status.value == 'BLOCKED_YET':
                # Активируем следующую тренировку
                await UserTrainingDAO.update(next_training.uuid, status='ACTIVE')
                return True, next_training
        
        return False, None
        
    except Exception as e:
        print(f"Ошибка при активации следующей тренировки: {e}")
        return False, None


async def finish_program_if_completed(user_training):
    """Завершить программу, если все тренировки выполнены"""
    try:
        if not user_training.user_program_id:
            return False
        
        # Проверяем, есть ли активные тренировочные дни (is_rest_day=False)
        active_trainings = await UserTrainingDAO.find_all(
            user_program_id=user_training.user_program_id, 
            status='ACTIVE', 
            is_rest_day=False
        )
        
        # Проверяем, есть ли вообще активные user_training (включая rest day)
        active_any = await UserTrainingDAO.find_all(
            user_program_id=user_training.user_program_id, 
            status='ACTIVE'
        )
        
        # Если нет ни одной активной тренировки, завершаем программу
        if not active_trainings and not active_any:
            user_program = await UserProgramDAO.find_one_or_none(id=user_training.user_program_id)
            if not user_program:
                return False
            
            # Переводим все blocked_yet тренировки (только не rest day) в passed
            blocked_trainings = await UserTrainingDAO.find_all(
                user_program_id=user_training.user_program_id, 
                status='BLOCKED_YET', 
                is_rest_day=False
            )
            for bt in blocked_trainings:
                await UserTrainingDAO.update(bt.uuid, status='PASSED')
            
            # Переводим user_program в finished
            await UserProgramDAO.update(
                user_program.uuid, 
                status='finished', 
                stopped_at=datetime.now()
            )
            logger.info(f"Программа {user_program.uuid} переведена в статус 'finished'")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Ошибка при завершении программы: {e}")
        logger.error(traceback.format_exc())
        return False


async def create_next_stage_if_needed(user_training):
    """Создать следующий этап, если все тренировки текущего этапа завершены"""
    try:
        print(f"[DEBUG] Проверка завершения этапа для user_program_id={user_training.user_program_id}")
        # 1. Проверяем, есть ли активные тренировочные дни (is_rest_day=False)
        active_trainings = await UserTrainingDAO.find_all(user_program_id=user_training.user_program_id, status='ACTIVE', is_rest_day=False)
        print(f"[DEBUG] Найдено активных тренировочных дней (is_rest_day=False): {len(active_trainings)}")
        # 2. Проверяем, есть ли вообще активные user_training (включая rest day)
        active_any = await UserTrainingDAO.find_all(user_program_id=user_training.user_program_id, status='ACTIVE')
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
            blocked_trainings = await UserTrainingDAO.find_all(user_program_id=user_training.user_program_id, status='BLOCKED_YET', is_rest_day=False)
            print(f"[DEBUG] blocked_yet тренировок для завершения (is_rest_day=False): {len(blocked_trainings)}")
            for bt in blocked_trainings:
                print(f"[DEBUG] Перевожу тренировку {bt.uuid} в passed")
                await UserTrainingDAO.update(bt.uuid, status='PASSED')
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
                'status': 'ACTIVE',
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
                if hasattr(ut, 'status') and ut.status.value == 'ACTIVE' and not getattr(ut, 'is_rest_day', False):
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
    page_size: int = Query(50, ge=1, le=100, description="Размер страницы"),
    is_rest_day: bool = Query(None, description="Фильтр по дню отдыха (true/false)")
) -> dict:
    # Используем оптимизированный метод с полными связанными данными
    filters = request_body.to_dict()
    if is_rest_day is not None:
        filters['is_rest_day'] = is_rest_day
    
    result, total_count = await UserTrainingDAO.find_all_with_full_relations_paginated(
        page=page, 
        page_size=page_size, 
        **filters
    )
    
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
    # Используем оптимизированный метод для получения тренировки с предзагруженным image
    training = await TrainingDAO.find_by_id_with_image(rez.training_id) if rez.training_id else None
    user = await UsersDAO.find_one_or_none(id=rez.user_id)
    
    data = rez.to_dict()
    data.pop('user_program_id', None)
    data.pop('program_id', None)
    data.pop('training_id', None)
    data.pop('user_id', None)
    data['user_program'] = user_program.to_dict() if user_program else None
    data['program'] = program.to_dict() if program else None
    data['training'] = training.to_dict() if training else None
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
            # Используем оптимизированный метод для получения тренировки
            training = await TrainingDAO.find_by_id_with_image(values['training_id'])
            if training:
                values['stage'] = training.stage

    # Фильтруем только те поля, которые есть в модели UserTraining
    valid_fields = {'user_program_id', 'program_id', 'training_id', 'user_id', 'training_date', 'status', 'stage', 'is_rest_day', 'week', 'weekday'}
    filtered_values = {k: v for k, v in values.items() if k in valid_fields}

    user_training_uuid = await UserTrainingDAO.add(**filtered_values)
    user_training_obj = await UserTrainingDAO.find_full_data(user_training_uuid)
    
    # Формируем ответ как в get_user_training_by_id
    user_program = await UserProgramDAO.find_one_or_none(id=user_training_obj.user_program_id) if user_training_obj.user_program_id else None
    program = await ProgramDAO.find_one_or_none(id=user_training_obj.program_id) if user_training_obj.program_id else None
    # Используем оптимизированный метод для получения тренировки
    training = await TrainingDAO.find_by_id_with_image(user_training_obj.training_id) if user_training_obj.training_id else None
    user = await UsersDAO.find_one_or_none(id=user_training_obj.user_id) if user_training_obj.user_id else None
    
    # Отправляем FCM уведомление, если program_id отсутствует
    if user_training_obj.program_id is None and training and user and user.fcm_token:
        from app.logger import logger
        from app.services.firebase_service import FirebaseService
        
        try:
            # Определяем тип тренировки
            training_type_value = training.training_type if hasattr(training, 'training_type') else None
            
            if training_type_value == 'userFree':
                # Свободная тренировка
                training_type = "userFree"
                logger.info(f"📤 Отправляю уведомление о свободной тренировке для user_training {user_training_uuid}")
            elif training_type_value in ('system_training', 'user'):
                # Обычная тренировка
                training_type = "system_training"
                logger.info(f"📤 Отправляю уведомление об обычной тренировке для user_training {user_training_uuid}")
            else:
                # Если тип не определен, используем system_training по умолчанию
                training_type = "system_training"
                logger.info(f"📤 Отправляю уведомление о тренировке (тип не определен, используем system_training) для user_training {user_training_uuid}")
            
            # Инициализируем Firebase если не инициализирован
            FirebaseService.initialize()
            
            # Отправляем уведомление
            result = FirebaseService.send_workout_notification(
                fcm_token=user.fcm_token,
                user_training_uuid=str(user_training_uuid),
                training_uuid=str(training.uuid),
                training_type=training_type
            )
            
            if result == True:
                logger.info(f"✅ Уведомление о тренировке успешно отправлено для user_training {user_training_uuid}")
            elif result == "INVALID_TOKEN":
                logger.warning(f"⚠️ FCM токен невалиден для пользователя {user.uuid}")
            else:
                logger.error(f"❌ Не удалось отправить уведомление о тренировке для user_training {user_training_uuid}")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления о тренировке: {e}", exc_info=True)
            # Не прерываем выполнение, если уведомление не отправилось
    
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
        data['user_program'] = user_program.to_dict() if user_program else None
        data['program'] = program.to_dict() if program else None
        data['training'] = training.to_dict() if training else None
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
async def pass_user_training(
    user_training_uuid: UUID,
    background_tasks: BackgroundTasks,
    user_data = Depends(get_current_user_user)
) -> dict:
    """
    Отметить пользовательскую тренировку как выполненную (PASSED)
    """
    from app.logger import logger
    
    logger.info(f"Попытка завершить тренировку {user_training_uuid} для пользователя {user_data.id}")
    
    # Получаем user_training
    user_training = await UserTrainingDAO.find_full_data(user_training_uuid)
    if not user_training:
        logger.warning(f"Тренировка {user_training_uuid} не найдена")
        raise HTTPException(status_code=404, detail="Пользовательская тренировка не найдена")
    
    logger.info(f"Тренировка {user_training_uuid} найдена, текущий статус: {user_training.status}, тип статуса: {type(user_training.status)}")
    
    # Проверяем, что тренировка в активном статусе
    # Обрабатываем как Enum, так и строку
    current_status = user_training.status.value if hasattr(user_training.status, 'value') else str(user_training.status)
    if current_status != 'ACTIVE':
        logger.warning(f"Тренировка {user_training_uuid} уже имеет статус {current_status}, нельзя завершить")
        raise HTTPException(status_code=400, detail=f"Тренировка уже имеет статус {current_status}")
    
    # Обновляем статус на PASSED и заполняем completed_at
    # Используем UTC для совместимости с created_at (который тоже в UTC через datetime.utcnow)
    current_time = datetime.utcnow()
    
    # Сохраняем created_at для расчета длительности
    training_created_at = user_training.created_at
    
    # Рассчитываем длительность только для тренировок без program_id
    duration_minutes = None
    if user_training.program_id is None:
        # Оба времени должны быть naive datetime (без timezone) в UTC
        # created_at создается через datetime.utcnow() (naive UTC)
        # current_time тоже datetime.utcnow() (naive UTC)
        # Поэтому можно напрямую вычитать
        duration_seconds = (current_time - training_created_at).total_seconds()
        duration_minutes = max(1, int(duration_seconds / 60))  # Минимум 1 минута, округление вниз
        logger.info(f"Рассчитана длительность тренировки {user_training_uuid}: {duration_minutes} минут (program_id отсутствует, created_at: {training_created_at}, completed_at: {current_time}, разница: {duration_seconds} сек)")
    else:
        logger.info(f"Расчет длительности не требуется для тренировки {user_training_uuid} (program_id={user_training.program_id})")
    
    update_data = {
        'status': 'PASSED',
        'completed_at': current_time
    }
    
    # Добавляем duration в update_data, если он был рассчитан
    if duration_minutes is not None:
        update_data['duration'] = duration_minutes
    
    logger.info(f"Обновляю статус тренировки {user_training_uuid} на PASSED")
    check = await UserTrainingDAO.update(user_training_uuid, **update_data)
    if not check:
        logger.error(f"Ошибка при обновлении статуса тренировки {user_training_uuid}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса тренировки")
    
    logger.info(f"Статус тренировки {user_training_uuid} успешно обновлен на PASSED")
    
    # Обновляем статус всех связанных user_exercise на PASSED
    if user_training.training_id is not None:
        logger.info(f"Ищу связанные user_exercise с training_id={user_training.training_id} и status=ACTIVE")
        active_exercises = await UserExerciseDAO.find_all(
            training_id=user_training.training_id,
            status=ExerciseStatus.ACTIVE
        )
        
        if active_exercises:
            logger.info(f"Найдено {len(active_exercises)} активных подходов для обновления статуса")
            updated_count = 0
            for exercise in active_exercises:
                update_result = await UserExerciseDAO.update(exercise.uuid, status=ExerciseStatus.PASSED)
                if update_result:
                    updated_count += 1
                else:
                    logger.warning(f"Не удалось обновить статус user_exercise {exercise.uuid}")
            logger.info(f"Успешно обновлено {updated_count} из {len(active_exercises)} подходов на статус PASSED")
        else:
            logger.info(f"Не найдено активных подходов для training_id={user_training.training_id}")
    else:
        logger.info(f"У тренировки {user_training_uuid} отсутствует training_id, пропускаю обновление user_exercise")
    
    # Удаляем FCM уведомление о тренировке, если оно было отправлено (program_id отсутствует)
    if user_training.program_id is None:
        try:
            from app.services.firebase_service import FirebaseService
            
            # Получаем пользователя для FCM токена
            user = await UsersDAO.find_one_or_none(id=user_training.user_id)
            if user and user.fcm_token:
                # Инициализируем Firebase если не инициализирован
                FirebaseService.initialize()
                
                # Удаляем уведомление
                result = FirebaseService.cancel_workout_notification(
                    fcm_token=user.fcm_token,
                    user_training_uuid=str(user_training_uuid)
                )
                
                if result == True:
                    logger.info(f"✅ Уведомление о тренировке успешно удалено для user_training {user_training_uuid}")
                elif result == "INVALID_TOKEN":
                    logger.warning(f"⚠️ FCM токен невалиден при удалении уведомления для пользователя {user.uuid}")
                else:
                    logger.error(f"❌ Не удалось удалить уведомление о тренировке для user_training {user_training_uuid}")
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении уведомления о тренировке: {e}", exc_info=True)
            # Не прерываем выполнение, если уведомление не удалилось
    
    # Добавляем +1 к score пользователя
    logger.info(f"Обновляю score пользователя {user_training.user_id}")
    user = await UsersDAO.find_one_or_none_by_id(user_training.user_id)
    if user:
        current_score = user.score if user.score else 0
        new_score = current_score + 1
        logger.info(f"Текущий score: {current_score}, новый score: {new_score}")
        await UsersDAO.update(user.uuid, score=new_score)
        logger.info(f"Score пользователя {user.uuid} обновлен на {new_score}")
    else:
        logger.warning(f"Пользователь {user_training.user_id} не найден для обновления score")
    
    # Получаем user_training заново с новым статусом
    user_training = await UserTrainingDAO.find_full_data(user_training_uuid)
    
    # Запускаем фоновую задачу для проверки достижений (только если не день отдыха)
    logger.info(f"is_rest_day: {user_training.is_rest_day}")
    if not user_training.is_rest_day:
        logger.info(f"Запускаю фоновую задачу проверки достижений для тренировки {user_training_uuid}")
        
        async def check_achievements_task():
            from app.achievements.check_service import AchievementCheckService
            from app.database import async_session_maker
            from sqlalchemy import select
            from app.user_training.models import UserTraining
            
            logger.info(f"[Background] Создаю сессию для проверки достижений...")
            session = None
            try:
                async with async_session_maker() as session:
                    logger.info(f"[Background] Сессия создана, начинаю проверку достижений для тренировки {user_training_uuid}")
                    logger.info(f"[Background] Выполняю запрос для загрузки UserTraining...")
                    # Загружаем тренировку напрямую через сессию, чтобы она была привязана к той же сессии
                    result = await session.execute(
                        select(UserTraining).where(UserTraining.uuid == user_training_uuid)
                    )
                    logger.info(f"[Background] Запрос выполнен, получаю результат...")
                    updated_training = result.scalar_one_or_none()
                    logger.info(f"[Background] Тренировка {'найдена' if updated_training else 'не найдена'}")
                    
                    if updated_training:
                        logger.info(f"[Background] Создаю AchievementCheckService...")
                        check_service = AchievementCheckService(session)
                        logger.info(f"[Background] Вызываю check_achievements_for_training...")
                        achievements = None
                        try:
                            logger.info(f"[Background] ════════════════════════════════════════════════════")
                            logger.info(f"[Background] НАЧАЛО проверки достижений для тренировки {user_training_uuid}")
                            logger.info(f"[Background] ════════════════════════════════════════════════════")
                            achievements = await check_service.check_achievements_for_training(updated_training)
                            logger.info(f"[Background] ════════════════════════════════════════════════════")
                            logger.info(f"[Background] ЗАВЕРШЕНИЕ проверки достижений, функция вернула результат")
                            logger.info(f"[Background] ════════════════════════════════════════════════════")
                        except Exception as check_error:
                            logger.error(f"[Background] ❌ ИСКЛЮЧЕНИЕ в check_achievements_for_training: {type(check_error).__name__}: {check_error}", exc_info=True)
                            raise
                        finally:
                            # ВСЕГДА отключаем все объекты от сессии сразу после вызова функции
                            # Это предотвратит проблемы при закрытии сессии
                            logger.info(f"[Background] ════════════════════════════════════════════════════")
                            logger.info(f"[Background] БЛОК FINALLY: Начинаю отключение объектов от сессии")
                            logger.info(f"[Background] ════════════════════════════════════════════════════")
                            try:
                                logger.info(f"[Background] Вызываю session.expunge_all()...")
                                session.expunge_all()
                                logger.info(f"[Background] ✅ session.expunge_all() выполнен успешно")
                            except Exception as expunge_error:
                                error_type = type(expunge_error).__name__
                                error_msg = str(expunge_error)
                                logger.warning(f"[Background] ⚠️ Ошибка при expunge_all: {error_type}: {error_msg}")
                                logger.warning(f"[Background] Stack trace:", exc_info=True)
                        
                        # Логируем результат после expunge_all
                        logger.info(f"[Background] ════════════════════════════════════════════════════")
                        logger.info(f"[Background] РЕЗУЛЬТАТ проверки достижений:")
                        if achievements is not None:
                            logger.info(f"[Background]   - Получено достижений: {len(achievements)}")
                            logger.info(f"[Background]   - Список: {[a.name if hasattr(a, 'name') else str(a) for a in achievements]}")
                        else:
                            logger.info(f"[Background]   - achievements = None")
                        logger.info(f"[Background] ════════════════════════════════════════════════════")
                    else:
                        logger.warning(f"[Background] Тренировка {user_training_uuid} не найдена для проверки достижений")
                    
                    logger.info(f"[Background] Выход из async with...")
            except Exception as e:
                error_type = type(e).__name__
                # Игнорируем MissingGreenlet ошибки - они не критичны, достижения уже сохранены
                if "MissingGreenlet" in error_type or "greenlet_spawn" in str(e):
                    logger.warning(f"[Background] Игнорирую некритичную ошибку при закрытии сессии: {error_type}: {e}")
                else:
                    logger.error(f"[Background] Ошибка при проверке достижений для {user_training_uuid}: {error_type}: {e}", exc_info=True)
            finally:
                logger.info(f"[Background] Финальная очистка завершена")
        
        # Используем BackgroundTasks с async функцией
        # FastAPI правильно обрабатывает async функции в BackgroundTasks
        background_tasks.add_task(check_achievements_task)
    else:
        logger.info(f"Тренировка {user_training_uuid} - день отдыха, пропускаю проверку достижений")
    
    # Активируем следующую тренировку
    next_activated, next_training = await activate_next_training(user_training)
    
    # Проверяем, нужно ли завершить программу (если не осталось активных тренировок)
    program_finished = await finish_program_if_completed(user_training)
    
    response = {
        "message": f"Тренировка {user_training.training_date} выполнена",
        "status": "passed",
        "training_date": user_training.training_date.isoformat(),
        "completed_at": current_time.isoformat(),
        "next_training_activated": next_activated,
        "program_finished": program_finished
    }
    
    if next_activated and next_training:
        response["next_training_date"] = next_training.training_date.isoformat()
        response["next_training_uuid"] = str(next_training.uuid)
    
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
    if user_training.status.value != 'ACTIVE':
        raise HTTPException(status_code=400, detail=f"Тренировка уже имеет статус {user_training.status.value}")
    
    # Обновляем статус на SKIPPED и заполняем skipped_at
    current_time = datetime.now()
    update_data = {
        'status': 'SKIPPED',
        'skipped_at': current_time
    }
    
    check = await UserTrainingDAO.update(user_training_uuid, **update_data)
    if not check:
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса тренировки")
    
    # Получаем user_training заново с новым статусом
    user_training = await UserTrainingDAO.find_full_data(user_training_uuid)
    
    # Активируем следующую тренировку
    next_activated, next_training = await activate_next_training(user_training)
    
    # Проверяем, нужно ли завершить программу (если не осталось активных тренировок)
    program_finished = await finish_program_if_completed(user_training)
    
    response = {
        "message": f"Тренировка {user_training.training_date} пропущена",
        "status": "skipped",
        "training_date": user_training.training_date.isoformat(),
        "skipped_at": current_time.isoformat(),
        "next_training_activated": next_activated,
        "program_finished": program_finished
    }
    
    if next_activated and next_training:
        response["next_training_date"] = next_training.training_date.isoformat()
        response["next_training_uuid"] = str(next_training.uuid)
    
    return response


@router.get("/active/userFree/{user_uuid}", summary="Получить активные пользовательские бесплатные тренировки")
async def get_active_user_free_trainings(
    user_uuid: UUID,
    user_data = Depends(get_current_user_user)
) -> list[dict]:
    """
    Получить все активные пользовательские бесплатные тренировки для указанного пользователя.
    Ищет записи в trainings и user_trainings, где:
    - trainings.training_type = 'userFree'
    - trainings.user_id соответствует указанному пользователю
    - user_trainings.status = 'ACTIVE'
    """
    # Проверяем права доступа - пользователь может получить только свои тренировки
    if str(user_uuid) != str(user_data.uuid):
        raise HTTPException(status_code=403, detail="Вы можете получить тренировки только для своего профиля")
    
    # Получаем активные бесплатные тренировки
    user_trainings = await UserTrainingDAO.find_user_free_active_trainings(user_uuid)
    
    if not user_trainings:
        return []
    
    # Формируем ответ
    result = []
    for ut in user_trainings:
        try:
            # Получаем тренировку
            training_data = None
            if ut.training:
                training_data = {
                    "uuid": str(ut.training.uuid),
                    "training_type": ut.training.training_type,
                    "caption": ut.training.caption,
                    "description": ut.training.description,
                    "difficulty_level": ut.training.difficulty_level,
                    "duration": ut.training.duration,
                    "order": ut.training.order,
                    "muscle_group": ut.training.muscle_group,
                    "stage": ut.training.stage,
                    "image_uuid": str(ut.training.image.uuid) if hasattr(ut.training, 'image') and ut.training.image else None,
                    "actual": ut.training.actual
                }
            
            # Получаем пользователя
            user_info = None
            if ut.user:
                user_info = await ut.user.to_dict()
            
            # Формируем данные user_training
            data = {
                "uuid": str(ut.uuid),
                "training_date": ut.training_date.isoformat() if ut.training_date else None,
                "status": ut.status.value,
                "duration": ut.duration,
                "stage": ut.stage,
                "week": ut.week,
                "weekday": ut.weekday,
                "is_rest_day": ut.is_rest_day,
                "completed_at": ut.completed_at.isoformat() if ut.completed_at else None,
                "skipped_at": ut.skipped_at.isoformat() if ut.skipped_at else None,
                "training": training_data,
                "user": user_info
            }
            
            result.append(data)
        except Exception as ex:
            print(f"Ошибка при обработке user_training {ut.id}: {ex}")
            import traceback
            traceback.print_exc()
            continue
    
    return result