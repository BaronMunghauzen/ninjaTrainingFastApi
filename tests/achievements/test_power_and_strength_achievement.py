import pytest
from datetime import datetime, time, date
from unittest.mock import AsyncMock, patch
from app.achievements.service import AchievementService
from app.achievements.models import Achievement
from app.user_training.models import UserTraining
from app.user_program.models import UserProgram
from app.programs.models import Program
from app.users.models import User


class TestPowerAndStrengthAchievement:
    """Тесты для достижения 'Мощь и сила'"""
    
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
        user_program.status = "completed"
        user_program.program = mock_program
        return user_program
    
    @pytest.fixture
    def mock_completed_training(self):
        """Мок завершенной тренировки"""
        training = UserTraining()
        training.id = 1
        training.uuid = "training-uuid-1"
        training.user_id = 1
        training.user_program_id = 1
        training.status = "completed"
        training.completed_at = datetime(2024, 1, 15, 14, 0, 0)
        return training
    
    @pytest.fixture
    def mock_achievement(self):
        """Мок достижения"""
        achievement = Achievement()
        achievement.id = 1
        achievement.name = "Мощь и сила"
        achievement.user_id = 1
        achievement.status = "active"
        return achievement
    
    @pytest.mark.asyncio
    async def test_check_power_and_strength_achievement_success(self, mock_user, mock_user_program, mock_completed_training, mock_achievement):
        """Тест успешного получения достижения 'Мощь и сила'"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.UserProgramDAO') as mock_user_program_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.async_session_maker') as mock_session_maker:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_user_program_dao.return_value.find_by_user_id.return_value = [mock_user_program]
            mock_training_dao.return_value.find_completed_program_trainings.return_value = [mock_completed_training]
            mock_achievement_dao.return_value.create.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_power_and_strength_achievement("test-user-uuid")
            
            # Проверки
            assert result is not None
            assert result.name == "Мощь и сила"
            assert result.status == "active"
            
            # Проверяем, что методы были вызваны
            mock_users_dao.return_value.find_by_uuid.assert_called_once_with("test-user-uuid")
            mock_achievement_dao.return_value.find_by_name_and_user.assert_called_once_with("Мощь и сила", 1)
            mock_user_program_dao.return_value.find_by_user_id.assert_called_once_with(1)
            mock_training_dao.return_value.find_completed_program_trainings.assert_called_once_with(user_id=1, user_program_id=1)
            mock_achievement_dao.return_value.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_power_and_strength_achievement_already_exists(self, mock_user, mock_achievement):
        """Тест, когда достижение уже существует"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_power_and_strength_achievement("test-user-uuid")
            
            # Проверки
            assert result == mock_achievement
    
    @pytest.mark.asyncio
    async def test_check_power_and_strength_achievement_no_completed_programs(self, mock_user):
        """Тест, когда нет завершенных программ"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.UserProgramDAO') as mock_user_program_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_user_program_dao.return_value.find_by_user_id.return_value = []  # Пустой список программ
            
            # Выполнение теста
            result = await AchievementService.check_power_and_strength_achievement("test-user-uuid")
            
            # Проверки
            assert result is None
    
    @pytest.mark.asyncio
    async def test_check_power_and_strength_achievement_no_completed_trainings(self, mock_user, mock_user_program):
        """Тест, когда нет завершенных тренировок"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.UserProgramDAO') as mock_user_program_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_user_program_dao.return_value.find_by_user_id.return_value = [mock_user_program]
            mock_training_dao.return_value.find_completed_program_trainings.return_value = []  # Пустой список тренировок
            
            # Выполнение теста
            result = await AchievementService.check_power_and_strength_achievement("test-user-uuid")
            
            # Проверки
            assert result is None
    
    @pytest.mark.asyncio
    async def test_check_power_and_strength_achievement_user_not_found(self):
        """Тест, когда пользователь не найден"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = None
            
            # Выполнение теста
            result = await AchievementService.check_power_and_strength_achievement("invalid-user-uuid")
            
            # Проверки
            assert result is None
    
    @pytest.mark.asyncio
    async def test_check_all_achievements_includes_power_and_strength(self, mock_user, mock_achievement):
        """Тест, что check_all_achievements включает проверку 'Мощь и сила'"""
        with patch('app.achievements.service.AchievementService.check_early_bird_achievement') as mock_check_early_bird, \
             patch('app.achievements.service.AchievementService.check_night_owl_achievement') as mock_check_night_owl, \
             patch('app.achievements.service.AchievementService.check_new_year_achievement') as mock_check_new_year, \
             patch('app.achievements.service.AchievementService.check_womens_day_achievement') as mock_check_womens_day, \
             patch('app.achievements.service.AchievementService.check_mens_day_achievement') as mock_check_mens_day, \
             patch('app.achievements.service.AchievementService.check_power_and_strength_achievement') as mock_check_power_and_strength:
            
            # Настройка моков
            mock_check_early_bird.return_value = None
            mock_check_night_owl.return_value = None
            mock_check_new_year.return_value = None
            mock_check_womens_day.return_value = None
            mock_check_mens_day.return_value = None
            mock_check_power_and_strength.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_all_achievements_for_user("test-user-uuid")
            
            # Проверки
            assert len(result) == 1
            assert result[0] == mock_achievement
            mock_check_early_bird.assert_called_once_with("test-user-uuid")
            mock_check_night_owl.assert_called_once_with("test-user-uuid")
            mock_check_new_year.assert_called_once_with("test-user-uuid")
            mock_check_womens_day.assert_called_once_with("test-user-uuid")
            mock_check_mens_day.assert_called_once_with("test-user-uuid")
            mock_check_power_and_strength.assert_called_once_with("test-user-uuid")


if __name__ == "__main__":
    pytest.main([__file__])
