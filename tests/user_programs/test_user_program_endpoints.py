import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestUserProgramEndpoints:
    """Тесты для эндпоинтов пользовательских программ"""

    def test_user_programs_endpoint_exists(self):
        """Тест что эндпоинт пользовательских программ существует"""
        client = TestClient(app)
        response = client.get("/user_programs/")
        # Должен вернуть 401 (Unauthorized), а не 404 (Not Found)
        assert response.status_code == 401

    def test_user_program_add_endpoint_exists(self):
        """Тест что эндпоинт добавления пользовательской программы существует"""
        client = TestClient(app)
        response = client.post("/user_programs/add/", json={})
        # Должен вернуть 401 (Unauthorized), а не 404 (Not Found)
        assert response.status_code == 401

    def test_user_program_get_by_uuid_endpoint_exists(self):
        """Тест что эндпоинт получения пользовательской программы по UUID существует"""
        client = TestClient(app)
        response = client.get("/user_programs/test-uuid")
        # Должен вернуть 401 (Unauthorized), а не 404 (Not Found)
        assert response.status_code == 401

    def test_user_program_update_endpoint_exists(self):
        """Тест что эндпоинт обновления пользовательской программы существует"""
        client = TestClient(app)
        response = client.put("/user_programs/update/test-uuid", json={})
        # Должен вернуть 401 (Unauthorized), а не 404 (Not Found)
        assert response.status_code == 401

    def test_user_program_delete_endpoint_exists(self):
        """Тест что эндпоинт удаления пользовательской программы существует"""
        client = TestClient(app)
        response = client.delete("/user_programs/delete/test-uuid")
        # Должен вернуть 401 (Unauthorized), а не 404 (Not Found)
        assert response.status_code == 401

    def test_user_programs_endpoint_requires_auth(self):
        """Тест что эндпоинт пользовательских программ требует аутентификации"""
        client = TestClient(app)
        response = client.get("/user_programs/")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_program_add_endpoint_requires_auth(self):
        """Тест что эндпоинт добавления пользовательской программы требует аутентификации"""
        user_program_data = {
            "program_uuid": "test-program-uuid",
            "user_uuid": "test-user-uuid",
            "caption": "Test User Program",
            "status": "not_active",
            "stage": 1
        }
        client = TestClient(app)
        response = client.post("/user_programs/add/", json=user_program_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_program_add_with_schedule_requires_auth(self):
        """Тест что эндпоинт добавления пользовательской программы с расписанием требует аутентификации"""
        user_program_data = {
            "program_uuid": "test-program-uuid",
            "user_uuid": "test-user-uuid",
            "caption": "Test User Program",
            "status": "not_active",
            "stage": 1,
            "generate_schedule": True,
            "training_days": [1, 3, 5],
            "weeks_ahead": 1
        }
        client = TestClient(app)
        response = client.post("/user_programs/add/", json=user_program_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_program_get_by_uuid_endpoint_requires_auth(self):
        """Тест что эндпоинт получения пользовательской программы по UUID требует аутентификации"""
        client = TestClient(app)
        response = client.get("/user_programs/test-uuid")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_program_update_endpoint_requires_auth(self):
        """Тест что эндпоинт обновления пользовательской программы требует аутентификации"""
        update_data = {
            "caption": "Updated User Program"
        }
        client = TestClient(app)
        response = client.put("/user_programs/update/test-uuid", json=update_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_program_update_with_schedule_requires_auth(self):
        """Тест что эндпоинт обновления пользовательской программы с расписанием требует аутентификации"""
        update_data = {
            "caption": "Updated User Program",
            "training_days": [2, 4, 6],
            "schedule_type": "weekly"
        }
        client = TestClient(app)
        response = client.put("/user_programs/update/test-uuid", json=update_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_user_program_delete_endpoint_requires_auth(self):
        """Тест что эндпоинт удаления пользовательской программы требует аутентификации"""
        client = TestClient(app)
        response = client.delete("/user_programs/delete/test-uuid")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data 