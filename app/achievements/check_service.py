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
        
        # Предзагружаем все необходимые атрибуты для всех achievement_types, чтобы избежать lazy loading после commit()
        # Это критично, так как после commit() объекты могут потерять связь с сессией
        logger.info(f"[DEBUG] Предзагружаю атрибуты для {len(achievement_types)} типов достижений...")
        achievement_types_data = []
        for at in achievement_types:
            try:
                # Загружаем все необходимые атрибуты напрямую, чтобы они были в памяти
                at_data = {
                    'obj': at,
                    'id': at.id,
                    'uuid': at.uuid,
                    'name': at.name,
                    'category': at.category,
                    'is_active': at.is_active,
                    'points': at.points,
                    'requirements': at.requirements,  # Предзагружаем requirements для методов проверки
                }
                achievement_types_data.append(at_data)
            except Exception as e:
                logger.error(f"[DEBUG] Ошибка при предзагрузке атрибутов для achievement_type: {e}", exc_info=True)
                # Пропускаем этот achievement_type, если не удалось загрузить атрибуты
                continue
        logger.info(f"[DEBUG] Предзагрузка завершена, готово {len(achievement_types_data)} типов достижений")
        
        # Получаем пользователя для проверки дня рождения
        user_result = await self.session.execute(
            select(User).where(User.id == user_training.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return []
        
        # Предзагружаем атрибуты user_training, чтобы избежать lazy loading после commit()
        user_training_user_id = user_training.user_id
        user_training_id = user_training.id
        user_training_completed_at = user_training.completed_at if hasattr(user_training, 'completed_at') else None
        user_id_preloaded = user.id
        user_fcm_token_preloaded = user.fcm_token if hasattr(user, 'fcm_token') else None
        user_birthday_preloaded = user.birthday if hasattr(user, 'birthday') else None
        user_score_preloaded = user.score or 0  # Предзагружаем текущий score
        
        # Проверяем каждое достижение
        logger.info(f"[DEBUG] Начинаю проверку {len(achievement_types_data)} типов достижений")
        for idx, at_data in enumerate(achievement_types_data, 1):
            try:
                # Используем предзагруженные данные
                achievement_type = at_data['obj']
                achievement_type_id = at_data['id']
                achievement_type_uuid_preloaded = at_data['uuid']
                achievement_type_name_preloaded = at_data['name']
                achievement_type_category_preloaded = at_data['category']
                achievement_type_is_active_preloaded = at_data['is_active']
                achievement_type_points_preloaded = at_data['points']
                achievement_type_requirements_preloaded = at_data['requirements']
                
                logger.info(f"[DEBUG] ═══ ИТЕРАЦИЯ {idx}/{len(achievement_types_data)}: '{achievement_type_name_preloaded}' (категория: {achievement_type_category_preloaded}) ═══")
                
                # Пропускаем неактивные достижения (используем предзагруженное значение)
                if not achievement_type_is_active_preloaded:
                    logger.debug(f"[DEBUG] Достижение '{achievement_type_name_preloaded}' неактивно, пропускаю")
                    continue
                
                # Пропускаем если уже есть достижение этого типа у пользователя (используем предзагруженный id)
                logger.debug(f"[DEBUG] Проверяю наличие достижения '{achievement_type_name_preloaded}' у пользователя {user_training_user_id}...")
                existing = await self.achievement_dao.find_by_user_and_type(
                    user_training_user_id,
                    achievement_type_id
                )
                if existing:
                    logger.debug(f"[DEBUG] Достижение '{achievement_type_name_preloaded}' уже есть у пользователя {user_training_user_id}, пропускаю")
                    continue
                logger.debug(f"[DEBUG] Достижение '{achievement_type_name_preloaded}' отсутствует у пользователя, продолжаю проверку")
                
                # Проверяем в зависимости от категории (используем предзагруженную категорию)
                should_create = False
                
                if achievement_type_category_preloaded == "special_day":
                    should_create = await self._check_special_day(
                        achievement_type_requirements_preloaded,
                        user_training_completed_at,
                        user_birthday_preloaded,
                        achievement_type_name_preloaded
                    )
                elif achievement_type_category_preloaded == "time_less_than":
                    should_create = await self._check_time_less_than(
                        achievement_type_requirements_preloaded,
                        user_training_completed_at,
                        achievement_type_name_preloaded
                    )
                elif achievement_type_category_preloaded == "time_more_than":
                    should_create = await self._check_time_more_than(
                        achievement_type_requirements_preloaded,
                        user_training_completed_at,
                        achievement_type_name_preloaded
                    )
                elif achievement_type_category_preloaded == "training_count":
                    should_create = await self._check_training_count(
                        achievement_type_requirements_preloaded,
                        user_training_user_id,
                        achievement_type_name_preloaded
                    )
                elif achievement_type_category_preloaded == "training_count_in_week":
                    should_create = await self._check_training_count_in_week(
                        achievement_type_requirements_preloaded,
                        user_training_user_id,
                        user_training_completed_at,
                        achievement_type_name_preloaded
                    )
                
                if should_create:
                    # Используем предзагруженные значения, чтобы избежать lazy loading после commit()
                    achievement_type_name = achievement_type_name_preloaded
                    achievement_type_uuid = achievement_type_uuid_preloaded
                    achievement_type_category = achievement_type_category_preloaded
                    achievement_type_points = achievement_type_points_preloaded
                    user_id = user_id_preloaded
                    fcm_token = user_fcm_token_preloaded
                    
                    logger.info(f"🎉 Создаю достижение '{achievement_type_name}' (категория: {achievement_type_category}) для пользователя {user_id}")
                    
                    try:
                        # Создаем достижение (без коммита пока)
                        from app.achievements.models import Achievement
                        import uuid
                        from datetime import datetime
                        
                        logger.info(f"[DEBUG] Создаю объект Achievement...")
                        achievement = Achievement(
                            uuid=str(uuid.uuid4()),
                            name=achievement_type_name,
                            achievement_type_id=achievement_type_id,  # Используем предзагруженный id
                            user_id=user_training_user_id,  # Используем предзагруженное значение
                            status="active",
                            user_training_id=user_training_id,  # Используем предзагруженное значение
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        logger.info(f"[DEBUG] Объект Achievement создан: {achievement.uuid}")
                        
                        # Добавляем очки к рейтингу пользователя (используем предзагруженное значение и обновляем через SQL)
                        achievement_points = achievement_type_points
                        if achievement_points:
                            old_score = user_score_preloaded
                            new_score = old_score + achievement_points
                            # Обновляем user.score через SQL запрос, чтобы избежать lazy loading после commit()
                            from sqlalchemy import update as sql_update
                            update_query = sql_update(User).where(User.id == user_id).values(score=new_score)
                            await self.session.execute(update_query)
                            logger.info(f"📊 Добавлено {achievement_points} очков к рейтингу пользователя {user_id} (было: {old_score}, стало: {new_score})")
                            # Обновляем предзагруженное значение для следующих итераций
                            user_score_preloaded = new_score
                        
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
                        
                        # Отключаем achievement от сессии, чтобы избежать проблем с lazy loading в BackgroundTasks
                        # НЕ отключаем user, так как он может понадобиться в следующих итерациях цикла
                        logger.info(f"[DEBUG] Отключаю achievement от сессии...")
                        self.session.expunge(achievement)
                        logger.info(f"[DEBUG] Achievement отключен от сессии")
                        
                        logger.info(f"[DEBUG] Добавляю achievement в список created_achievements...")
                        created_achievements.append(achievement)
                        logger.info(f"[DEBUG] Achievement добавлен в список")
                        
                        logger.info(f"✅ Достижение '{achievement_type_name}' создано (UUID: {achievement_uuid})")
                    except Exception as e:
                        logger.error(f"[DEBUG] Ошибка при создании достижения '{achievement_type_name}': {type(e).__name__}: {e}", exc_info=True)
                        # Откатываем изменения для этого достижения, но продолжаем проверку остальных
                        try:
                            await self.session.rollback()
                            logger.warning(f"⚠️ Откатил транзакцию после ошибки создания достижения '{achievement_type_name}', продолжаю проверку остальных достижений")
                        except Exception as rollback_error:
                            logger.error(f"❌ Ошибка при откате транзакции: {rollback_error}")
                        # Продолжаем цикл для проверки остальных достижений
                        continue
                    
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
                            logger.error(f"❌ Ошибка отправки push-уведомления о достижении '{achievement_type_name}': {type(e).__name__}: {e}", exc_info=True)
                            # Продолжаем проверку остальных достижений даже при ошибке отправки уведомления
                            logger.info(f"[DEBUG] Продолжаю проверку остальных достижений после ошибки отправки уведомления")
                    else:
                        logger.debug(f"[DEBUG] FCM токен отсутствует для пользователя {user_id}, пропускаю отправку уведомления для достижения '{achievement_type_name}'")
                    
                    logger.info(f"[DEBUG] ✅ Завершил обработку достижения '{achievement_type_name}', продолжаю цикл...")
                
                # Логируем завершение проверки текущего достижения (используем предзагруженное имя)
                logger.debug(f"[DEBUG] ═══ ЗАВЕРШЕНИЕ ИТЕРАЦИИ {idx}/{len(achievement_types_data)}: '{achievement_type_name_preloaded}' (should_create={should_create}) ═══")
            except Exception as iteration_error:
                error_type = type(iteration_error).__name__
                error_msg = str(iteration_error)
                # Используем предзагруженное имя, чтобы избежать lazy loading
                try:
                    achievement_type_name_for_log = achievement_type_name_preloaded if 'achievement_type_name_preloaded' in locals() else f"достижение {idx}"
                except Exception:
                    achievement_type_name_for_log = f"достижение {idx}"
                logger.error(f"[DEBUG] ❌ ОШИБКА в итерации {idx}/{len(achievement_types_data)} для достижения '{achievement_type_name_for_log}': {error_type}: {error_msg}", exc_info=True)
                # Продолжаем цикл для проверки остальных достижений
                logger.warning(f"[DEBUG] ⚠️ Продолжаю проверку остальных достижений после ошибки в итерации {idx}")
                continue
        
        logger.info(f"[DEBUG] Завершаю check_achievements_for_training, создано {len(created_achievements)} достижений")
        # Безопасное получение имен достижений, так как они могут быть expunged
        try:
            achievement_names = [getattr(a, 'name', str(a.uuid) if hasattr(a, 'uuid') else 'unknown') for a in created_achievements]
            logger.info(f"[DEBUG] Список созданных достижений: {achievement_names}")
        except Exception as e:
            logger.warning(f"[DEBUG] Не удалось получить список имен достижений: {e}")
            logger.info(f"[DEBUG] Создано {len(created_achievements)} достижений")
        
        # Возвращаем список созданных достижений
        logger.info(f"[DEBUG] Возвращаю список из {len(created_achievements)} достижений")
        # НЕ вызываем expunge_all здесь - это будет сделано в роутере перед закрытием сессии
        return created_achievements
    
    async def _check_special_day(
        self,
        requirements: str,
        completed_at,
        user_birthday,
        achievement_type_name: str
    ) -> bool:
        """
        Проверяет достижения категории special_day
        Для requirements="user_birthday" проверяет день рождения пользователя
        Для других значений проверяет совпадение месяца и дня (формат: MM-DD), игнорируя год
        """
        if not requirements or not completed_at:
            return False
        
        completed_date = completed_at.date()
        requirements_clean = requirements.strip() if requirements else None
        
        # Специальный случай: день рождения пользователя
        if requirements_clean == "user_birthday":
            # Проверяем день рождения из user (предзагруженное значение)
            if user_birthday:
                # Сравниваем только месяц и день, игнорируя год
                return (completed_date.month == user_birthday.month and 
                       completed_date.day == user_birthday.day)
            return False
        
        # Проверяем совпадение месяца и дня (формат: MM-DD, например "12-01" для 1 декабря)
        try:
            target_month, target_day = map(int, requirements_clean.split("-"))
            # Сравниваем только месяц и день, игнорируя год
            return (completed_date.month == target_month and 
                   completed_date.day == target_day)
        except (ValueError, AttributeError):
            return False
    
    async def _check_time_less_than(
        self,
        requirements: str,
        completed_at,
        achievement_type_name: str
    ) -> bool:
        """Проверяет достижения категории time_less_than"""
        if not requirements or not completed_at:
            return False
        
        try:
            # Парсим время требования (например, "06:00")
            req_hour, req_minute = map(int, requirements.split(":"))
            # Получаем только время из completed_at
            completed_time = completed_at.time()
            requirement_time_obj = dt_time(hour=req_hour, minute=req_minute, second=0, microsecond=0)
            
            # Проверяем, что время завершения меньше требуемого
            return completed_time < requirement_time_obj
        except (ValueError, AttributeError, TypeError):
            return False
    
    async def _check_time_more_than(
        self,
        requirements: str,
        completed_at,
        achievement_type_name: str
    ) -> bool:
        """Проверяет достижения категории time_more_than"""
        if not requirements or not completed_at:
            return False
        
        try:
            # Парсим время требования (например, "22:00")
            req_hour, req_minute = map(int, requirements.split(":"))
            # Получаем только время из completed_at
            from datetime import time as dt_time
            completed_time = completed_at.time()
            requirement_time_obj = dt_time(hour=req_hour, minute=req_minute, second=0, microsecond=0)
            
            # Проверяем, что время завершения больше требуемого
            return completed_time > requirement_time_obj
        except (ValueError, AttributeError, TypeError):
            return False
    
    async def _check_training_count(
        self,
        requirements: str,
        user_id: int,
        achievement_type_name: str
    ) -> bool:
        """Проверяет достижения категории training_count"""
        if not requirements:
            return False
        
        try:
            required_count = int(requirements)
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
            logger.info(f"✅ Достижение '{achievement_type_name}': у пользователя {user_id} {actual_count} тренировок, требуется {required_count}")
        else:
            logger.debug(f"❌ Достижение '{achievement_type_name}': у пользователя {user_id} {actual_count} тренировок, требуется {required_count}")
        
        return is_achieved
    
    async def _check_training_count_in_week(
        self,
        requirements: str,
        user_id: int,
        completed_at,
        achievement_type_name: str
    ) -> bool:
        """Проверяет достижения категории training_count_in_week"""
        if not requirements or not completed_at:
            return False
        
        try:
            required_count = int(requirements)
        except ValueError:
            return False
        
        # Определяем начало и конец недели (понедельник - воскресенье)
        completed_date = completed_at.date()
        # Находим понедельник текущей недели
        days_since_monday = completed_date.weekday()
        week_start = completed_date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        # Считаем тренировки в текущей неделе
        result = await self.session.execute(
            select(func.count(UserTraining.id))
            .where(
                and_(
                    UserTraining.user_id == user_id,
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
            logger.info(f"✅ Достижение '{achievement_type_name}' (неделя {week_start} - {week_end}): у пользователя {user_id} {actual_count} тренировок, требуется {required_count}")
        else:
            logger.debug(f"❌ Достижение '{achievement_type_name}' (неделя {week_start} - {week_end}): у пользователя {user_id} {actual_count} тренировок, требуется {required_count}")
        
        return is_achieved

