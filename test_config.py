import os
from app.config import get_db_url, settings

def test_config():
    print("⚙️  ТЕСТИРОВАНИЕ КОНФИГУРАЦИИ")
    print("=" * 50)
    
    print("1. Переменные окружения:")
    print(f"   DB_HOST: {os.getenv('DB_HOST', 'НЕ УСТАНОВЛЕНА')}")
    print(f"   DB_PORT: {os.getenv('DB_PORT', 'НЕ УСТАНОВЛЕНА')}")
    print(f"   DB_NAME: {os.getenv('DB_NAME', 'НЕ УСТАНОВЛЕНА')}")
    print(f"   DB_USER: {os.getenv('DB_USER', 'НЕ УСТАНОВЛЕНА')}")
    print(f"   DB_PASSWORD: {os.getenv('DB_PASSWORD', 'НЕ УСТАНОВЛЕНА')}")
    
    print("\n2. Настройки из settings:")
    try:
        print(f"   DB_HOST: {settings.DB_HOST}")
        print(f"   DB_PORT: {settings.DB_PORT}")
        print(f"   DB_NAME: {settings.DB_NAME}")
        print(f"   DB_USER: {settings.DB_USER}")
        print(f"   DB_PASSWORD: {'***' if settings.DB_PASSWORD else 'НЕ УСТАНОВЛЕН'}")
    except Exception as e:
        print(f"   ❌ Ошибка получения настроек: {e}")
    
    print("\n3. URL базы данных:")
    try:
        db_url = get_db_url()
        # Скрываем пароль в URL
        safe_url = db_url.replace(settings.DB_PASSWORD, '***') if settings.DB_PASSWORD else db_url
        print(f"   {safe_url}")
    except Exception as e:
        print(f"   ❌ Ошибка получения URL: {e}")

if __name__ == "__main__":
    test_config()

