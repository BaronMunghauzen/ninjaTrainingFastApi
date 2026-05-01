import logging
from typing import Any, Dict, Optional

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

    async def call_raw_api(
        self,
        api_method: str,
        *,
        get_params: Optional[Dict[str, Any]] = None,
        post_json: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0,
    ) -> Optional[dict]:
        """
        Вызов Telegram Bot API (getUpdates, deleteWebhook и т.д.).
        Та же схема прокси, что и у send_message: сначала прокси, при сбое — напрямую.
        """
        if not self.bot_token or not self.api_url:
            logger.debug("Telegram API: нет токена, пропускаем %s", api_method)
            return None

        async def _attempt(proxy_url: Optional[str], label: str) -> Optional[dict]:
            url = f"{self.api_url}/{api_method}"
            try:
                client_kwargs: Dict[str, Any] = {"timeout": timeout}
                if proxy_url:
                    client_kwargs["proxy"] = proxy_url
                async with httpx.AsyncClient(**client_kwargs) as client:
                    if get_params is not None:
                        response = await client.get(url, params=get_params)
                    elif post_json is not None:
                        response = await client.post(url, json=post_json)
                    else:
                        response = await client.post(url)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPError as e:
                logger.exception(
                    "Ошибка HTTP Telegram API %s (%s): %r",
                    api_method,
                    label,
                    e,
                )
                return None
            except Exception as e:
                logger.exception(
                    "Ошибка Telegram API %s (%s): %r",
                    api_method,
                    label,
                    e,
                )
                return None

        if self.proxy_url:
            data = await _attempt(self.proxy_url, "через прокси")
            if data is not None:
                return data
            logger.warning(
                "Telegram API %s через прокси не удался, пробуем напрямую",
                api_method,
            )
            return await _attempt(None, "напрямую")
        return await _attempt(None, "напрямую")
    
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

        if self.proxy_url:
            sent_via_proxy = await self._send_message_request(
                text=text,
                parse_mode=parse_mode,
                proxy_url=self.proxy_url,
                transport_label="через прокси",
            )
            if sent_via_proxy:
                return True

            logger.warning(
                "Отправка Telegram через прокси не удалась, пробуем прямое подключение"
            )
            return await self._send_message_request(
                text=text,
                parse_mode=parse_mode,
                proxy_url=None,
                transport_label="напрямую",
            )

        return await self._send_message_request(
            text=text,
            parse_mode=parse_mode,
            proxy_url=None,
            transport_label="напрямую",
        )

    async def _send_message_request(
        self,
        text: str,
        parse_mode: str,
        proxy_url: Optional[str],
        transport_label: str,
    ) -> bool:
        try:
            client_kwargs = {"timeout": 10.0}
            if proxy_url:
                client_kwargs["proxy"] = proxy_url

            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                    },
                )
                response.raise_for_status()
                result = response.json()

                if result.get("ok"):
                    logger.info(f"Telegram сообщение отправлено успешно ({transport_label})")
                    return True

                logger.error(
                    "Ошибка Telegram API (%s): %s",
                    transport_label,
                    result.get("description"),
                )
                return False
        except httpx.HTTPError as e:
            logger.exception(
                "Ошибка HTTP при отправке Telegram сообщения (%s): %r",
                transport_label,
                e,
            )
            return False
        except Exception as e:
            logger.exception(
                "Неожиданная ошибка при отправке Telegram сообщения (%s): %r",
                transport_label,
                e,
            )
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

