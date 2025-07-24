import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestExerciseEndpoints:
    """Тесты для эндпоинтов упражнений"""

    def test_exercises_endpoint_exists(self):
        """Тест что эндпоинт упражнений существует"""
        client = TestClient(app)
        response = client.get("/exercises/")
        # Должен вернуть 401 (Unauthorized), а не 404 (Not Found)
        assert response.status_code == 401

    def test_exercise_add_endpoint_exists(self):
        """Тест что эндпоинт добавления упражнения существует"""
        client = TestClient(app)
        response = client.post("/exercises/add/", json={})
        # Должен вернуть 401 (Unauthorized), а не 404 (Not Found)
        assert response.status_code == 401

    def test_exercise_get_by_uuid_endpoint_exists(self):
        """Тест что эндпоинт получения упражнения по UUID существует"""
        client = TestClient(app)
        response = client.get("/exercises/test-uuid")
        # Должен вернуть 401 (Unauthorized), а не 404 (Not Found)
        assert response.status_code == 401

    def test_exercise_update_endpoint_exists(self):
        """Тест что эндпоинт обновления упражнения существует"""
        client = TestClient(app)
        response = client.put("/exercises/update/test-uuid", json={})
        # Должен вернуть 401 (Unauthorized), а не 404 (Not Found)
        assert response.status_code == 401

    def test_exercise_delete_endpoint_exists(self):
        """Тест что эндпоинт удаления упражнения существует"""
        client = TestClient(app)
        response = client.delete("/exercises/delete/test-uuid")
        # Должен вернуть 401 (Unauthorized), а не 404 (Not Found)
        assert response.status_code == 401

    def test_exercises_endpoint_requires_auth(self):
        """Тест что эндпоинт упражнений требует аутентификации"""
        client = TestClient(app)
        response = client.get("/exercises/")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_exercise_add_endpoint_requires_auth(self):
        """Тест что эндпоинт добавления упражнения требует аутентификации"""
        exercise_data = {
            "exercise_type": "strength",
            "caption": "Test Exercise",
            "difficulty_level": 5,
            "order": 1,
            "muscle_group": "chest"
        }
        client = TestClient(app)
        response = client.post("/exercises/add/", json=exercise_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_exercise_get_by_uuid_endpoint_requires_auth(self):
        """Тест что эндпоинт получения упражнения по UUID требует аутентификации"""
        client = TestClient(app)
        response = client.get("/exercises/test-uuid")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_exercise_update_endpoint_requires_auth(self):
        """Тест что эндпоинт обновления упражнения требует аутентификации"""
        update_data = {
            "caption": "Updated Exercise"
        }
        client = TestClient(app)
        response = client.put("/exercises/update/test-uuid", json=update_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_exercise_delete_endpoint_requires_auth(self):
        """Тест что эндпоинт удаления упражнения требует аутентификации"""
        client = TestClient(app)
        response = client.delete("/exercises/delete/test-uuid")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data 