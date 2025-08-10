from datetime import date, timedelta
from typing import List, Optional
import json
from fastapi import HTTPException

from app.trainings.dao import TrainingDAO
from app.user_training.dao import UserTrainingDAO
from app.user_training.models import TrainingStatus


class ScheduleGenerator:
    """Сервис для генерации расписания тренировок"""
    
    @staticmethod
    def get_next_training_date(training_days: List[int], from_date: Optional[date] = None) -> date:
        """
        Получить следующую дату тренировки
        
        Args:
            training_days: Список дней недели (1=понедельник, 7=воскресенье)
            from_date: Дата, с которой начинать поиск (по умолчанию сегодня)
            
        Returns:
            Дата следующей тренировки
        """
        if from_date is None:
            from_date = date.today()
            
        if not training_days:
            return from_date
            
        # Получаем день недели (1=понедельник, 7=воскресенье)
        current_weekday = from_date.isoweekday()
        
        # Если сегодня день тренировки, возвращаем сегодня
        if current_weekday in training_days:
            return from_date
            
        # Ищем следующий день тренировки
        for i in range(1, 8):  # Проверяем следующие 7 дней
            check_date = from_date + timedelta(days=i)
            if check_date.isoweekday() in training_days:
                return check_date
                
        # Если не нашли в ближайшие 7 дней, возвращаем сегодня
        return from_date
    
    @staticmethod
    def generate_training_dates(training_days: List[int], start_date: date, count: int = 10) -> List[date]:
        """
        Сгенерировать список дат тренировок
        
        Args:
            training_days: Список дней недели (1=понедельник, 7=воскресенье)
            start_date: Дата начала
            count: Количество тренировок для генерации
            
        Returns:
            Список дат тренировок
        """
        if not training_days:
            return [start_date]
            
        training_dates = []
        current_date = start_date
        
        for _ in range(count):
            training_dates.append(current_date)
            current_date = ScheduleGenerator.get_next_training_date(training_days, current_date + timedelta(days=1))
            
        return training_dates
    
    @staticmethod
    def parse_training_days(training_days_str: str) -> List[int]:
        """
        Парсить строку с днями тренировок из JSON
        
        Args:
            training_days_str: Строка в формате JSON, например "[1,3,5]"
            
        Returns:
            Список дней недели
        """
        if not training_days_str:
            return [1, 3, 5]  # По умолчанию: пн, ср, пт
            
        try:
            return json.loads(training_days_str)
        except (json.JSONDecodeError, TypeError):
            return [1, 3, 5]  # По умолчанию: пн, ср, пт

    @staticmethod
    async def create_next_stage_schedule(user_program_id: int, program_id: int, user_id: int, 
                                       current_stage: int, training_days: List[int], 
                                       training_dao, user_training_dao) -> dict:
        """
        Создать расписание для следующего этапа (включая rest days)
        Расписание всегда начинается с понедельника текущей недели, но активной становится только тренировка, совпадающая с сегодняшней датой.
        """
        # Пытаемся найти тренировки следующего этапа
        next_stage = current_stage + 1
        next_stage_trainings = await training_dao.find_by_program_and_stage(program_id=program_id, stage=next_stage)
        # Если нет тренировок следующего этапа, используем текущий
        if not next_stage_trainings:
            next_stage_trainings = await training_dao.find_by_program_and_stage(program_id=program_id, stage=current_stage)
            next_stage = current_stage
        if not next_stage_trainings:
            return {
                "created": False,
                "message": "Нет доступных тренировок для создания расписания",
                "stage": next_stage
            }
        from datetime import date, timedelta, datetime
        today = date.today()
        # Начинаем с текущего дня
        start_date = today
        days_ahead = 28
        created_count = 0
        trainings_count = 0
        for i in range(days_ahead):
            current_date = start_date + timedelta(days=i)
            # Вычисляем день программы (1-7, циклически)
            program_day = ((i % 7) + 1)
            weekday = program_day  # weekday теперь содержит день программы
            week = (i // 7) + 1
            if program_day in training_days:
                training = next_stage_trainings[trainings_count % len(next_stage_trainings)]
                # Статус: 'active' если дата совпадает с today, иначе 'blocked_yet'
                status = 'active' if current_date == today else 'blocked_yet'
                user_training_data = {
                    'user_program_id': user_program_id,
                    'program_id': program_id,
                    'training_id': training.id,
                    'user_id': user_id,
                    'training_date': current_date,
                    'stage': training.stage,
                    'status': status,
                    'week': week,
                    'weekday': weekday,
                    'is_rest_day': False
                }
                trainings_count += 1
            else:
                # Статус: 'active' если дата совпадает с today (даже для выходных), иначе 'blocked_yet'
                status = 'active' if current_date == today else 'blocked_yet'
                user_training_data = {
                    'user_program_id': user_program_id,
                    'program_id': program_id,
                    'training_id': None,
                    'user_id': user_id,
                    'training_date': current_date,
                    'stage': next_stage,
                    'status': status,
                    'week': week,
                    'weekday': weekday,
                    'is_rest_day': True
                }
            await user_training_dao.add(**user_training_data)
            created_count += 1
        return {
            "created": True,
            "message": f"Создано {created_count} дней расписания (включая rest days) для этапа {next_stage}",
            "stage": next_stage,
            "count": created_count
        } 