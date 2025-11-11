import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str
    DEBUG: bool = False
    
    # Email настройки (добавляем только их)
    MAIL_USERNAME: str = "your_email@gmail.com"
    MAIL_PASSWORD: str = "your_app_password"
    MAIL_FROM: str = "your_email@gmail.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    BASE_URL: str = "http://localhost:8000"
    
    # Настройки Точка Банк для платежей
    # Все значения настраиваются в .env файле
    # Документация: https://enter.tochka.com/
    TOCHKA_ACCESS_TOKEN: str
    TOCHKA_CUSTOMER_CODE: str
    TOCHKA_MERCHANT_ID: Optional[str] = None
    TOCHKA_API_URL: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
        env_file_encoding='utf-8'
    )


settings = Settings()


def get_db_url():
    return (
        f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )

def get_auth_data():
    return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}


SETTINGS_JSON: Dict[str, Any] = {
    "app": {
        "isPaymentVisible": True
    }
}