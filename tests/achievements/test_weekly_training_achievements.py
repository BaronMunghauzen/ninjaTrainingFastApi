import pytest
from datetime import datetime, time, date, timedelta
from unittest.mock import AsyncMock, patch
from app.achievements.service import AchievementService
from app.achievements.models import Achievement
from app.user_training.models import UserTraining
from app.user_program.models import UserProgram
from app.programs.models import Program
from app.users.models import User


class TestWeeklyTrainingAchievements:
    """Тесты для достижений за количество тренировок в неделю"""
    
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
        achievement.name = "5 раза в неделю"
        achievement.user_id = 1
        achievement.status = "active"
        return achievement
    
    @pytest.fixture
    def sample_week_start(self):
        """Пример начала недели (понедельник)"""
        return date(2024, 1, 8)  # Понедельник
    
    @pytest.mark.asyncio
    async def test_check_weekly_training_achievements_success(self, mock_user, mock_last_training, mock_achievement):
        """Тест успешного получения достижений за количество тренировок в неделю"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.async_session_maker') as mock_session_maker:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_training_dao.return_value.find_weekly_training_achievements.side_effect = [
                [date(2024, 1, 8)],  # 3 раза в неделю
                [date(2024, 1, 8)],  # 4 раза в неделю
                [date(2024, 1, 8)],  # 5 раза в неделю
                [],  # 6 раза в неделю - нет
                []   # 7 раза в неделю - нет
            ]
            mock_training_dao.return_value.find_last_completed_training.return_value = mock_last_training
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_achievement_dao.return_value.create.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_weekly_training_achievements("test-user-uuid")
            
            # Проверки
            assert len(result) == 3  # 3, 4, 5 раза в неделю
            assert result[0].name == "3 раза в неделю"
            assert result[1].name == "4 раза в неделю"
            assert result[2].name == "5 раза в неделю"
            
            # Проверяем, что методы были вызваны
            mock_users_dao.return_value.find_by_uuid.assert_called_once_with("test-user-uuid")
            assert mock_training_dao.return_value.find_weekly_training_achievements.call_count == 5
    
    @pytest.mark.asyncio
    async def test_check_weekly_training_achievements_no_new_achievements(self, mock_user):
        """Тест, когда нет новых достижений за количество тренировок в неделю"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_training_dao.return_value.find_weekly_training_achievements.return_value = []  # Нет недель с достаточным количеством
            
            # Выполнение теста
            result = await AchievementService.check_weekly_training_achievements("test-user-uuid")
            
            # Проверки
            assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_check_weekly_training_achievements_already_exists(self, mock_user, mock_last_training):
        """Тест, когда достижения уже существуют"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_training_dao.return_value.find_weekly_training_achievements.return_value = [date(2024, 1, 8)]
            mock_training_dao.return_value.find_last_completed_training.return_value = mock_last_training
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = mock_achievement  # Уже существует
            
            # Выполнение теста
            result = await AchievementService.check_weekly_training_achievements("test-user-uuid")
            
            # Проверки
            assert len(result) == 0  # Новых достижений нет
    
    @pytest.mark.asyncio
    async def test_check_weekly_training_achievements_user_not_found(self):
        """Тест, когда пользователь не найден"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = None
            
            # Выполнение теста
            result = await AchievementService.check_weekly_training_achievements("invalid-user-uuid")
            
            # Проверки
            assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_check_weekly_training_achievements_all_milestones(self, mock_user, mock_last_training, mock_achievement):
        """Тест для всех вех (3, 4, 5, 6, 7 тренировок в неделю)"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.async_session_maker') as mock_session_maker:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_training_dao.return_value.find_weekly_training_achievements.return_value = [date(2024, 1, 8)]  # Все вехи достигнуты
            mock_training_dao.return_value.find_last_completed_training.return_value = mock_last_training
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_achievement_dao.return_value.create.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_weekly_training_achievements("test-user-uuid")
            
            # Проверки
            assert len(result) == 5  # Все 5 достижений
            achievement_names = [ach.name for ach in result]
            expected_names = [
                "3 раза в неделю", "4 раза в неделю", "5 раза в неделю",
                "6 раза в неделю", "7 раза в неделю"
            ]
            assert achievement_names == expected_names
    
    @pytest.mark.asyncio
    async def test_check_all_achievements_includes_weekly_training(self, mock_user, mock_achievement):
        """Тест, что check_all_achievements включает проверку достижений за количество тренировок в неделю"""
        with patch('app.achievements.service.AchievementService.check_early_bird_achievement') as mock_check_early_bird, \
             patch('app.achievements.service.AchievementService.check_night_owl_achievement') as mock_check_night_owl, \
             patch('app.achievements.service.AchievementService.check_new_year_achievement') as mock_check_new_year, \
             patch('app.achievements.service.AchievementService.check_womens_day_achievement') as mock_check_womens_day, \
             patch('app.achievements.service.AchievementService.check_mens_day_achievement') as mock_check_mens_day, \
             patch('app.achievements.service.AchievementService.check_power_and_strength_achievement') as mock_check_power_and_strength, \
             patch('app.achievements.service.AchievementService.check_training_count_achievements') as mock_check_training_count, \
             patch('app.achievements.service.AchievementService.check_weekly_training_achievements') as mock_check_weekly_training:
            
            # Настройка моков
            mock_check_early_bird.return_value = None
            mock_check_night_owl.return_value = None
            mock_check_new_year.return_value = None
            mock_check_womens_day.return_value = None
            mock_check_mens_day.return_value = None
            mock_check_power_and_strength.return_value = None
            mock_check_training_count.return_value = []
            mock_check_weekly_training.return_value = [mock_achievement]
            
            # Выполнение теста
            result = await AchievementService.check_all_achievements_for_user("test-user-uuid")
            
            # Проверки
            assert len(result) == 1
            assert result[0] == mock_achievement
            mock_check_weekly_training.assert_called_once_with("test-user-uuid")


if __name__ == "__main__":
    pytest.main([__file__])
