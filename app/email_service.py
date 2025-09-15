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

    async def send_password_reset_code(self, email: str, code: str, base_url: str = None):
        """Отправить email с кодом для сброса пароля"""
        logger.info(f"Попытка отправить email с кодом сброса пароля на: {email}")
        
        message = MessageSchema(
            subject="Код для сброса пароля",
            recipients=[email],
            body=f"""
            <html>
            <body>
                <h1>Сброс пароля</h1>
                <p>Ваш код для сброса пароля:</p>
                <div style="background-color: #f4f4f4; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
                    <h2 style="color: #333; font-size: 32px; letter-spacing: 5px; margin: 0;">{code}</h2>
                </div>
                <p>Введите этот код в приложении для сброса пароля.</p>
                <p>Код действителен в течение 10 минут.</p>
                <p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
            </body>
            </html>
            """,
            subtype="html"
        )
        
        try:
            logger.info("Отправка email с кодом сброса пароля...")
            await self.fm.send_message(message)
            logger.info(f"Email с кодом сброса пароля успешно отправлен на {email}")
        except Exception as e:
            logger.error(f"Ошибка отправки email с кодом сброса пароля на {email}: {str(e)}")
            raise e

    async def send_support_request(self, user_email: str, user_name: str, request_type: str, message: str):
        """Отправить email с обращением пользователя в службу поддержки"""
        logger.info(f"Попытка отправить обращение от пользователя {user_email}")
        
        # Отправляем письмо на свой же адрес (MAIL_FROM)
        message_content = MessageSchema(
            subject="Новое обращение от пользователя NinjaTraining",
            recipients=[settings.MAIL_FROM],
            body=f"""
            <html>
            <body>
                <h1>Новое обращение от пользователя NinjaTraining</h1>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h2>Информация о пользователе:</h2>
                    <p><strong>Email:</strong> {user_email}</p>
                    <p><strong>Имя:</strong> {user_name}</p>
                </div>
                <div style="background-color: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h2>Детали обращения:</h2>
                    <p><strong>Тип обращения:</strong> {request_type}</p>
                    <p><strong>Сообщение:</strong></p>
                    <div style="background-color: white; padding: 15px; border-left: 4px solid #007bff; margin: 10px 0;">
                        {message.replace(chr(10), '<br>')}
                    </div>
                </div>
                <p style="color: #6c757d; font-size: 12px; margin-top: 30px;">
                    Это письмо было отправлено автоматически через форму обратной связи NinjaTraining.
                </p>
            </body>
            </html>
            """,
            subtype="html"
        )
        
        try:
            logger.info("Отправка обращения в службу поддержки...")
            await self.fm.send_message(message_content)
            logger.info(f"Обращение успешно отправлено от пользователя {user_email}")
        except Exception as e:
            logger.error(f"Ошибка отправки обращения от пользователя {user_email}: {str(e)}")
            raise e


# Создаем экземпляр сервиса
logger.info("Создание экземпляра EmailService...")
email_service = EmailService() 