import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO

client = TestClient(app)


@pytest.mark.asyncio
async def test_upload_avatar_success():
    """Тест успешной загрузки аватара"""
    # Создаем тестового пользователя
    user_data = {
        "login": "test_user_avatar",
        "email": "test_avatar@example.com",
        "password": "testpass123"
    }
    
    # Регистрируем пользователя
    response = client.post("/auth/register/", json=user_data)
    assert response.status_code == 200
    
    # Получаем токен
    login_response = client.post("/auth/login", json={
        "user_identity": user_data["login"],
        "password": user_data["password"]
    })
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    
    # Создаем тестовый файл
    test_file_content = b"fake image content"
    files = {"file": ("test_avatar.jpg", test_file_content, "image/jpeg")}
    
    # Получаем UUID пользователя из токена (в реальном приложении нужно декодировать токен)
    # Для теста используем фиксированный UUID
    user_uuid = "test-uuid-123"
    
    # Загружаем аватар
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post(
        f"/files/upload/avatar/{user_uuid}",
        files=files,
        headers=headers
    )
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Аватар успешно загружен"
    assert "file" in data
    assert data["file"]["filename"] == "test_avatar.jpg"
    assert data["file"]["mime_type"] == "image/jpeg"


@pytest.mark.asyncio
async def test_upload_avatar_invalid_file_type():
    """Тест загрузки файла неподдерживаемого типа"""
    # Создаем тестового пользователя
    user_data = {
        "login": "test_user_invalid",
        "email": "test_invalid@example.com",
        "password": "testpass123"
    }
    
    # Регистрируем пользователя
    response = client.post("/auth/register/", json=user_data)
    assert response.status_code == 200
    
    # Получаем токен
    login_response = client.post("/auth/login", json={
        "user_identity": user_data["login"],
        "password": user_data["password"]
    })
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    
    # Создаем файл неподдерживаемого типа
    test_file_content = b"fake text content"
    files = {"file": ("test.txt", test_file_content, "text/plain")}
    
    user_uuid = "test-uuid-456"
    
    # Загружаем файл
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post(
        f"/files/upload/avatar/{user_uuid}",
        files=files,
        headers=headers
    )
    
    # Проверяем, что получили ошибку
    assert response.status_code == 400
    assert "Неподдерживаемый тип файла" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_avatar():
    """Тест получения аватара"""
    # Создаем тестового пользователя
    user_data = {
        "login": "test_user_get",
        "email": "test_get@example.com",
        "password": "testpass123"
    }
    
    # Регистрируем пользователя
    response = client.post("/auth/register/", json=user_data)
    assert response.status_code == 200
    
    # Получаем UUID пользователя (в реальном приложении нужно получить из БД)
    user_uuid = "test-uuid-789"
    
    # Пытаемся получить аватар
    response = client.get(f"/files/avatar/{user_uuid}")
    
    # Проверяем, что получили 404 (аватар не найден)
    assert response.status_code == 404
    assert "Аватар не найден" in response.json()["detail"] 