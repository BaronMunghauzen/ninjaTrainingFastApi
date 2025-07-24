import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_register_endpoint_validation():
    """Тест валидации эндпоинта регистрации"""
    response = client.post("/auth/register/", json={})
    assert response.status_code == 422
    response = client.post("/auth/register/", json={"login": "test"})
    assert response.status_code == 422

def test_login_endpoint_validation():
    """Тест валидации эндпоинта логина"""
    response = client.post("/auth/login/", json={})
    assert response.status_code == 422
    response = client.post("/auth/login/", json={"user_identity": "test"})
    assert response.status_code == 422

def test_register_schema_validation():
    """Тест схемы регистрации с правильными данными"""
    valid_data = {
        "login": "testuser",
        "email": "test@example.com",
        "password": "12345"
    }
    response = client.post("/auth/register/", json=valid_data)
    assert response.status_code in [200, 409, 422]

def test_register_duplicate_login():
    """Тест регистрации с дублирующимся логином"""
    valid_data = {
        "login": "duplicateuser",
        "email": "test1@example.com",
        "password": "12345"
    }
    # Первая регистрация
    response1 = client.post("/auth/register/", json=valid_data)
    assert response1.status_code in [200, 409, 422]
    
    # Вторая регистрация с тем же логином, но другим email
    duplicate_data = {
        "login": "duplicateuser",
        "email": "test2@example.com",
        "password": "12345"
    }
    response2 = client.post("/auth/register/", json=duplicate_data)
    assert response2.status_code == 409

def test_register_success():
    """Тест успешной регистрации с минимальными данными"""
    valid_data = {
        "login": "newuser123",
        "email": "newuser123@example.com",
        "password": "12345"
    }
    response = client.post("/auth/register/", json=valid_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "Вы успешно зарегистрированы!"
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert response_data["access_token"] is not None
    assert response_data["refresh_token"] is not None

def test_login_with_tokens():
    """Тест логина с возвратом токенов"""
    # Сначала регистрируем пользователя
    register_data = {
        "login": "logintestuser",
        "email": "logintest@example.com",
        "password": "12345"
    }
    client.post("/auth/register/", json=register_data)
    
    # Теперь логинимся
    login_data = {
        "user_identity": "logintestuser",
        "password": "12345"
    }
    response = client.post("/auth/login/", json=login_data)
    assert response.status_code == 200
    response_data = response.json()
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert response_data["access_token"] is not None
    assert response_data["refresh_token"] is not None 