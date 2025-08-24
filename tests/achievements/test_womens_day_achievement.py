import pytest
from datetime import datetime, time, date
from unittest.mock import AsyncMock, patch
from app.achievements.service import AchievementService
from app.achievements.models import Achievement
from app.user_training.models import UserTraining
from app.users.models import User


class TestWomensDayAchievement:
    """Тесты для достижения 'Международный женский день'"""
    
    @pytest.fixture
    def mock_user(self):
        """Мок пользователя"""
        user = User()
        user.id = 1
        user.uuid = "test-user-uuid"
        return user
    
    @pytest.fixture
    def mock_womens_day_training(self):
        """Мок тренировки 8 марта"""
        training = UserTraining()
        training.id = 1
        training.uuid = "training-uuid-1"
        training.completed_at = datetime(2024, 3, 8, 14, 0, 0)  # 8 марта 2024, 14:00
        training.status = "completed"
        return training
    
    @pytest.fixture
    def mock_achievement(self):
        """Мок достижения"""
        achievement = Achievement()
        achievement.id = 1
        achievement.name = "Международный женский день 2024"
        achievement.user_id = 1
        achievement.status = "active"
        return achievement
    
    @pytest.mark.asyncio
    async def test_check_womens_day_achievement_success(self, mock_user, mock_womens_day_training, mock_achievement):
        """Тест успешного получения достижения 'Международный женский день'"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.async_session_maker') as mock_session_maker:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_training_dao.return_value.find_womens_day_trainings.return_value = [mock_womens_day_training]
            mock_achievement_dao.return_value.create.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_womens_day_achievement("test-user-uuid")
            
            # Проверки
            assert result is not None
            assert result.name == "Международный женский день 2024"
            assert result.status == "active"
            
            # Проверяем, что методы были вызваны
            mock_users_dao.return_value.find_by_uuid.assert_called_once_with("test-user-uuid")
            mock_achievement_dao.return_value.find_by_name_and_user.assert_called_once_with("Международный женский день 2024", 1)
            mock_training_dao.return_value.find_womens_day_trainings.assert_called_once_with(user_id=1, year=2024)
            mock_achievement_dao.return_value.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_womens_day_achievement_specific_year(self, mock_user, mock_womens_day_training, mock_achievement):
        """Тест получения достижения для конкретного года"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.async_session_maker') as mock_session_maker:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_training_dao.return_value.find_womens_day_trainings.return_value = [mock_womens_day_training]
            mock_achievement_dao.return_value.create.return_value = mock_achievement
            
            # Выполнение теста для 2023 года
            result = await AchievementService.check_womens_day_achievement("test-user-uuid", 2023)
            
            # Проверки
            assert result is not None
            assert result.name == "Международный женский день 2023"
            mock_training_dao.return_value.find_womens_day_trainings.assert_called_once_with(user_id=1, year=2023)
    
    @pytest.mark.asyncio
    async def test_check_womens_day_achievement_already_exists(self, mock_user, mock_achievement):
        """Тест, когда достижение уже существует"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_womens_day_achievement("test-user-uuid")
            
            # Проверки
            assert result == mock_achievement
            mock_achievement_dao.return_value.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_womens_day_achievement_no_trainings(self, mock_user):
        """Тест, когда нет тренировок 8 марта"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_training_dao.return_value.find_womens_day_trainings.return_value = []  # Пустой список
            
            # Выполнение теста
            result = await AchievementService.check_womens_day_achievement("test-user-uuid")
            
            # Проверки
            assert result is None
            mock_achievement_dao.return_value.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_womens_day_achievement_user_not_found(self):
        """Тест, когда пользователь не найден"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = None
            
            # Выполнение теста
            result = await AchievementService.check_womens_day_achievement("invalid-user-uuid")
            
            # Проверки
            assert result is None
    
    @pytest.mark.asyncio
    async def test_check_all_achievements_includes_womens_day(self, mock_user, mock_achievement):
        """Тест, что check_all_achievements включает проверку 'Международный женский день'"""
        with patch('app.achievements.service.AchievementService.check_early_bird_achievement') as mock_check_early_bird, \
             patch('app.achievements.service.AchievementService.check_night_owl_achievement') as mock_check_night_owl, \
             patch('app.achievements.service.AchievementService.check_new_year_achievement') as mock_check_new_year, \
             patch('app.achievements.service.AchievementService.check_womens_day_achievement') as mock_check_womens_day:
            
            # Настройка моков
            mock_check_early_bird.return_value = None
            mock_check_night_owl.return_value = None
            mock_check_new_year.return_value = None
            mock_check_womens_day.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_all_achievements_for_user("test-user-uuid")
            
            # Проверки
            assert len(result) == 1
            assert result[0] == mock_achievement
            mock_check_early_bird.assert_called_once_with("test-user-uuid")
            mock_check_night_owl.assert_called_once_with("test-user-uuid")
            mock_check_new_year.assert_called_once_with("test-user-uuid")
            mock_check_womens_day.assert_called_once_with("test-user-uuid")


if __name__ == "__main__":
    pytest.main([__file__])
