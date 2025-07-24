# Базовые тесты
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_home_page():
    """Тест главной страницы"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Привет!"} 