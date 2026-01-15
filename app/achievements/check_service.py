"""
Сервис для автоматической проверки достижений после завершения тренировки
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, case
from datetime import datetime, date, timedelta, time as dt_time
from app.achievements.dao import AchievementTypeDAO, AchievementDAO
from app.achievements.models import AchievementType, Achievement
from app.user_training.models import UserTraining, TrainingStatus
from app.users.models import User
from app.logger import logger
from app.logger import logger


class AchievementCheckService:
    """Сервис для проверки достижений"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.achievement_type_dao = AchievementTypeDAO(session)
        self.achievement_dao = AchievementDAO(session)
    
    async def check_achievements_for_training(
        self,
        user_training: UserTraining
    ) -> list[Achievement]:
        """
        Проверяет все возможные достижения для завершенной тренировки
        Возвращает список созданных достижений
        """
        if user_training.is_rest_day:
            return []
        
        if user_training.status != TrainingStatus.PASSED:
            return []
        
        if not user_training.completed_at:
            return []
        
        created_achievements = []
        
        # Получаем все типы достижений
        achievement_types = await self.achievement_type_dao.find_all()
        
        # Получаем пользователя для проверки дня рождения
        user_result = await self.session.execute(
            select(User).where(User.id == user_training.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return []
        
        # Проверяем каждое достижение
        for achievement_type in achievement_types:
            # Пропускаем неактивные достижения
            if not achievement_type.is_active:
                continue
            
            # Пропускаем если уже есть достижение этого типа у пользователя
            existing = await self.achievement_dao.find_by_user_and_type(
                user_training.user_id,
                achievement_type.id
            )
            if existing:
                logger.debug(f"Достижение '{achievement_type.name}' уже есть у пользователя {user_training.user_id}, пропускаю")
                continue
            
            # Проверяем в зависимости от категории
            should_create = False
            
            if achievement_type.category == "special_day":
                should_create = await self._check_special_day(
                    achievement_type,
                    user_training,
                    user
                )
            elif achievement_type.category == "time_less_than":
                should_create = await self._check_time_less_than(
                    achievement_type,
                    user_training
                )
            elif achievement_type.category == "time_more_than":
                should_create = await self._check_time_more_than(
                    achievement_type,
                    user_training
                )
            elif achievement_type.category == "training_count":
                should_create = await self._check_training_count(
                    achievement_type,
                    user_training.user_id
                )
            elif achievement_type.category == "training_count_in_week":
                should_create = await self._check_training_count_in_week(
                    achievement_type,
                    user_training
                )
            
            if should_create:
                # Сохраняем все нужные значения заранее, чтобы избежать lazy loading после отключения от сессии
                achievement_type_name = achievement_type.name
                achievement_type_uuid = achievement_type.uuid
                user_id = user.id
                fcm_token = user.fcm_token
                
                logger.info(f"🎉 Создаю достижение '{achievement_type_name}' (категория: {achievement_type.category}) для пользователя {user_training.user_id}")
                
                try:
                    # Создаем достижение (без коммита пока)
                    from app.achievements.models import Achievement
                    import uuid
                    from datetime import datetime
                    
                    logger.info(f"[DEBUG] Создаю объект Achievement...")
                    achievement = Achievement(
                        uuid=str(uuid.uuid4()),
                        name=achievement_type_name,
                        achievement_type_id=achievement_type.id,
                        user_id=user_training.user_id,
                        status="active",
                        user_training_id=user_training.id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    logger.info(f"[DEBUG] Объект Achievement создан: {achievement.uuid}")
                    
                    # Добавляем очки к рейтингу пользователя
                    achievement_points = achievement_type.points
                    if achievement_points:
                        old_score = user.score or 0
                        user.score = old_score + achievement_points
                        logger.info(f"📊 Добавлено {achievement_points} очков к рейтингу пользователя {user_id} (было: {old_score}, стало: {user.score})")
                    
                    logger.info(f"[DEBUG] Добавляю achievement в session...")
                    # Сохраняем достижение и обновление score одним коммитом
                    self.session.add(achievement)
                    logger.info(f"[DEBUG] Achievement добавлен в session, начинаю commit...")
                    await self.session.commit()
                    logger.info(f"[DEBUG] Commit выполнен успешно, начинаю refresh...")
                    await self.session.refresh(achievement)
                    logger.info(f"[DEBUG] Refresh выполнен успешно")
                    
                    # Сохраняем UUID до отключения от сессии, чтобы избежать проблем с lazy loading
                    logger.info(f"[DEBUG] Получаю UUID достижения...")
                    achievement_uuid = achievement.uuid
                    logger.info(f"[DEBUG] UUID получен: {achievement_uuid}")
                    
                    # Отключаем все объекты от сессии, чтобы избежать проблем с lazy loading в BackgroundTasks
                    logger.info(f"[DEBUG] Отключаю achievement и user от сессии...")
                    self.session.expunge(achievement)
                    self.session.expunge(user)
                    logger.info(f"[DEBUG] Achievement и user отключены от сессии")
                    
                    logger.info(f"[DEBUG] Добавляю achievement в список created_achievements...")
                    created_achievements.append(achievement)
                    logger.info(f"[DEBUG] Achievement добавлен в список")
                    
                    logger.info(f"✅ Достижение '{achievement_type_name}' создано (UUID: {achievement_uuid})")
                except Exception as e:
                    logger.error(f"[DEBUG] Ошибка при создании достижения '{achievement_type_name}': {type(e).__name__}: {e}", exc_info=True)
                    raise
                
                logger.info(f"[DEBUG] Проверяю наличие FCM токена...")
                # Отправляем push-уведомление пользователю
                if fcm_token:
                    logger.info(f"📤 Отправляю push-уведомление о достижении '{achievement_type_name}' пользователю {user_id}")
                    try:
                        from app.services.firebase_service import FirebaseService
                        FirebaseService.initialize()
                        
                        title = "Поздравляем!"
                        body = f"Вы получили достижение: {achievement_type_name}"
                        
                        data = {
                            'achievement_uuid': str(achievement_type_uuid)
                        }
                        
                        logger.info(f"📝 Формирую push-уведомление: title='{title}', body='{body}', channel='achievements_channel', data={data}")
                        
                        result = FirebaseService.send_notification(
                            fcm_token=fcm_token,
                            title=title,
                            body=body,
                            data=data,
                            channel_id='achievements_channel'  # Отдельный канал для достижений
                        )
                        
                        # Обрабатываем результат отправки
                        if result == "INVALID_TOKEN":
                            # Не очищаем токен автоматически - может быть временная проблема
                            # Просто логируем и продолжаем попытки отправки для остальных достижений
                            logger.warning(f"⚠️ FCM токен невалиден для пользователя {user_id}, но продолжаю попытки отправки для остальных достижений. Токен НЕ очищен автоматически.")
                        elif result == True:
                            logger.info(f"✅ Отправлено push-уведомление о достижении {achievement_type_name} пользователю {user_id}")
                        else:
                            logger.warning(f"⚠️ Не удалось отправить push-уведомление о достижении {achievement_type_name} пользователю {user_id} (результат: {result})")
                    except Exception as e:
                        logger.error(f"❌ Ошибка отправки push-уведомления о достижении: {e}")
        
        logger.info(f"[DEBUG] Завершаю check_achievements_for_training, создано {len(created_achievements)} достижений")
        
        # Возвращаем пустой список, так как достижения уже сохранены в БД
        logger.info(f"[DEBUG] Возвращаю пустой список (достижения уже сохранены)")
        # НЕ вызываем expunge_all здесь - это будет сделано в роутере перед закрытием сессии
        return []
    
    async def _check_special_day(
        self,
        achievement_type: AchievementType,
        user_training: UserTraining,
        user: User
    ) -> bool:
        """
        Проверяет достижения категории special_day
        Для requirements="user_birthday" проверяет день рождения пользователя
        Для других значений проверяет совпадение месяца и дня (формат: MM-DD), игнорируя год
        """
        if not achievement_type.requirements or not user_training.completed_at:
            return False
        
        completed_date = user_training.completed_at.date()
        requirements = achievement_type.requirements.strip()
        
        # Специальный случай: день рождения пользователя
        if requirements == "user_birthday":
            # Проверяем день рождения из user (если есть поле birthday)
            if hasattr(user, 'birthday') and user.birthday:
                user_birthday = user.birthday
                # Сравниваем только месяц и день, игнорируя год
                return (completed_date.month == user_birthday.month and 
                       completed_date.day == user_birthday.day)
            return False
        
        # Проверяем совпадение месяца и дня (формат: MM-DD, например "12-01" для 1 декабря)
        try:
            target_month, target_day = map(int, requirements.split("-"))
            # Сравниваем только месяц и день, игнорируя год
            return (completed_date.month == target_month and 
                   completed_date.day == target_day)
        except (ValueError, AttributeError):
            return False
    
    async def _check_time_less_than(
        self,
        achievement_type: AchievementType,
        user_training: UserTraining
    ) -> bool:
        """Проверяет достижения категории time_less_than"""
        if not achievement_type.requirements or not user_training.completed_at:
            return False
        
        try:
            # Парсим время требования (например, "06:00")
            req_hour, req_minute = map(int, achievement_type.requirements.split(":"))
            # Получаем только время из completed_at
            completed_time = user_training.completed_at.time()
            requirement_time_obj = dt_time(hour=req_hour, minute=req_minute, second=0, microsecond=0)
            
            # Проверяем, что время завершения меньше требуемого
            return completed_time < requirement_time_obj
        except (ValueError, AttributeError, TypeError):
            return False
    
    async def _check_time_more_than(
        self,
        achievement_type: AchievementType,
        user_training: UserTraining
    ) -> bool:
        """Проверяет достижения категории time_more_than"""
        if not achievement_type.requirements or not user_training.completed_at:
            return False
        
        try:
            # Парсим время требования (например, "22:00")
            req_hour, req_minute = map(int, achievement_type.requirements.split(":"))
            # Получаем только время из completed_at
            from datetime import time as dt_time
            completed_time = user_training.completed_at.time()
            requirement_time_obj = dt_time(hour=req_hour, minute=req_minute, second=0, microsecond=0)
            
            # Проверяем, что время завершения больше требуемого
            return completed_time > requirement_time_obj
        except (ValueError, AttributeError, TypeError):
            return False
    
    async def _check_training_count(
        self,
        achievement_type: AchievementType,
        user_id: int
    ) -> bool:
        """Проверяет достижения категории training_count"""
        if not achievement_type.requirements:
            return False
        
        try:
            required_count = int(achievement_type.requirements)
        except ValueError:
            return False
        
        # Считаем все завершенные тренировки пользователя (is_rest_day = false)
        result = await self.session.execute(
            select(func.count(UserTraining.id))
            .where(
                and_(
                    UserTraining.user_id == user_id,
                    UserTraining.status == TrainingStatus.PASSED,
                    UserTraining.is_rest_day.is_(False)
                )
            )
        )
        actual_count = result.scalar() or 0
        
        # Проверяем, что достигнут требуемый порог (>=, а не ==)
        # Это позволяет получить достижение даже если у пользователя уже больше тренировок
        is_achieved = actual_count >= required_count
        
        if is_achieved:
            logger.info(f"✅ Достижение '{achievement_type.name}': у пользователя {user_id} {actual_count} тренировок, требуется {required_count}")
        else:
            logger.debug(f"❌ Достижение '{achievement_type.name}': у пользователя {user_id} {actual_count} тренировок, требуется {required_count}")
        
        return is_achieved
    
    async def _check_training_count_in_week(
        self,
        achievement_type: AchievementType,
        user_training: UserTraining
    ) -> bool:
        """Проверяет достижения категории training_count_in_week"""
        if not achievement_type.requirements or not user_training.completed_at:
            return False
        
        try:
            required_count = int(achievement_type.requirements)
        except ValueError:
            return False
        
        # Определяем начало и конец недели (понедельник - воскресенье)
        completed_date = user_training.completed_at.date()
        # Находим понедельник текущей недели
        days_since_monday = completed_date.weekday()
        week_start = completed_date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        # Считаем тренировки в текущей неделе
        result = await self.session.execute(
            select(func.count(UserTraining.id))
            .where(
                and_(
                    UserTraining.user_id == user_training.user_id,
                    UserTraining.status == TrainingStatus.PASSED,
                    UserTraining.is_rest_day.is_(False),
                    UserTraining.completed_at >= datetime.combine(week_start, datetime.min.time()),
                    UserTraining.completed_at <= datetime.combine(week_end, datetime.max.time())
                )
            )
        )
        actual_count = result.scalar() or 0
        
        # Проверяем, что достигнут требуемый порог (>=, а не ==)
        # Это позволяет получить достижение даже если у пользователя уже больше тренировок
        is_achieved = actual_count >= required_count
        
        if is_achieved:
            logger.info(f"✅ Достижение '{achievement_type.name}' (неделя {week_start} - {week_end}): у пользователя {user_training.user_id} {actual_count} тренировок, требуется {required_count}")
        else:
            logger.debug(f"❌ Достижение '{achievement_type.name}' (неделя {week_start} - {week_end}): у пользователя {user_training.user_id} {actual_count} тренировок, требуется {required_count}")
        
        return is_achieved

