import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime
from uuid import uuid4


class TestAchievementAPI:
    """Тесты для API достижений"""
    
    def test_get_achievements_empty(self, client: TestClient):
        """Тест получения пустого списка достижений"""
        response = client.get("/achievements/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_achievement(self, client: TestClient):
        """Тест создания достижения"""
        achievement_data = {
            "name": "Первая тренировка",
            "user_uuid": "test-user-uuid",
            "status": "active",
            "user_training_uuid": "test-training-uuid"
        }
        
        response = client.post("/achievements/", json=achievement_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "uuid" in data
        assert data["name"] == "Первая тренировка"
        assert data["status"] == "active"
    
    def test_get_achievement_by_uuid(self, client: TestClient):
        """Тест получения достижения по UUID"""
        # Сначала создаем достижение
        achievement_data = {
            "name": "Тестовая тренировка",
            "user_uuid": "test-user-uuid",
            "status": "active",
            "user_training_uuid": "test-training-uuid"
        }
        
        create_response = client.post("/achievements/", json=achievement_data)
        assert create_response.status_code == 200
        
        achievement_uuid = create_response.json()["uuid"]
        
        # Теперь получаем его по UUID
        response = client.get(f"/achievements/{achievement_uuid}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["uuid"] == achievement_uuid
        assert data["name"] == "Тестовая тренировка"
    
    def test_update_achievement(self, client: TestClient):
        """Тест обновления достижения"""
        # Сначала создаем достижение
        achievement_data = {
            "name": "Тестовая тренировка",
            "user_uuid": "test-user-uuid",
            "status": "active",
            "user_training_uuid": "test-training-uuid"
        }
        
        create_response = client.post("/achievements/", json=achievement_data)
        assert create_response.status_code == 200
        
        achievement_uuid = create_response.json()["uuid"]
        
        # Обновляем достижение
        update_data = {
            "name": "Обновленная тренировка"
        }
        
        response = client.put(f"/achievements/{achievement_uuid}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Обновленная тренировка"
    
    def test_delete_achievement(self, client: TestClient):
        """Тест удаления достижения"""
        # Сначала создаем достижение
        achievement_data = {
            "name": "Тестовая тренировка",
            "user_uuid": "test-user-uuid",
            "status": "active",
            "user_training_uuid": "test-training-uuid"
        }
        
        create_response = client.post("/achievements/", json=achievement_data)
        assert create_response.status_code == 200
        
        achievement_uuid = create_response.json()["uuid"]
        
        # Удаляем достижение
        response = client.delete(f"/achievements/{achievement_uuid}")
        assert response.status_code == 200
        assert response.json()["message"] == "Достижение успешно удалено"
        
        # Проверяем, что достижение действительно удалено
        get_response = client.get(f"/achievements/{achievement_uuid}")
        assert get_response.status_code == 404
    
    def test_get_achievements_stats(self, client: TestClient):
        """Тест получения статистики по достижениям"""
        response = client.get("/achievements/stats/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_achievements" in data
        assert "completed_achievements" in data
        assert "completion_rate" in data
        assert data["total_achievements"] >= 0
        assert data["completed_achievements"] >= 0
        assert 0 <= data["completion_rate"] <= 100
