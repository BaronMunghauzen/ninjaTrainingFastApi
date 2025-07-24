import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.user_training.models import TrainingStatus

client = TestClient(app)


class TestUserTrainingEndpoints:
    """Тесты для эндпоинтов UserTraining"""

    def test_user_trainings_endpoint_protection(self):
        """Тест защиты эндпоинта пользовательских тренировок"""
        response = client.get("/user_trainings/")
        assert response.status_code in [401, 403]

    def test_user_trainings_by_id_protection(self):
        """Тест защиты эндпоинта пользовательской тренировки по ID"""
        response = client.get("/user_trainings/test-uuid")
        assert response.status_code in [401, 403]

    def test_user_trainings_add_protection(self):
        """Тест защиты эндпоинта добавления пользовательской тренировки"""
        response = client.post("/user_trainings/add/", json={})
        assert response.status_code in [401, 403]

    def test_user_trainings_update_protection(self):
        """Тест защиты эндпоинта обновления пользовательской тренировки"""
        response = client.put("/user_trainings/update/test-uuid", json={})
        assert response.status_code in [401, 403]

    def test_user_trainings_delete_protection(self):
        """Тест защиты эндпоинта удаления пользовательской тренировки"""
        response = client.delete("/user_trainings/delete/test-uuid")
        assert response.status_code in [401, 403]

    def test_user_trainings_endpoint_requires_auth(self):
        """Тест что эндпоинт пользовательских тренировок требует аутентификации"""
        response = client.get("/user_trainings/")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_training_add_endpoint_requires_auth(self):
        """Тест что эндпоинт добавления пользовательской тренировки требует аутентификации"""
        training_data = {
            "user_program_uuid": "test-user-program-uuid",
            "program_uuid": "test-program-uuid",
            "training_uuid": "test-training-uuid",
            "user_uuid": "test-user-uuid",
            "training_date": "2025-01-01",
            "status": TrainingStatus.ACTIVE.value
        }
        response = client.post("/user_trainings/add/", json=training_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_training_get_by_uuid_endpoint_requires_auth(self):
        """Тест что эндпоинт получения пользовательской тренировки по UUID требует аутентификации"""
        response = client.get("/user_trainings/test-uuid")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_training_update_endpoint_requires_auth(self):
        """Тест что эндпоинт обновления пользовательской тренировки требует аутентификации"""
        update_data = {
            "status": TrainingStatus.PASSED.value
        }
        response = client.put("/user_trainings/update/test-uuid", json=update_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_training_delete_endpoint_requires_auth(self):
        """Тест что эндпоинт удаления пользовательской тренировки требует аутентификации"""
        response = client.delete("/user_trainings/delete/test-uuid")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data 