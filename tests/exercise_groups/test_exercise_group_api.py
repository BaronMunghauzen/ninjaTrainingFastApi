import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_exercise_groups_endpoint_protection():
    """Тест защиты эндпоинта групп упражнений"""
    response = client.get("/exercise-groups/")
    assert response.status_code in [401, 403]

def test_exercise_groups_by_id_protection():
    """Тест защиты эндпоинта группы упражнений по ID"""
    response = client.get("/exercise-groups/test-uuid")
    assert response.status_code in [401, 403]

def test_exercise_groups_add_protection():
    """Тест защиты эндпоинта добавления группы упражнений"""
    response = client.post("/exercise-groups/add/", json={})
    assert response.status_code in [401, 403]

def test_exercise_groups_update_protection():
    """Тест защиты эндпоинта обновления группы упражнений"""
    response = client.put("/exercise-groups/update/test-uuid", json={})
    assert response.status_code in [401, 403]

def test_exercise_groups_delete_protection():
    """Тест защиты эндпоинта удаления группы упражнений"""
    response = client.delete("/exercise-groups/delete/test-uuid")
    assert response.status_code in [401, 403] 