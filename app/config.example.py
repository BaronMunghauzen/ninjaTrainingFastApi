"""
Шаблон настроек приложения.

Скопируйте этот файл в app/config.py и заполните значения
(или задайте те же переменные в .env в корне проекта — см. pydantic-settings).

    cp app/config.example.py app/config.py

Файл app/config.py в репозитории не хранится (.gitignore).
"""
import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "your_database"
    DB_USER: str = "your_db_user"
    DB_PASSWORD: str = "your_db_password"
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    ALGORITHM: str = "HS256"
    DEBUG: bool = False

    MAIL_USERNAME: str = "your_email@gmail.com"
    MAIL_PASSWORD: str = "your_app_password"
    MAIL_FROM: str = "your_email@gmail.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    BASE_URL: str = "http://localhost:8000"

    TOCHKA_ACCESS_TOKEN: str = "your_tochka_token"
    TOCHKA_CUSTOMER_CODE: str = "your_customer_code"
    TOCHKA_MERCHANT_ID: Optional[str] = None
    TOCHKA_API_URL: str = "https://enter.tochka.com/uapi"

    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_PROXY_HOST: Optional[str] = None
    TELEGRAM_PROXY_PORT: Optional[int] = None
    TELEGRAM_PROXY_USERNAME: Optional[str] = None
    TELEGRAM_PROXY_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
        env_file_encoding="utf-8",
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
        "isPaymentVisible": True,
        "isPaymentVisibleWorldwide": False,
    },
}
