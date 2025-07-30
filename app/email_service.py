import os
import logging
from typing import Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config import settings

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        logger.info("Инициализация EmailService...")
        logger.info(f"MAIL_USERNAME: {settings.MAIL_USERNAME}")
        logger.info(f"MAIL_FROM: {settings.MAIL_FROM}")
        logger.info(f"MAIL_SERVER: {settings.MAIL_SERVER}")
        logger.info(f"MAIL_PORT: {settings.MAIL_PORT}")
        
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True
        )
        self.fm = FastMail(self.conf)
        logger.info("EmailService инициализирован успешно")

    async def send_verification_email(self, email: str, token: str, base_url: str = None):
        """Отправить email для подтверждения"""
        logger.info(f"Попытка отправить email подтверждения на: {email}")
        logger.info(f"Токен: {token[:10]}...")
        
        if base_url is None:
            base_url = settings.BASE_URL
        logger.info(f"Base URL: {base_url}")
            
        verification_url = f"{base_url}/auth/verify-email?token={token}"
        logger.info(f"URL подтверждения: {verification_url}")
        
        message = MessageSchema(
            subject="Подтвердите ваш email",
            recipients=[email],
            body=f"""
            <html>
            <body>
                <h1>Добро пожаловать в Ninja Training!</h1>
                <p>Для подтверждения вашего email перейдите по ссылке ниже:</p>
                <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Подтвердить email</a></p>
                <p>Или скопируйте эту ссылку в браузер:</p>
                <p>{verification_url}</p>
                <p>Ссылка действительна в течение 24 часов.</p>
                <p>Если вы не регистрировались в нашем сервисе, просто проигнорируйте это письмо.</p>
            </body>
            </html>
            """,
            subtype="html"
        )
        
        try:
            logger.info("Отправка email...")
            await self.fm.send_message(message)
            logger.info(f"Email успешно отправлен на {email}")
        except Exception as e:
            logger.error(f"Ошибка отправки email на {email}: {str(e)}")
            logger.error(f"Тип ошибки: {type(e).__name__}")
            raise e

    async def send_password_reset_email(self, email: str, token: str, base_url: str = None):
        """Отправить email для сброса пароля"""
        logger.info(f"Попытка отправить email сброса пароля на: {email}")
        
        if base_url is None:
            base_url = settings.BASE_URL
            
        reset_url = f"{base_url}/auth/reset-password?token={token}"
        
        message = MessageSchema(
            subject="Сброс пароля",
            recipients=[email],
            body=f"""
            <html>
            <body>
                <h1>Сброс пароля</h1>
                <p>Для сброса пароля перейдите по ссылке ниже:</p>
                <p><a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Сбросить пароль</a></p>
                <p>Или скопируйте эту ссылку в браузер:</p>
                <p>{reset_url}</p>
                <p>Ссылка действительна в течение 1 часа.</p>
                <p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
            </body>
            </html>
            """,
            subtype="html"
        )
        
        try:
            logger.info("Отправка email сброса пароля...")
            await self.fm.send_message(message)
            logger.info(f"Email сброса пароля успешно отправлен на {email}")
        except Exception as e:
            logger.error(f"Ошибка отправки email сброса пароля на {email}: {str(e)}")
            raise e


# Создаем экземпляр сервиса
logger.info("Создание экземпляра EmailService...")
email_service = EmailService() 