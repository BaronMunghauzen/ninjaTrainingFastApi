import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_trainings_endpoint_protection():
    """Тест защиты эндпоинта тренировок"""
    response = client.get("/trainings/")
    assert response.status_code in [401, 403]

def test_trainings_by_id_protection():
    """Тест защиты эндпоинта тренировки по ID"""
    response = client.get("/trainings/test-uuid")
    assert response.status_code in [401, 403]

def test_trainings_add_protection():
    """Тест защиты эндпоинта добавления тренировки"""
    response = client.post("/trainings/add/", json={})
    assert response.status_code in [401, 403]

def test_trainings_update_protection():
    """Тест защиты эндпоинта обновления тренировки"""
    response = client.put("/trainings/update/test-uuid", json={})
    assert response.status_code in [401, 403]

def test_trainings_delete_protection():
    """Тест защиты эндпоинта удаления тренировки"""
    response = client.delete("/trainings/delete/test-uuid")
    assert response.status_code in [401, 403] 