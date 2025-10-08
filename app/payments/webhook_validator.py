"""
Валидация и расшифровка вебхуков от Точки
Документация: https://developers.tochka.com/docs/tochka-api/opisanie-metodov/vebhuki
"""

from jose import jwt, JWTError
import logging

logger = logging.getLogger(__name__)

# Публичный ключ Точки для проверки подписи вебхуков
# Источник: https://enter.tochka.com/doc/openapi/static/keys/public
TOCHKA_PUBLIC_KEY = {
    "kty": "RSA",
    "e": "AQAB",
    "n": "rwm77av7GIttq-JF1itEgLCGEZW_zz16RlUQVYlLbJtyRSu61fCec_rroP6PxjXU2uLzUOaGaLgAPeUZAJrGuVp9nryKgbZceHckdHDYgJd9TsdJ1MYUsXaOb9joN9vmsCscBx1lwSlFQyNQsHUsrjuDk-opf6RCuazRQ9gkoDCX70HV8WBMFoVm-YWQKJHZEaIQxg_DU4gMFyKRkDGKsYKA0POL-UgWA1qkg6nHY5BOMKaqxbc5ky87muWB5nNk4mfmsckyFv9j1gBiXLKekA_y4UwG2o1pbOLpJS3bP_c95rm4M9ZBmGXqfOQhbjz8z-s9C11i-jmOQ2ByohS-ST3E5sqBzIsxxrxyQDTw--bZNhzpbciyYW4GfkkqyeYoOPd_84jPTBDKQXssvj8ZOj2XboS77tvEO1n1WlwUzh8HPCJod5_fEgSXuozpJtOggXBv0C2ps7yXlDZf-7Jar0UYc_NJEHJF-xShlqd6Q3sVL02PhSCM-ibn9DN9BKmD"
}


def decode_webhook_jwt(jwt_token: str) -> dict:
    """
    Расшифровка и проверка JWT токена от вебхука Точки
    
    Args:
        jwt_token: JWT токен в виде строки
    
    Returns:
        Расшифрованные данные вебхука
    
    Raises:
        JWTError: Если токен невалиден или подпись неверна
    """
    try:
        # Расшифровываем JWT с проверкой подписи
        # Используем публичный ключ Точки и алгоритм RS256
        decoded = jwt.decode(
            jwt_token,
            TOCHKA_PUBLIC_KEY,
            algorithms=['RS256'],
            options={
                'verify_signature': True,  # Проверяем подпись
                'verify_exp': False,       # Не проверяем срок действия
                'verify_aud': False        # Не проверяем аудиторию
            }
        )
        
        logger.info("✓ JWT вебхука успешно расшифрован и подпись проверена")
        return decoded
        
    except JWTError as e:
        logger.error(f"✗ Ошибка расшифровки JWT вебхука: {e}")
        raise
