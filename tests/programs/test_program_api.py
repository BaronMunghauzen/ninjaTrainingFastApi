import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_programs_endpoint_protection():
    """Тест защиты эндпоинта программ"""
    response = client.get("/programs/")
    assert response.status_code in [401, 403]

def test_programs_by_id_protection():
    """Тест защиты эндпоинта программы по ID"""
    response = client.get("/programs/test-uuid")
    assert response.status_code in [401, 403]

def test_programs_add_protection():
    """Тест защиты эндпоинта добавления программы"""
    response = client.post("/programs/add/", json={})
    assert response.status_code in [401, 403]

def test_programs_update_protection():
    """Тест защиты эндпоинта обновления программы"""
    response = client.put("/programs/update/test-uuid", json={})
    assert response.status_code in [401, 403]

def test_programs_delete_protection():
    """Тест защиты эндпоинта удаления программы"""
    response = client.delete("/programs/delete/test-uuid")
    assert response.status_code in [401, 403] 