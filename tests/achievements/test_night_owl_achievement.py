import pytest
from datetime import datetime, time, date
from unittest.mock import AsyncMock, patch
from app.achievements.service import AchievementService
from app.achievements.models import Achievement
from app.user_training.models import UserTraining
from app.users.models import User


class TestNightOwlAchievement:
    """Тесты для достижения 'Сова'"""
    
    @pytest.fixture
    def mock_user(self):
        """Мок пользователя"""
        user = User()
        user.id = 1
        user.uuid = "test-user-uuid"
        return user
    
    @pytest.fixture
    def mock_late_night_trainings(self):
        """Мок тренировок с 21 до 00"""
        trainings = []
        for i in range(5):
            training = UserTraining()
            training.id = i + 1
            training.uuid = f"training-uuid-{i}"
            training.completed_at = datetime(2024, 1, 1, 21 + (i % 3), 0, 0)  # 21:00, 22:00, 23:00
            training.status = "completed"
            trainings.append(training)
        return trainings
    
    @pytest.fixture
    def mock_achievement(self):
        """Мок достижения"""
        achievement = Achievement()
        achievement.id = 1
        achievement.name = "Сова"
        achievement.user_id = 1
        achievement.status = "active"
        return achievement
    
    @pytest.mark.asyncio
    async def test_check_night_owl_achievement_success(self, mock_user, mock_late_night_trainings, mock_achievement):
        """Тест успешного получения достижения 'Сова'"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao, \
             patch('app.achievements.service.async_session_maker') as mock_session_maker:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_training_dao.return_value.find_late_night_completed_trainings.return_value = mock_late_night_trainings
            mock_achievement_dao.return_value.create.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_night_owl_achievement("test-user-uuid")
            
            # Проверки
            assert result is not None
            assert result.name == "Сова"
            assert result.status == "active"
            
            # Проверяем, что методы были вызваны
            mock_users_dao.return_value.find_by_uuid.assert_called_once_with("test-user-uuid")
            mock_achievement_dao.return_value.find_by_name_and_user.assert_called_once_with("Сова", 1)
            mock_training_dao.return_value.find_late_night_completed_trainings.assert_called_once_with(user_id=1, min_count=5)
            mock_achievement_dao.return_value.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_night_owl_achievement_already_exists(self, mock_user, mock_achievement):
        """Тест, когда достижение уже существует"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_night_owl_achievement("test-user-uuid")
            
            # Проверки
            assert result == mock_achievement
            mock_achievement_dao.return_value.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_night_owl_achievement_not_enough_trainings(self, mock_user):
        """Тест, когда недостаточно тренировок для получения достижения"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao, \
             patch('app.achievements.service.AchievementDAO') as mock_achievement_dao, \
             patch('app.achievements.service.UserTrainingDAO') as mock_training_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = mock_user
            mock_achievement_dao.return_value.find_by_name_and_user.return_value = None
            mock_training_dao.return_value.find_late_night_completed_trainings.return_value = []  # Пустой список
            
            # Выполнение теста
            result = await AchievementService.check_night_owl_achievement("test-user-uuid")
            
            # Проверки
            assert result is None
            mock_achievement_dao.return_value.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_night_owl_achievement_user_not_found(self):
        """Тест, когда пользователь не найден"""
        with patch('app.achievements.service.UsersDAO') as mock_users_dao:
            
            # Настройка моков
            mock_users_dao.return_value.find_by_uuid.return_value = None
            
            # Выполнение теста
            result = await AchievementService.check_night_owl_achievement("invalid-user-uuid")
            
            # Проверки
            assert result is None
    
    @pytest.mark.asyncio
    async def test_check_all_achievements_includes_night_owl(self, mock_user, mock_achievement):
        """Тест, что check_all_achievements включает проверку 'Сова'"""
        with patch('app.achievements.service.AchievementService.check_early_bird_achievement') as mock_check_early_bird, \
             patch('app.achievements.service.AchievementService.check_night_owl_achievement') as mock_check_night_owl:
            
            # Настройка моков
            mock_check_early_bird.return_value = None
            mock_check_night_owl.return_value = mock_achievement
            
            # Выполнение теста
            result = await AchievementService.check_all_achievements_for_user("test-user-uuid")
            
            # Проверки
            assert len(result) == 1
            assert result[0] == mock_achievement
            mock_check_early_bird.assert_called_once_with("test-user-uuid")
            mock_check_night_owl.assert_called_once_with("test-user-uuid")


if __name__ == "__main__":
    pytest.main([__file__])
