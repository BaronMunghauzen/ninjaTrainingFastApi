import logging
from typing import Optional
import httpx
from app.config import settings

# Настраиваем логирование
logger = logging.getLogger(__name__)


class TelegramService:
    """Сервис для отправки уведомлений в Telegram"""
    
    def __init__(self):
        self.bot_token: Optional[str] = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.chat_id: Optional[str] = getattr(settings, 'TELEGRAM_CHAT_ID', None)
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        self.proxy_url = self._build_proxy_url()
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram уведомления отключены: не настроены TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID")
        else:
            logger.info("TelegramService инициализирован успешно")
            if self.proxy_url:
                logger.info("Для TelegramService включен HTTP-прокси")

    def _build_proxy_url(self) -> Optional[str]:
        proxy_host: Optional[str] = getattr(settings, "TELEGRAM_PROXY_HOST", None)
        proxy_port: Optional[int] = getattr(settings, "TELEGRAM_PROXY_PORT", None)
        proxy_username: Optional[str] = getattr(settings, "TELEGRAM_PROXY_USERNAME", None)
        proxy_password: Optional[str] = getattr(settings, "TELEGRAM_PROXY_PASSWORD", None)

        if not proxy_host or not proxy_port:
            return None
        if proxy_username and proxy_password:
            return f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
        return f"http://{proxy_host}:{proxy_port}"
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Отправить сообщение в Telegram
        
        Args:
            text: Текст сообщения
            parse_mode: Режим форматирования (HTML или Markdown)
        
        Returns:
            True если сообщение отправлено успешно, False в противном случае
        """
        if not self.bot_token or not self.chat_id:
            logger.debug("Telegram уведомления отключены, пропускаем отправку")
            return False
        
        try:
            client_kwargs = {"timeout": 10.0}
            if self.proxy_url:
                client_kwargs["proxy"] = self.proxy_url

            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": parse_mode
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("ok"):
                    logger.info("Telegram сообщение отправлено успешно")
                    return True
                else:
                    logger.error(f"Ошибка отправки Telegram сообщения: {result.get('description')}")
                    return False
                    
        except httpx.HTTPError as e:
            logger.error(f"Ошибка HTTP при отправке Telegram сообщения: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке Telegram сообщения: {e}")
            return False
    
    async def notify_new_registration(
        self,
        user_email: str,
        user_login: str,
        user_id: int,
        user_uuid: str
    ) -> bool:
        """
        Отправить уведомление о новой регистрации
        
        Args:
            user_email: Email пользователя
            user_login: Логин пользователя
            user_id: ID пользователя
            user_uuid: UUID пользователя
        
        Returns:
            True если уведомление отправлено успешно
        """
        message = (
            "🆕 <b>Новая регистрация!</b>\n\n"
            f"📧 Email: <code>{user_email}</code>\n"
            f"👤 Логин: <code>{user_login}</code>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"🔑 UUID: <code>{user_uuid}</code>"
        )
        
        return await self.send_message(message)
    
    async def notify_payment_success(
        self,
        user_email: str,
        user_login: str,
        payment_uuid: str,
        amount: float,
        plan_name: str,
        subscription_until: str
    ) -> bool:
        """
        Отправить уведомление об успешной оплате
        
        Args:
            user_email: Email пользователя
            user_login: Логин пользователя
            payment_uuid: UUID платежа
            amount: Сумма платежа
            plan_name: Название тарифного плана
            subscription_until: Дата окончания подписки
        
        Returns:
            True если уведомление отправлено успешно
        """
        message = (
            "💳 <b>Успешная оплата!</b>\n\n"
            f"👤 Пользователь: <code>{user_login}</code>\n"
            f"📧 Email: <code>{user_email}</code>\n"
            f"💰 Сумма: <b>{amount:.2f} ₽</b>\n"
            f"📦 План: <b>{plan_name}</b>\n"
            f"📅 Подписка до: <b>{subscription_until}</b>\n"
            f"🔑 Payment UUID: <code>{payment_uuid}</code>"
        )
        
        return await self.send_message(message)


# Создаем экземпляр сервиса
logger.info("Создание экземпляра TelegramService...")
telegram_service = TelegramService()

