import pytest
from datetime import datetime, time, date, timedelta
from unittest.mock import AsyncMock, patch
from app.achievements.service import AchievementService
from app.achievements.models import Achievement
from app.user_training.models import UserTraining
from app.user_program.models import UserProgram
from app.programs.models import Program
from app.users.models import User


class TestConsecutivePeriodsAchievements:
    """Тесты для достижений за непрерывные периоды тренировок"""
    
    @pytest.fixture
    def mock_user(self):
        """Мок пользователя"""
        user = User()
        user.id = 1
        user.uuid = "test-user-uuid"
        return user
    
    @pytest.fixture
    def mock_program(self):
        """Мок программы"""
        program = Program()
        program.id = 1
        program.uuid = "program-uuid-1"
        program.name = "Тестовая программа"
        return program
    
    @pytest.fixture
    def mock_user_program(self, mock_program):
        """Мок программы пользователя"""
        user_program = UserProgram()
        user_program.id = 1
        user_program.uuid = "user-program-uuid-1"
        user_program.user_id = 1
        user_program.program_id = 1
        user_program.status = "active"
        user_program.program = mock_program
        return user_program
    
    @pytest.fixture
    def mock_last_training(self, mock_user_program):
        """Мок последней завершенной тренировки"""
        training = UserTraining()
        training.id = 1
        training.uuid = "training-uuid-1"
        training.user_id = 1
        training.user_program_id = 1
        training.status = "completed"
        training.completed_at = datetime(2024, 1, 15, 14, 0, 0)
        training.user_program = mock_user_program
        return training
    
    @pytest.fixture
    def mock_achievement(self):
        """Мок достижения"""
        achievement = Achievement()
        achievement.id = 1
        achievement.name = "3 недели подряд"
        achievement.user_id = 1
        achievement.status = "active"
        return achievement
    
    @pytest.mark.asyncio
    async def test_check_consecutive_weeks_achievements_success(self, mock_user, mock_last_training, mock_achievement):
        """Тест успешного получения достижений за непрерывные недели"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.async_session_maker') as mock_session_maker:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_training_dao.return_value.find_consecutive_weeks_with_min_trainings.return_value = 5  # 5 недель подряд
            mock_training_dao.return_value.find_last_completed_training.return_value = mock_last_training
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_achievement_dao.return_value.create.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_consecutive_weeks_achievements("test-user-uuid")
            
            # Проверки
            assert len(result) == 5  # 2, 3, 4, 5 недели подряд
            achievement_names = [ach.name for ach in result]
            expected_names = [
                "2 недели подряд", "3 недели подряд", "4 недели подряд", "5 недель подряд"
            ]
            assert achievement_names == expected_names
            
            # Проверяем, что методы были вызваны
            mock_users_dao.return_value.find_by_uuid.assert_called_once_with("test-user-uuid")
            assert mock_training_dao.return_value.find_consecutive_weeks_with_min_trainings.call_count == 6
    
    @pytest.mark.asyncio
    async def test_check_consecutive_months_achievements_success(self, mock_user, mock_last_training, mock_achievement):
        """Тест успешного получения достижений за непрерывные месяцы"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.async_session_maker') as mock_session_maker:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_training_dao.return_value.find_consecutive_months_with_min_trainings.return_value = 4  # 4 месяца подряд
            mock_training_dao.return_value.find_last_completed_training.return_value = mock_last_training
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_achievement_dao.return_value.create.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_consecutive_months_achievements("test-user-uuid")
            
            # Проверки
            assert len(result) == 3  # 2, 3, 4 месяца подряд
            achievement_names = [ach.name for ach in result]
            expected_names = [
                "2 месяца подряд", "3 месяца подряд", "4 месяца подряд"
            ]
            assert achievement_names == expected_names
            
            # Проверяем, что методы были вызваны
            mock_users_dao.return_value.find_by_uuid.assert_called_once_with("test-user-uuid")
            assert mock_training_dao.return_value.find_consecutive_months_with_min_trainings.call_count == 10
    
    @pytest.mark.asyncio
    async def test_check_year_without_breaks_achievement_success(self, mock_user, mock_last_training, mock_achievement):
        """Тест успешного получения достижения за год без перерывов"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.async_session_maker') as mock_session_maker:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_training_dao.return_value.find_consecutive_year_with_min_trainings.return_value = True
            mock_training_dao.return_value.find_last_completed_training.return_value = mock_last_training
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_achievement_dao.return_value.create.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_year_without_breaks_achievement("test-user-uuid")
            
            # Проверки
            assert result is not None
            assert result.name == "1 год без перерывов"
            
            # Проверяем, что методы были вызваны
            mock_users_dao.return_value.find_by_uuid.assert_called_once_with("test-user-uuid")
            mock_training_dao.return_value.find_consecutive_year_with_min_trainings.assert_called_once_with(1, 1)
    
    @pytest.mark.asyncio
    async def test_check_year_without_breaks_achievement_no_condition(self, mock_user):
        """Тест, когда условие для года без перерывов не выполнено"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_training_dao.return_value.find_consecutive_year_with_min_trainings.return_value = False
            
            # Выполнение теста
            result = await AchievementService.check_year_without_breaks_achievement("test-user-uuid")
            
            # Проверки
            assert result is None
    
    @pytest.mark.asyncio
    async def test_check_consecutive_weeks_achievements_no_new(self, mock_user):
        """Тест, когда нет новых достижений за непрерывные недели"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_training_dao.return_value.find_consecutive_weeks_with_min_trainings.return_value = 1  # Меньше 2 недель
            
            # Выполнение теста
            result = await AchievementService.check_consecutive_weeks_achievements("test-user-uuid")
            
            # Проверки
            assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_check_consecutive_months_achievements_no_new(self, mock_user):
        """Тест, когда нет новых достижений за непрерывные месяцы"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_training_dao.return_value.find_consecutive_months_with_min_trainings.return_value = 1  # Меньше 2 месяцев
            
            # Выполнение теста
            result = await AchievementService.check_consecutive_months_achievements("test-user-uuid")
            
            # Проверки
            assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_check_all_achievements_includes_consecutive_periods(self, mock_user, mock_achievement):
        """Тест, что check_all_achievements включает проверку достижений за непрерывные периоды"""
        with patch('app.achievements.service.AchievementService.check_early_bird_achievement') as mock_check_early_bird, \
             patch('app.achievements.service.AchievementService.check_night_owl_achievement') as mock_check_night_owl, \
             patch('app.achievements.service.AchievementService.check_new_year_achievement') as mock_check_new_year, \
             patch('app.achievements.service.AchievementService.check_womens_day_achievement') as mock_check_womens_day, \
             patch('app.achievements.service.AchievementService.check_mens_day_achievement') as mock_check_mens_day, \
             patch('app.achievements.service.AchievementService.check_power_and_strength_achievement') as mock_check_power_and_strength, \
             patch('app.achievements.service.AchievementService.check_training_count_achievements') as mock_check_training_count, \
             patch('app.achievements.service.AchievementService.check_weekly_training_achievements') as mock_check_weekly_training, \
             patch('app.achievements.service.AchievementService.check_consecutive_weeks_achievements') as mock_check_consecutive_weeks, \
             patch('app.achievements.service.AchievementService.check_consecutive_months_achievements') as mock_check_consecutive_months, \
             patch('app.achievements.service.AchievementService.check_year_without_breaks_achievement') as mock_check_year:
            
            # Настройка моков
            mock_check_early_bird.return_value = None
            mock_check_night_owl.return_value = None
            mock_check_new_year.return_value = None
            mock_check_womens_day.return_value = None
            mock_check_mens_day.return_value = None
            mock_check_power_and_strength.return_value = None
            mock_check_training_count.return_value = []
            mock_check_weekly_training.return_value = []
            mock_check_consecutive_weeks.return_value = [mock_achievement]
            mock_check_consecutive_months.return_value = []
            mock_check_year.return_value = None
            
            # Выполнение теста
            result = await AchievementService.check_all_achievements_for_user("test-user-uuid")
            
            # Проверки
            assert len(result) == 1
            assert result[0] == mock_achievement
            mock_check_consecutive_weeks.assert_called_once_with("test-user-uuid")
            mock_check_consecutive_months.assert_called_once_with("test-user-uuid")
            mock_check_year.assert_called_once_with("test-user-uuid")


if __name__ == "__main__":
    pytest.main([__file__])
