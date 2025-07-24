import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.user_exercises.models import ExerciseStatus

client = TestClient(app)


class TestUserExerciseEndpoints:
    """Тесты для эндпоинтов UserExercise"""

    def test_user_exercises_endpoint_protection(self):
        """Тест защиты эндпоинта пользовательских упражнений"""
        response = client.get("/user_exercises/")
        assert response.status_code in [401, 403]

    def test_user_exercises_by_id_protection(self):
        """Тест защиты эндпоинта пользовательского упражнения по ID"""
        response = client.get("/user_exercises/test-uuid")
        assert response.status_code in [401, 403]

    def test_user_exercises_add_protection(self):
        """Тест защиты эндпоинта добавления пользовательского упражнения"""
        response = client.post("/user_exercises/add/", json={})
        assert response.status_code in [401, 403]

    def test_user_exercises_update_protection(self):
        """Тест защиты эндпоинта обновления пользовательского упражнения"""
        response = client.put("/user_exercises/update/test-uuid", json={})
        assert response.status_code in [401, 403]

    def test_user_exercises_delete_protection(self):
        """Тест защиты эндпоинта удаления пользовательского упражнения"""
        response = client.delete("/user_exercises/delete/test-uuid")
        assert response.status_code in [401, 403]

    def test_user_exercises_endpoint_requires_auth(self):
        """Тест что эндпоинт пользовательских упражнений требует аутентификации"""
        response = client.get("/user_exercises/")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_exercise_add_endpoint_requires_auth(self):
        """Тест что эндпоинт добавления пользовательского упражнения требует аутентификации"""
        exercise_data = {
            "program_uuid": "test-program-uuid",
            "training_uuid": "test-training-uuid",
            "user_uuid": "test-user-uuid",
            "exercise_uuid": "test-exercise-uuid",
            "training_date": "2025-01-01",
            "status": ExerciseStatus.ACTIVE.value,
            "set_number": 1,
            "weight": 50.0,
            "reps": 10
        }
        response = client.post("/user_exercises/add/", json=exercise_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_exercise_get_by_uuid_endpoint_requires_auth(self):
        """Тест что эндпоинт получения пользовательского упражнения по UUID требует аутентификации"""
        response = client.get("/user_exercises/test-uuid")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_exercise_update_endpoint_requires_auth(self):
        """Тест что эндпоинт обновления пользовательского упражнения требует аутентификации"""
        update_data = {
            "status": ExerciseStatus.PASSED.value,
            "set_number": 2,
            "weight": 55.0,
            "reps": 12
        }
        response = client.put("/user_exercises/update/test-uuid", json=update_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_exercise_delete_endpoint_requires_auth(self):
        """Тест что эндпоинт удаления пользовательского упражнения требует аутентификации"""
        response = client.delete("/user_exercises/delete/test-uuid")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data 