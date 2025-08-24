from app.dao.base import BaseDAO
from app.user_training.models import UserTraining
from app.user_program.dao import UserProgramDAO
from app.user_program.models import UserProgram
from app.programs.dao import ProgramDAO
from app.trainings.dao import TrainingDAO
from app.users.dao import UsersDAO
from app.database import async_session_maker
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from functools import lru_cache
import hashlib
import json
from uuid import UUID
import sqlalchemy as sa
import asyncio
from datetime import date, time, timedelta


class UserTrainingDAO(BaseDAO):
    model = UserTraining
    uuid_fk_map = {
        'user_program_id': (UserProgramDAO, 'user_program_uuid'),
        'program_id': (ProgramDAO, 'program_uuid'),
        'training_id': (TrainingDAO, 'training_uuid'),
        'user_id': (UsersDAO, 'user_uuid')
    }
    
    # Простой кэш для результатов запросов
    _cache = {}
    _cache_ttl = 300  # 5 минут
    
    @classmethod
    async def find_active_trainings(cls, user_program_id: int | None):
        """Получить активные тренировки для программы пользователя без исключения"""
        async with async_session_maker() as session:
            query = select(cls.model)
            if user_program_id is not None:
                query = query.filter_by(user_program_id=user_program_id, status='active')
            else:
                query = query.filter_by(status='active')
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    def _get_cache_key(cls, **filter_by):
        """Генерирует ключ кэша на основе параметров фильтрации"""
        # Сортируем параметры для стабильного ключа
        sorted_params = sorted(filter_by.items())
        params_str = json.dumps(sorted_params, sort_keys=True)
        return hashlib.md5(params_str.encode()).hexdigest()

    @classmethod
    async def find_all_with_relations(cls, **filter_by):
        """Оптимизированный метод для загрузки user_trainings без задержки"""
        filters = filter_by.copy()
        for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                if related_obj:
                    filters[fk_field] = related_obj.id
                else:
                    return []
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filters)
            query = query.order_by(cls.model.training_date.asc())
            result = await session.execute(query)
            objects = result.scalars().all()
            return objects

    @classmethod
    async def find_all_with_relations_paginated(cls, page: int = 1, page_size: int = 50, **filter_by):
        """Оптимизированный метод с пагинацией на уровне БД без задержки"""
        filters = filter_by.copy()
        for fk_field, (related_dao, uuid_field) in getattr(cls, 'uuid_fk_map', {}).items():
            if uuid_field in filters:
                uuid_value = filters.pop(uuid_field)
                related_obj = await related_dao.find_one_or_none(uuid=uuid_value)
                if related_obj:
                    filters[fk_field] = related_obj.id
                else:
                    return [], 0
        async with async_session_maker() as session:
            count_query = select(sa.func.count(cls.model.id)).filter_by(**filters)
            total_count = await session.scalar(count_query)
            query = select(cls.model).filter_by(**filters)
            query = query.order_by(cls.model.training_date.asc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            objects = result.scalars().all()
            return objects, total_count

    @classmethod
    def clear_cache(cls):
        """Очищает кэш"""
        pass  # Кэш больше не используется

    @classmethod
    async def update(cls, object_uuid: UUID, **values):
        """Переопределяем метод update для очистки кэша при обновлении"""
        # Кэш больше не используется
    
    @classmethod
    async def find_early_morning_completed_trainings(cls, user_id: int, min_count: int = 5):
        """
        Находит завершенные тренировки пользователя с 5 до 8 утра
        Возвращает тренировки, отсортированные по времени завершения
        """
        from datetime import time
        
        async with async_session_maker() as session:
            query = select(cls.model).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED',
                cls.model.completed_at.isnot(None),
                sa.func.extract('hour', cls.model.completed_at) >= 5,
                sa.func.extract('hour', cls.model.completed_at) < 8
            ).order_by(cls.model.completed_at.asc())
            
            result = await session.execute(query)
            trainings = result.scalars().all()
            
            # Возвращаем только если достигнуто минимальное количество
            if len(trainings) >= min_count:
                return trainings[:min_count]  # Возвращаем первые min_count тренировок
            
            return []
    
    @classmethod
    async def find_late_night_completed_trainings(cls, user_id: int, min_count: int = 5):
        """
        Находит завершенные тренировки пользователя с 21 до 00 (полночь)
        Возвращает тренировки, отсортированные по времени завершения
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED',
                cls.model.completed_at.isnot(None),
                sa.func.extract('hour', cls.model.completed_at) >= 21
            ).order_by(cls.model.completed_at.asc())
            
            result = await session.execute(query)
            trainings = result.scalars().all()
            
            # Возвращаем только если достигнуто минимальное количество
            if len(trainings) >= min_count:
                return trainings[:min_count]  # Возвращаем первые min_count тренировок
            
            return []
    
    @classmethod
    async def find_new_year_trainings(cls, user_id: int, year: int = None):
        """
        Находит тренировки пользователя в первый день нового года (1 января)
        Возвращает тренировки, отсортированные по времени завершения
        """
        async with async_session_maker() as session:
            if year is None:
                # Если год не указан, берем текущий
                from datetime import datetime
                year = datetime.now().year
            
            query = select(cls.model).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED',
                cls.model.completed_at.isnot(None),
                sa.func.extract('year', cls.model.completed_at) == year,
                sa.func.extract('month', cls.model.completed_at) == 1,
                sa.func.extract('day', cls.model.completed_at) == 1
            ).order_by(cls.model.completed_at.asc())
            
            result = await session.execute(query)
            return result.scalars().all()
    
    @classmethod
    async def find_womens_day_trainings(cls, user_id: int, year: int = None):
        """
        Находит тренировки пользователя в Международный женский день (8 марта)
        Возвращает тренировки, отсортированные по времени завершения
        """
        async with async_session_maker() as session:
            if year is None:
                # Если год не указан, берем текущий
                from datetime import datetime
                year = datetime.now().year
            
            query = select(cls.model).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED',
                cls.model.completed_at.isnot(None),
                sa.func.extract('year', cls.model.completed_at) == year,
                sa.func.extract('month', cls.model.completed_at) == 3,
                sa.func.extract('day', cls.model.completed_at) == 8
            ).order_by(cls.model.completed_at.asc())
            
            result = await session.execute(query)
            return result.scalars().all()
    
    @classmethod
    async def find_mens_day_trainings(cls, user_id: int, year: int = None):
        """
        Находит тренировки пользователя в День защитника Отечества (23 февраля)
        Возвращает тренировки, отсортированные по времени завершения
        """
        async with async_session_maker() as session:
            if year is None:
                # Если год не указан, берем текущий
                from datetime import datetime
                year = datetime.now().year
            
            query = select(cls.model).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED',
                cls.model.completed_at.isnot(None),
                sa.func.extract('year', cls.model.completed_at) == year,
                sa.func.extract('month', cls.model.completed_at) == 2,
                sa.func.extract('day', cls.model.completed_at) == 23
            ).order_by(cls.model.completed_at.asc())
            
            result = await session.execute(query)
            return result.scalars().all()
    
    @classmethod
    async def find_completed_program_trainings(cls, user_id: int, user_program_id: int):
        """
        Находит все завершенные тренировки пользователя для конкретной программы
        Возвращает тренировки, отсортированные по дате
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter(
                cls.model.user_id == user_id,
                cls.model.user_program_id == user_program_id,
                cls.model.status == 'PASSED'
            ).order_by(cls.model.training_date.asc())
            
            result = await session.execute(query)
            return result.scalars().all()
    
    @classmethod
    async def count_completed_trainings(cls, user_id: int):
        """
        Подсчитывает общее количество завершенных тренировок пользователя
        Возвращает количество тренировок
        """
        async with async_session_maker() as session:
            query = select(sa.func.count(cls.model.id)).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED'
            )
            
            result = await session.scalar(query)
            return result or 0
    
    @classmethod
    async def find_last_completed_training(cls, user_id: int):
        """
        Находит последнюю завершенную тренировку пользователя
        Возвращает тренировку или None
        """
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.user_program).joinedload(UserProgram.program)
            ).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED'
            ).order_by(cls.model.completed_at.desc()).limit(1)
            
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @classmethod
    async def count_completed_trainings_in_week(cls, user_id: int, week_start_date: date):
        """
        Подсчитывает количество завершенных тренировок пользователя за конкретную неделю
        Возвращает количество тренировок
        """
        async with async_session_maker() as session:
            # Вычисляем конец недели (7 дней от начала)
            from datetime import timedelta
            week_end_date = week_start_date + timedelta(days=6)
            
            query = select(sa.func.count(cls.model.id)).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED',
                cls.model.completed_at.isnot(None),
                cls.model.completed_at >= week_start_date,
                cls.model.completed_at < week_end_date + timedelta(days=1)  # +1 день для включения конца недели
            )
            
            result = await session.scalar(query)
            return result or 0
    
    @classmethod
    async def find_weekly_training_achievements(cls, user_id: int, min_count: int = 3):
        """
        Находит недели, когда пользователь выполнил минимум указанное количество тренировок
        Возвращает список дат начала недель
        """
        async with async_session_maker() as session:
            # Получаем все завершенные тренировки пользователя
            query = select(cls.model.completed_at).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED',
                cls.model.completed_at.isnot(None)
            ).order_by(cls.model.completed_at.desc())
            
            result = await session.execute(query)
            completed_dates = result.scalars().all()
            
            if not completed_dates:
                return []
            
            # Группируем тренировки по неделям
            from datetime import timedelta
            weekly_counts = {}
            
            for completed_date in completed_dates:
                # Находим начало недели (понедельник)
                days_since_monday = completed_date.weekday()
                week_start = completed_date.date() - timedelta(days=days_since_monday)
                
                if week_start not in weekly_counts:
                    weekly_counts[week_start] = 0
                weekly_counts[week_start] += 1
            
            # Фильтруем недели с достаточным количеством тренировок
            qualifying_weeks = [
                week_start for week_start, count in weekly_counts.items()
                if count >= min_count
            ]
            
            return sorted(qualifying_weeks, reverse=True)  # Сортируем по убыванию (новые недели первыми)
    
    @classmethod
    async def find_consecutive_weeks_with_min_trainings(cls, user_id: int, min_trainings_per_week: int = 1, min_consecutive_weeks: int = 2):
        """
        Находит максимальное количество недель подряд, когда пользователь выполнил минимум указанное количество тренировок
        Возвращает количество недель подряд
        """
        async with async_session_maker() as session:
            # Получаем все завершенные тренировки пользователя
            query = select(cls.model.completed_at).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED',
                cls.model.completed_at.isnot(None)
            ).order_by(cls.model.completed_at.asc())
            
            result = await session.execute(query)
            completed_dates = result.scalars().all()
            
            if not completed_dates:
                return 0
            
            # Группируем тренировки по неделям
            from datetime import timedelta
            weekly_counts = {}
            
            for completed_date in completed_dates:
                # Находим начало недели (понедельник)
                days_since_monday = completed_date.weekday()
                week_start = completed_date.date() - timedelta(days=days_since_monday)
                
                if week_start not in weekly_counts:
                    weekly_counts[week_start] = 0
                weekly_counts[week_start] += 1
            
            # Сортируем недели по дате
            sorted_weeks = sorted(weekly_counts.keys())
            
            # Ищем максимальное количество недель подряд
            max_consecutive = 0
            current_consecutive = 0
            
            for i, week_start in enumerate(sorted_weeks):
                if weekly_counts[week_start] >= min_trainings_per_week:
                    if current_consecutive == 0:
                        current_consecutive = 1
                    else:
                        # Проверяем, что неделя идет подряд
                        prev_week = sorted_weeks[i-1]
                        if (week_start - prev_week).days == 7:
                            current_consecutive += 1
                        else:
                            current_consecutive = 1
                    
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0
            
            return max_consecutive
    
    @classmethod
    async def find_consecutive_months_with_min_trainings(cls, user_id: int, min_trainings_per_week: int = 1, min_consecutive_months: int = 2):
        """
        Находит максимальное количество месяцев подряд, когда пользователь выполнил минимум указанное количество тренировок в неделю
        Возвращает количество месяцев подряд
        """
        async with async_session_maker() as session:
            # Получаем все завершенные тренировки пользователя
            query = select(cls.model.completed_at).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED',
                cls.model.completed_at.isnot(None)
            ).order_by(cls.model.completed_at.asc())
            
            result = await session.execute(query)
            completed_dates = result.scalars().all()
            
            if not completed_dates:
                return 0
            
            # Группируем тренировки по неделям и месяцам
            from datetime import timedelta
            weekly_counts = {}
            monthly_weekly_counts = {}
            
            for completed_date in completed_dates:
                # Находим начало недели (понедельник)
                days_since_monday = completed_date.weekday()
                week_start = completed_date.date() - timedelta(days=days_since_monday)
                
                # Находим месяц
                month_key = (week_start.year, week_start.month)
                
                if week_start not in weekly_counts:
                    weekly_counts[week_start] = 0
                weekly_counts[week_start] += 1
                
                if month_key not in monthly_weekly_counts:
                    monthly_weekly_counts[month_key] = []
                monthly_weekly_counts[month_key].append(week_start)
            
            # Сортируем месяцы по дате
            sorted_months = sorted(monthly_weekly_counts.keys())
            
            # Ищем максимальное количество месяцев подряд
            max_consecutive = 0
            current_consecutive = 0
            
            for i, month_key in enumerate(sorted_months):
                # Проверяем, что в месяце есть недели с достаточным количеством тренировок
                month_has_qualifying_weeks = False
                for week_start in monthly_weekly_counts[month_key]:
                    if weekly_counts[week_start] >= min_trainings_per_week:
                        month_has_qualifying_weeks = True
                        break
                
                if month_has_qualifying_weeks:
                    if current_consecutive == 0:
                        current_consecutive = 1
                    else:
                        # Проверяем, что месяц идет подряд
                        prev_month_key = sorted_months[i-1]
                        prev_year, prev_month = prev_month_key
                        current_year, current_month = month_key
                        
                        # Вычисляем разницу в месяцах
                        month_diff = (current_year - prev_year) * 12 + (current_month - prev_month)
                        if month_diff == 1:
                            current_consecutive += 1
                        else:
                            current_consecutive = 1
                    
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0
            
            return max_consecutive
    
    @classmethod
    async def find_consecutive_year_with_min_trainings(cls, user_id: int, min_trainings_per_week: int = 1):
        """
        Проверяет, выполнил ли пользователь минимум указанное количество тренировок в неделю в течение года
        Возвращает True, если условие выполнено
        """
        async with async_session_maker() as session:
            # Получаем все завершенные тренировки пользователя
            query = select(cls.model.completed_at).filter(
                cls.model.user_id == user_id,
                cls.model.status == 'PASSED',
                cls.model.completed_at.isnot(None)
            ).order_by(cls.model.completed_at.asc())
            
            result = await session.execute(query)
            completed_dates = result.scalars().all()
            
            if not completed_dates:
                return False
            
            # Группируем тренировки по неделям
            from datetime import timedelta
            weekly_counts = {}
            
            for completed_date in completed_dates:
                # Находим начало недели (понедельник)
                days_since_monday = completed_date.weekday()
                week_start = completed_date.date() - timedelta(days=days_since_monday)
                
                if week_start not in weekly_counts:
                    weekly_counts[week_start] = 0
                weekly_counts[week_start] += 1
            
            # Сортируем недели по дате
            sorted_weeks = sorted(weekly_counts.keys())
            
            if len(sorted_weeks) < 52:  # Меньше года
                return False
            
            # Проверяем последние 52 недели (год)
            year_weeks = sorted_weeks[-52:]
            qualifying_weeks = 0
            
            for week_start in year_weeks:
                if weekly_counts[week_start] >= min_trainings_per_week:
                    qualifying_weeks += 1
            
            # Требуем минимум 80% недель (примерно 42 недели из 52)
            return qualifying_weeks >= 42
        return await super().update(object_uuid, **values)
