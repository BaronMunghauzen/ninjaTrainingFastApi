import os
from typing import Optional
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
    # Получите JWT-токен в личном кабинете Точки: https://enter.tochka.com/
    TOCHKA_ACCESS_TOKEN: str = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIyODE5MDlhMTlhNzZiYWNlZDM2ZjAyYTE3OWVhNDZlNSIsInN1YiI6ImQzNjJjZDhiLWVhMTUtNDE1Ny05NDI5LWFkYmVjMzRhYTk4NyIsImN1c3RvbWVyX2NvZGUiOiIzMDUzMDI3NDYifQ.UC317SCbmSNJRLC7JjuxDtRieizQ1NhuJCFPapmm1J6c5G_Ky9VTXiSAZ1zn5ffupiB98xF4N01_jqO1mJzIGET3DV-FGHAxUoJ2766ZciJOsPOSNu5gd_xyvhYdKvKSSh3MKZElJt5CFLRmw-CSCIYS6UAgdnJbKwYnjHh2nh-9IcOLfw8s_h-NmfxV1ErEwgHMgQ7aPw9sSzL5gFFDtxPjmbDJR78NCz2QVYwodO3j46fOIN_BlD_GLlCgOlEtoVD9kVuIxoGpKKv17eAoU4P31_11U6Buq_1y-Sos2olNWQAlFmQwHU8d9751nl_7BmqkNNG8kAWYDK1Owcxdpk8ga9mcxC3vq4leKUWgsTlZMZVkFJctUitividtKtXhPvoUal_8wdVrhB608M95R4hKJwJEU8YYxhKJOoGRiVIIL3Xh86vefkeyFgZkGQmK7oXtZf6Q1_EuCB-rdg4oKTRAEGkUfJKY0aj4yRP2LhP188VK77oOLOclb_rS76hv"  # JWT-токен для авторизации
    # TOCHKA_ACCESS_TOKEN: str = "sandbox.jwt.token"  # JWT-токен для авторизации SANDBOX (тестовый)
  
    # Код клиента - раскомментируйте нужный вариант:
    TOCHKA_CUSTOMER_CODE: str = "305015065"  # PROD (боевой код клиента)
    # TOCHKA_CUSTOMER_CODE: str = "1234567ab"  # SANDBOX (тестовый код клиента)
    
    # ID торговой точки - раскомментируйте нужный вариант:
    TOCHKA_MERCHANT_ID: Optional[str] = None  # PROD (не передавать merchantId)
    # TOCHKA_MERCHANT_ID: Optional[str] = "123456789012345"  # SANDBOX (тестовый ID, 15 символов)
    
    # URL API - раскомментируйте нужный вариант:
    TOCHKA_API_URL: str = "https://enter.tochka.com/uapi"  # PROD (боевой)
    # TOCHKA_API_URL: str = "https://enter.tochka.com/sandbox/v2"  # SANDBOX (тестовый)

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