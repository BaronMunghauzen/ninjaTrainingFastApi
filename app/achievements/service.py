from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.achievements.dao import AchievementDAO, AchievementTypeDAO
from app.user_training.dao import UserTrainingDAO
from app.users.dao import UsersDAO
from app.user_program.dao import UserProgramDAO
from app.programs.dao import ProgramDAO
from app.achievements.models import Achievement, AchievementType
from app.achievements.schemas import AchievementCheckResponse
from datetime import date, datetime, timedelta
import uuid


class AchievementService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.achievement_dao = AchievementDAO(session)
        self.achievement_type_dao = AchievementTypeDAO(session)
        # Используем статические методы DAO
        self.user_training_dao = UserTrainingDAO
        self.users_dao = UsersDAO
        self.user_program_dao = UserProgramDAO
        self.program_dao = ProgramDAO

    async def ensure_achievement_types_exist(self):
        """Убедиться, что все типы достижений существуют в базе"""
        achievement_types = [
            # Временные достижения
            {
                "name": "Ранняя пташка",
                "description": "Завершить 5 тренировок с 5 до 8 утра",
                "category": "time_based",
                "subcategory": "morning",
                "requirements": "5_trainings_5_8_am",
                "points": 10,
                "order": 1
            },
            {
                "name": "Сова",
                "description": "Завершить 5 тренировок с 21 до 00",
                "category": "time_based",
                "subcategory": "night",
                "requirements": "5_trainings_21_00",
                "points": 10,
                "order": 2
            },
            {
                "name": "С Новым годом",
                "description": "Завершить тренировку 1 января",
                "category": "holiday",
                "subcategory": "new_year",
                "requirements": "training_on_january_1",
                "points": 5,
                "order": 3
            },
            {
                "name": "Международный женский день",
                "description": "Завершить тренировку 8 марта",
                "category": "holiday",
                "subcategory": "womens_day",
                "requirements": "training_on_march_8",
                "points": 5,
                "order": 4
            },
            {
                "name": "Мужской день",
                "description": "Завершить тренировку 23 февраля",
                "category": "holiday",
                "subcategory": "mens_day",
                "requirements": "training_on_february_23",
                "points": 5,
                "order": 5
            },
            # Программные достижения
            {
                "name": "Мощь и сила",
                "description": "Завершить полную программу тренировок",
                "category": "program",
                "subcategory": "completion",
                "requirements": "complete_full_program",
                "points": 50,
                "order": 6
            },
            # Количественные достижения
            {
                "name": "1 тренировка",
                "description": "Завершить первую тренировку",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "1_training",
                "points": 1,
                "order": 7
            },
            {
                "name": "3 тренировки",
                "description": "Завершить 3 тренировки",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "3_trainings",
                "points": 3,
                "order": 8
            },
            {
                "name": "5 тренировок",
                "description": "Завершить 5 тренировок",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "5_trainings",
                "points": 5,
                "order": 9
            },
            {
                "name": "7 тренировок",
                "description": "Завершить 7 тренировок",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "7_trainings",
                "points": 7,
                "order": 10
            },
            {
                "name": "10 тренировок",
                "description": "Завершить 10 тренировок",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "10_trainings",
                "points": 10,
                "order": 11
            },
            {
                "name": "15 тренировок",
                "description": "Завершить 15 тренировок",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "15_trainings",
                "points": 15,
                "order": 12
            },
            {
                "name": "20 тренировок",
                "description": "Завершить 20 тренировок",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "20_trainings",
                "points": 20,
                "order": 13
            },
            {
                "name": "25 тренировок",
                "description": "Завершить 25 тренировок",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "25_trainings",
                "points": 25,
                "order": 14
            },
            {
                "name": "30 тренировок",
                "description": "Завершить 30 тренировок",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "30_trainings",
                "points": 30,
                "order": 15
            },
            {
                "name": "40 тренировок",
                "description": "Завершить 40 тренировок",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "40_trainings",
                "points": 40,
                "order": 16
            },
            {
                "name": "50 тренировок",
                "description": "Завершить 50 тренировок",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "50_trainings",
                "points": 50,
                "order": 17
            },
            {
                "name": "75 тренировок",
                "description": "Завершить 75 тренировок",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "75_trainings",
                "points": 75,
                "order": 18
            },
            {
                "name": "100 тренировок",
                "description": "Завершить 100 тренировок",
                "category": "count",
                "subcategory": "milestone",
                "requirements": "100_trainings",
                "points": 100,
                "order": 19
            },
            # Недельные достижения
            {
                "name": "3 раза в неделю",
                "description": "Завершить 3 тренировки за одну неделю",
                "category": "weekly",
                "subcategory": "frequency",
                "requirements": "3_trainings_per_week",
                "points": 15,
                "order": 20
            },
            {
                "name": "4 раза в неделю",
                "description": "Завершить 4 тренировки за одну неделю",
                "category": "weekly",
                "subcategory": "frequency",
                "requirements": "4_trainings_per_week",
                "points": 20,
                "order": 21
            },
            {
                "name": "5 раз в неделю",
                "description": "Завершить 5 тренировок за одну неделю",
                "category": "weekly",
                "subcategory": "frequency",
                "requirements": "5_trainings_per_week",
                "points": 25,
                "order": 22
            },
            {
                "name": "6 раз в неделю",
                "description": "Завершить 6 тренировок за одну неделю",
                "category": "weekly",
                "subcategory": "frequency",
                "requirements": "6_trainings_per_week",
                "points": 30,
                "order": 23
            },
            {
                "name": "7 раз в неделю",
                "description": "Завершить 7 тренировок за одну неделю",
                "category": "weekly",
                "subcategory": "frequency",
                "requirements": "7_trainings_per_week",
                "points": 35,
                "order": 24
            },
            # Непрерывные периоды
            {
                "name": "2 недели подряд",
                "description": "Завершить минимум 1 тренировку в неделю 2 недели подряд",
                "category": "consecutive",
                "subcategory": "weeks",
                "requirements": "2_weeks_consecutive",
                "points": 20,
                "order": 25
            },
            {
                "name": "3 недели подряд",
                "description": "Завершить минимум 1 тренировку в неделю 3 недели подряд",
                "category": "consecutive",
                "subcategory": "weeks",
                "requirements": "3_weeks_consecutive",
                "points": 30,
                "order": 26
            },
            {
                "name": "4 недели подряд",
                "description": "Завершить минимум 1 тренировку в неделю 4 недели подряд",
                "category": "consecutive",
                "subcategory": "weeks",
                "requirements": "4_weeks_consecutive",
                "points": 40,
                "order": 27
            },
            {
                "name": "5 недель подряд",
                "description": "Завершить минимум 1 тренировку в неделю 5 недель подряд",
                "category": "consecutive",
                "subcategory": "weeks",
                "requirements": "5_weeks_consecutive",
                "points": 50,
                "order": 28
            },
            {
                "name": "6 недель подряд",
                "description": "Завершить минимум 1 тренировку в неделю 6 недель подряд",
                "category": "consecutive",
                "subcategory": "weeks",
                "requirements": "6_weeks_consecutive",
                "points": 60,
                "order": 29
            },
            {
                "name": "7 недель подряд",
                "description": "Завершить минимум 1 тренировку в неделю 7 недель подряд",
                "category": "consecutive",
                "subcategory": "weeks",
                "requirements": "7_weeks_consecutive",
                "points": 70,
                "order": 30
            },
            {
                "name": "2 месяца подряд",
                "description": "Завершить минимум 1 тренировку в неделю 2 месяца подряд",
                "category": "consecutive",
                "subcategory": "months",
                "requirements": "2_months_consecutive",
                "points": 100,
                "order": 31
            },
            {
                "name": "3 месяца подряд",
                "description": "Завершить минимум 1 тренировку в неделю 3 месяца подряд",
                "category": "consecutive",
                "subcategory": "months",
                "requirements": "3_months_consecutive",
                "points": 150,
                "order": 32
            },
            {
                "name": "4 месяца подряд",
                "description": "Завершить минимум 1 тренировку в неделю 4 месяца подряд",
                "category": "consecutive",
                "subcategory": "months",
                "requirements": "4_months_consecutive",
                "points": 200,
                "order": 33
            },
            {
                "name": "5 месяцев подряд",
                "description": "Завершить минимум 1 тренировку в неделю 5 месяцев подряд",
                "category": "consecutive",
                "subcategory": "months",
                "requirements": "5_months_consecutive",
                "points": 250,
                "order": 34
            },
            {
                "name": "6 месяцев подряд",
                "description": "Завершить минимум 1 тренировку в неделю 6 месяцев подряд",
                "category": "consecutive",
                "subcategory": "months",
                "requirements": "6_months_consecutive",
                "points": 300,
                "order": 35
            },
            {
                "name": "7 месяцев подряд",
                "description": "Завершить минимум 1 тренировку в неделю 7 месяцев подряд",
                "category": "consecutive",
                "subcategory": "months",
                "requirements": "7_months_consecutive",
                "points": 350,
                "order": 36
            },
            {
                "name": "8 месяцев подряд",
                "description": "Завершить минимум 1 тренировку в неделю 8 месяцев подряд",
                "category": "consecutive",
                "subcategory": "months",
                "requirements": "8_months_consecutive",
                "points": 400,
                "order": 37
            },
            {
                "name": "9 месяцев подряд",
                "description": "Завершить минимум 1 тренировку в неделю 9 месяцев подряд",
                "category": "consecutive",
                "subcategory": "months",
                "requirements": "9_months_consecutive",
                "points": 450,
                "order": 38
            },
            {
                "name": "10 месяцев подряд",
                "description": "Завершить минимум 1 тренировку в неделю 10 месяцев подряд",
                "category": "consecutive",
                "subcategory": "months",
                "requirements": "10_months_consecutive",
                "points": 500,
                "order": 39
            },
            {
                "name": "11 месяцев подряд",
                "description": "Завершить минимум 1 тренировку в неделю 11 месяцев подряд",
                "category": "consecutive",
                "subcategory": "months",
                "requirements": "11_months_consecutive",
                "points": 550,
                "order": 40
            },
            {
                "name": "1 год без перерывов",
                "description": "Завершить минимум 1 тренировку в неделю в течение года",
                "category": "consecutive",
                "subcategory": "year",
                "requirements": "1_year_consecutive",
                "points": 1000,
                "order": 41
            }
        ]

        for achievement_type_data in achievement_types:
            existing = await self.achievement_type_dao.find_by_name(achievement_type_data["name"])
            if not existing:
                # Создаем новый тип достижения с правильными полями
                achievement_type = AchievementType(
                    uuid=str(uuid.uuid4()),
                    name=achievement_type_data["name"],
                    description=achievement_type_data["description"],
                    category=achievement_type_data["category"],
                    subcategory=achievement_type_data.get("subcategory"),
                    requirements=achievement_type_data.get("requirements"),
                    points=achievement_type_data.get("points"),
                    is_active=True
                )
                await self.achievement_type_dao.add(achievement_type)

    async def check_early_bird_achievement(self, user_uuid: str) -> AchievementCheckResponse:
        """Проверить достижение 'Ранняя пташка'"""
        user = await self.users_dao.find_by_uuid(user_uuid)
        if not user:
            return AchievementCheckResponse(
                success=False,
                message="Пользователь не найден"
            )

        achievement_type = await self.achievement_type_dao.find_by_name("Ранняя пташка")
        if not achievement_type:
            return AchievementCheckResponse(
                success=False,
                message="Тип достижения не найден"
            )

        # Проверяем, есть ли уже достижение
        if await self.achievement_dao.check_achievement_exists(user.id, achievement_type.id):
            return AchievementCheckResponse(
                success=True,
                message="Достижение уже получено",
                already_earned=True
            )

        # Проверяем условия
        early_trainings = await self.user_training_dao.find_early_morning_completed_trainings(user.id)
        
        if len(early_trainings) >= 5:
            # Создаем достижение
            achievement = await self.achievement_dao.create_achievement(
                achievement_type_id=achievement_type.id,
                user_id=user.id,
                user_training_id=early_trainings[0].id
            )
            
            return AchievementCheckResponse(
                success=True,
                message="Достижение 'Ранняя пташка' получено!",
                achievement=achievement
            )
        
        return AchievementCheckResponse(
            success=True,
            message=f"Прогресс: {len(early_trainings)}/5 тренировок с 5 до 8 утра"
        )

    async def check_night_owl_achievement(self, user_uuid: str) -> AchievementCheckResponse:
        """Проверить достижение 'Сова'"""
        user = await self.users_dao.find_by_uuid(user_uuid)
        if not user:
            return AchievementCheckResponse(
                success=False,
                message="Пользователь не найден"
            )

        achievement_type = await self.achievement_type_dao.find_by_name("Сова")
        if not achievement_type:
            return AchievementCheckResponse(
                success=False,
                message="Тип достижения не найден"
            )

        if await self.achievement_dao.check_achievement_exists(user.id, achievement_type.id):
            return AchievementCheckResponse(
                success=True,
                message="Достижение уже получено",
                already_earned=True
            )

        late_trainings = await self.user_training_dao.find_late_night_completed_trainings(user.id)
        
        if len(late_trainings) >= 5:
            achievement = await self.achievement_dao.create_achievement(
                achievement_type_id=achievement_type.id,
                user_id=user.id,
                user_training_id=late_trainings[0].id
            )
            
            return AchievementCheckResponse(
                success=True,
                message="Достижение 'Сова' получено!",
                achievement=achievement
            )
        
        return AchievementCheckResponse(
            success=True,
            message=f"Прогресс: {len(late_trainings)}/5 тренировок с 21 до 00"
        )

    async def check_new_year_achievement(self, user_uuid: str) -> AchievementCheckResponse:
        """Проверить достижение 'С Новым годом'"""
        user = await self.users_dao.find_by_uuid(user_uuid)
        if not user:
            return AchievementCheckResponse(
                success=False,
                message="Пользователь не найден"
            )

        achievement_type = await self.achievement_type_dao.find_by_name("С Новым годом")
        if not achievement_type:
            return AchievementCheckResponse(
                success=False,
                message="Тип достижения не найден"
            )

        if await self.achievement_dao.check_achievement_exists(user.id, achievement_type.id):
            return AchievementCheckResponse(
                success=True,
                message="Достижение уже получено",
                already_earned=True
            )

        new_year_trainings = await self.user_training_dao.find_new_year_trainings(user.id)
        
        if new_year_trainings:
            achievement = await self.achievement_dao.create_achievement(
                achievement_type_id=achievement_type.id,
                user_id=user.id,
                user_training_id=new_year_trainings[0].id
            )
            
            return AchievementCheckResponse(
                success=True,
                message="Достижение 'С Новым годом' получено!",
                achievement=achievement
            )
        
        return AchievementCheckResponse(
            success=True,
            message="Достижение 'С Новым годом' еще не получено"
        )

    async def check_womens_day_achievement(self, user_uuid: str) -> AchievementCheckResponse:
        """Проверить достижение 'Международный женский день'"""
        user = await self.users_dao.find_by_uuid(user_uuid)
        if not user:
            return AchievementCheckResponse(
                success=False,
                message="Пользователь не найден"
            )

        achievement_type = await self.achievement_type_dao.find_by_name("Международный женский день")
        if not achievement_type:
            return AchievementCheckResponse(
                success=False,
                message="Тип достижения не найден"
            )

        if await self.achievement_dao.check_achievement_exists(user.id, achievement_type.id):
            return AchievementCheckResponse(
                success=True,
                message="Достижение уже получено",
                already_earned=True
            )

        womens_day_trainings = await self.user_training_dao.find_womens_day_trainings(user.id)
        
        if womens_day_trainings:
            achievement = await self.achievement_dao.create_achievement(
                achievement_type_id=achievement_type.id,
                user_id=user.id,
                user_training_id=womens_day_trainings[0].id
            )
            
            return AchievementCheckResponse(
                success=True,
                message="Достижение 'Международный женский день' получено!",
                achievement=achievement
            )
        
        return AchievementCheckResponse(
            success=True,
            message="Достижение 'Международный женский день' еще не получено"
        )

    async def check_mens_day_achievement(self, user_uuid: str) -> AchievementCheckResponse:
        """Проверить достижение 'Мужской день'"""
        user = await self.users_dao.find_by_uuid(user_uuid)
        if not user:
            return AchievementCheckResponse(
                success=False,
                message="Пользователь не найден"
            )

        achievement_type = await self.achievement_type_dao.find_by_name("Мужской день")
        if not achievement_type:
            return AchievementCheckResponse(
                success=False,
                message="Тип достижения не найден"
            )

        if await self.achievement_dao.check_achievement_exists(user.id, achievement_type.id):
            return AchievementCheckResponse(
                success=True,
                message="Достижение уже получено",
                already_earned=True
            )

        mens_day_trainings = await self.user_training_dao.find_mens_day_trainings(user.id)
        
        if mens_day_trainings:
            achievement = await self.achievement_dao.create_achievement(
                achievement_type_id=achievement_type.id,
                user_id=user.id,
                user_training_id=mens_day_trainings[0].id
            )
            
            return AchievementCheckResponse(
                success=True,
                message="Достижение 'Мужской день' получено!",
                achievement=achievement
            )
        
        return AchievementCheckResponse(
            success=True,
            message="Достижение 'Мужской день' еще не получено"
        )

    async def check_power_and_strength_achievement(self, user_uuid: str) -> AchievementCheckResponse:
        """Проверить достижение 'Мощь и сила'"""
        user = await self.users_dao.find_by_uuid(user_uuid)
        if not user:
            return AchievementCheckResponse(
                success=False,
                message="Пользователь не найден"
            )

        achievement_type = await self.achievement_type_dao.find_by_name("Мощь и сила")
        if not achievement_type:
            return AchievementCheckResponse(
                success=False,
                message="Тип достижения не найден"
            )

        if await self.achievement_dao.check_achievement_exists(user.id, achievement_type.id):
            return AchievementCheckResponse(
                success=True,
                message="Достижение уже получено",
                already_earned=True
            )

        completed_program_trainings = await self.user_training_dao.find_completed_program_trainings(user.id)
        
        if completed_program_trainings:
            achievement = await self.achievement_dao.create_achievement(
                achievement_type_id=achievement_type.id,
                user_id=user.id,
                user_program_id=completed_program_trainings[0].user_program_id,
                program_id=completed_program_trainings[0].user_program.program_id if completed_program_trainings[0].user_program else None
            )
            
            return AchievementCheckResponse(
                success=True,
                message="Достижение 'Мощь и сила' получено!",
                achievement=achievement
            )
        
        return AchievementCheckResponse(
            success=True,
            message="Достижение 'Мощь и сила' еще не получено"
        )

    async def check_training_count_achievements(self, user_uuid: str) -> List[AchievementCheckResponse]:
        """Проверить количественные достижения"""
        user = await self.users_dao.find_by_uuid(user_uuid)
        if not user:
            return [AchievementCheckResponse(
                success=False,
                message="Пользователь не найден"
            )]

        completed_count = await self.user_training_dao.count_completed_trainings(user.id)
        
        # Определяем все возможные количественные достижения
        count_achievements = [1, 3, 5, 7, 10, 15, 20, 25, 30, 40, 50, 75, 100]
        results = []

        for count in count_achievements:
            if completed_count >= count:
                achievement_type = await self.achievement_type_dao.find_by_name(f"{count} тренировка{'и' if count > 1 else ''}")
                if not achievement_type:
                    continue

                # Проверяем, есть ли уже достижение
                if not await self.achievement_dao.check_achievement_exists(user.id, achievement_type.id):
                    # Создаем достижение
                    last_training = await self.user_training_dao.find_last_completed_training(user.id)
                    achievement = await self.achievement_dao.create_achievement(
                        achievement_type_id=achievement_type.id,
                        user_id=user.id,
                        user_training_id=last_training.id if last_training else None
                    )
                    
                    results.append(AchievementCheckResponse(
                        success=True,
                        message=f"Достижение '{count} тренировка{'и' if count > 1 else ''}' получено!",
                        achievement=achievement
                    ))
                else:
                    results.append(AchievementCheckResponse(
                        success=True,
                        message=f"Достижение '{count} тренировка{'и' if count > 1 else ''}' уже получено",
                        already_earned=True
                    ))
            else:
                results.append(AchievementCheckResponse(
                    success=True,
                    message=f"Прогресс: {completed_count}/{count} тренировок"
                ))

        return results

    async def check_weekly_training_achievements(self, user_uuid: str) -> List[AchievementCheckResponse]:
        """Проверить недельные достижения"""
        user = await self.users_dao.find_by_uuid(user_uuid)
        if not user:
            return [AchievementCheckResponse(
                success=False,
                message="Пользователь не найден"
            )]

        weekly_achievements = await self.user_training_dao.find_weekly_training_achievements(user.id)
        results = []

        for week_data in weekly_achievements:
            week_start = week_data['week_start']
            training_count = week_data['training_count']
            
            # Определяем все возможные недельные достижения
            weekly_counts = [3, 4, 5, 6, 7]
            
            for count in weekly_counts:
                if training_count >= count:
                    achievement_type = await self.achievement_type_dao.find_by_name(f"{count} раз{'а' if count in [3, 4] else ''} в неделю")
                    if not achievement_type:
                        continue

                    # Проверяем, есть ли уже достижение за эту неделю
                    existing_achievement = await self.achievement_dao.find_by_name_and_user(
                        f"{count} раз{'а' if count in [3, 4] else ''} в неделю", user.id
                    )
                    
                    if not existing_achievement:
                        # Создаем достижение
                        achievement = await self.achievement_dao.create_achievement(
                            achievement_type_id=achievement_type.id,
                            user_id=user.id
                        )
                        
                        results.append(AchievementCheckResponse(
                            success=True,
                            message=f"Достижение '{count} раз{'а' if count in [3, 4] else ''} в неделю' получено за неделю {week_start}!",
                            achievement=achievement
                        ))
                    else:
                        results.append(AchievementCheckResponse(
                            success=True,
                            message=f"Достижение '{count} раз{'а' if count in [3, 4] else ''} в неделю' уже получено за неделю {week_start}",
                            already_earned=True
                        ))

        return results

    async def check_consecutive_weeks_achievements(self, user_uuid: str) -> List[AchievementCheckResponse]:
        """Проверить достижения за непрерывные недели"""
        user = await self.users_dao.find_by_uuid(user_uuid)
        if not user:
            return [AchievementCheckResponse(
                success=False,
                message="Пользователь не найден"
            )]

        consecutive_weeks = await self.user_training_dao.find_consecutive_weeks_with_min_trainings(user.id)
        results = []

        for weeks_count in range(2, 8):  # 2-7 недель
            if consecutive_weeks >= weeks_count:
                achievement_type = await self.achievement_type_dao.find_by_name(f"{weeks_count} недел{'и' if weeks_count in [2, 3, 4] else 'ь'} подряд")
                if not achievement_type:
                    continue

                if not await self.achievement_dao.check_achievement_exists(user.id, achievement_type.id):
                    achievement = await self.achievement_dao.create_achievement(
                        achievement_type_id=achievement_type.id,
                        user_id=user.id
                    )
                    
                    results.append(AchievementCheckResponse(
                        success=True,
                        message=f"Достижение '{weeks_count} недел{'и' if weeks_count in [2, 3, 4] else 'ь'} подряд' получено!",
                        achievement=achievement
                    ))
                else:
                    results.append(AchievementCheckResponse(
                        success=True,
                        message=f"Достижение '{weeks_count} недел{'и' if weeks_count in [2, 3, 4] else 'ь'} подряд' уже получено",
                        already_earned=True
                    ))
            else:
                results.append(AchievementCheckResponse(
                    success=True,
                    message=f"Прогресс: {consecutive_weeks}/{weeks_count} недель подряд"
                ))

        return results

    async def check_consecutive_months_achievements(self, user_uuid: str) -> List[AchievementCheckResponse]:
        """Проверить достижения за непрерывные месяцы"""
        user = await self.users_dao.find_by_uuid(user_uuid)
        if not user:
            return [AchievementCheckResponse(
                success=False,
                message="Пользователь не найден"
            )]

        consecutive_months = await self.user_training_dao.find_consecutive_months_with_min_trainings(user.id)
        results = []

        for months_count in range(2, 12):  # 2-11 месяцев
            if consecutive_months >= months_count:
                achievement_type = await self.achievement_type_dao.find_by_name(f"{months_count} месяц{'а' if months_count in [2, 3, 4] else 'ев'} подряд")
                if not achievement_type:
                    continue

                if not await self.achievement_dao.check_achievement_exists(user.id, achievement_type.id):
                    achievement = await self.achievement_dao.create_achievement(
                        achievement_type_id=achievement_type.id,
                        user_id=user.id
                    )
                    
                    results.append(AchievementCheckResponse(
                        success=True,
                        message=f"Достижение '{months_count} месяц{'а' if months_count in [2, 3, 4] else 'ев'} подряд' получено!",
                        achievement=achievement
                    ))
                else:
                    results.append(AchievementCheckResponse(
                        success=True,
                        message=f"Достижение '{months_count} месяц{'а' if months_count in [2, 3, 4] else 'ев'} подряд' уже получено",
                        already_earned=True
                    ))
            else:
                results.append(AchievementCheckResponse(
                    success=True,
                    message=f"Прогресс: {consecutive_months}/{months_count} месяцев подряд"
                ))

        return results

    async def check_year_without_breaks_achievement(self, user_uuid: str) -> AchievementCheckResponse:
        """Проверить достижение '1 год без перерывов'"""
        user = await self.users_dao.find_by_uuid(user_uuid)
        if not user:
            return AchievementCheckResponse(
                success=False,
                message="Пользователь не найден"
            )

        achievement_type = await self.achievement_type_dao.find_by_name("1 год без перерывов")
        if not achievement_type:
            return AchievementCheckResponse(
                success=False,
                message="Тип достижения не найден"
            )

        if await self.achievement_dao.check_achievement_exists(user.id, achievement_type.id):
            return AchievementCheckResponse(
                success=True,
                message="Достижение уже получено",
                already_earned=True
            )

        year_success = await self.user_training_dao.find_consecutive_year_with_min_trainings(user.id)
        
        if year_success:
            achievement = await self.achievement_dao.create_achievement(
                achievement_type_id=achievement_type.id,
                user_id=user.id
            )
            
            return AchievementCheckResponse(
                success=True,
                message="Достижение '1 год без перерывов' получено!",
                achievement=achievement
            )
        
        return AchievementCheckResponse(
            success=True,
            message="Достижение '1 год без перерывов' еще не получено"
        )

    async def check_all_achievements_for_user(self, user_uuid: str) -> List[AchievementCheckResponse]:
        """Проверить все достижения для пользователя"""
        # Сначала убеждаемся, что все типы достижений существуют
        await self.ensure_achievement_types_exist()
        
        results = []
        
        # Проверяем все типы достижений
        results.extend(await self.check_early_bird_achievement(user_uuid))
        results.extend(await self.check_night_owl_achievement(user_uuid))
        results.extend(await self.check_new_year_achievement(user_uuid))
        results.extend(await self.check_womens_day_achievement(user_uuid))
        results.extend(await self.check_mens_day_achievement(user_uuid))
        results.extend(await self.check_power_and_strength_achievement(user_uuid))
        results.extend(await self.check_training_count_achievements(user_uuid))
        results.extend(await self.check_weekly_training_achievements(user_uuid))
        results.extend(await self.check_consecutive_weeks_achievements(user_uuid))
        results.extend(await self.check_consecutive_months_achievements(user_uuid))
        results.extend(await self.check_year_without_breaks_achievement(user_uuid))
        
        return results
