"""
Сервис для работы с API Точка Банка
Документация: https://developers.tochka.com/docs/tochka-api/
"""

import httpx
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class TochkaPaymentService:
    """Сервис для работы с API Точки через платёжные ссылки"""
    
    def __init__(self):
        self.base_url = settings.TOCHKA_API_URL
        self.access_token = settings.TOCHKA_ACCESS_TOKEN
        self.api_version = "v1.0"  # Версия API
        
    def _get_headers(self) -> dict:
        """Получить заголовки для запроса"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def create_payment_link(
        self,
        amount: float,
        description: str,
        user_id: int,
        user_uuid: str,
        user_email: str,
        payment_uuid: str,
        return_url: str,
        payment_mode: list,
        user_phone: Optional[str] = None
    ) -> dict:
        """
        Создание платёжной ссылки через API Точки
        
        Документация: https://developers.tochka.com/docs/tochka-api/api/create-payment-operation-acquiring-api-version-payments-post
        
        Args:
            amount: Сумма платежа в рублях
            description: Описание платежа (название тарифа)
            user_id: ID пользователя (для customerCode)
            user_uuid: UUID пользователя (для consumerId)
            user_email: Email пользователя
            payment_uuid: UUID платежа из нашей БД
            return_url: URL для возврата после оплаты
            payment_mode: Способы оплаты ['card', 'sbp', 'tinkoff', 'dolyame']
            user_phone: Телефон пользователя (опционально)
        
        Returns:
            {
                'payment_link_id': 'xxx',
                'payment_url': 'https://...',
                'status': 'new'
            }
        
        Raises:
            Exception: При ошибке создания платёжной ссылки
        """
        
        # Используем константный customerCode из конфига (код клиента в системе Точки)
        customer_code = settings.TOCHKA_CUSTOMER_CODE
        
        # Формируем payload согласно документации Точки
        # ВАЖНО: Все данные должны быть внутри объекта "Data"
        # Примечание: webhookUrl здесь НЕ указывается - вебхуки настраиваются отдельно через Create Webhook API
        payload = {
            "Data": {
                "customerCode": customer_code,  # Код клиента в системе Точки (константа)
                "amount": str(int(amount)),  # Сумма в рублях (строка!)
                "purpose": description,  # Назначение платежа
                "consumerId": user_uuid,  # UUID пользователя
                "paymentMode": payment_mode,  # Способы оплаты: card, sbp, tinkoff, dolyame
                "redirectUrl": return_url,  # URL для редиректа после оплаты
                "ttl": 5  # Время действия ссылки в минутах (5 минут)
            }
        }
        
        # Добавляем merchantId если указан (опционально)
        if settings.TOCHKA_MERCHANT_ID:
            payload["Data"]["merchantId"] = settings.TOCHKA_MERCHANT_ID
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/acquiring/{self.api_version}/payments"
                headers = self._get_headers()
                
                logger.info("=" * 80)
                logger.info("ЗАПРОС К API ТОЧКИ:")
                logger.info(f"URL: {url}")
                logger.info(f"Метод: POST")
                logger.info(f"Заголовки: {headers}")
                logger.info(f"Тело запроса: {payload}")
                logger.info("=" * 80)
                
                response = await client.post(url, headers=headers, json=payload)
                
                logger.info("=" * 80)
                logger.info("ОТВЕТ ОТ API ТОЧКИ:")
                logger.info(f"Статус: {response.status_code}")
                logger.info(f"Заголовки ответа: {dict(response.headers)}")
                logger.info(f"Тело ответа: {response.text}")
                logger.info("=" * 80)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.info(f"✓ Платёжная ссылка создана успешно")
                    logger.info(f"Полный ответ: {data}")
                    
                    # Извлекаем данные из объекта "Data"
                    payment_data = data.get('Data', {})
                    
                    return {
                        'payment_link_id': payment_data.get('paymentLinkId', 'unknown'),
                        'payment_url': payment_data.get('paymentLink', ''),
                        'operation_id': payment_data.get('operationId', ''),
                        'status': payment_data.get('status', 'new')
                    }
                else:
                    error_text = response.text
                    logger.error(f"✗ Ошибка API Точки [{response.status_code}]: {error_text}")
                    raise Exception(f"Ошибка создания платёжной ссылки: {error_text}")
                    
        except httpx.TimeoutException:
            logger.error("Таймаут при обращении к API Точки")
            raise Exception("Таймаут при создании платёжной ссылки. Попробуйте позже.")
        except httpx.RequestError as e:
            logger.error(f"Ошибка соединения с API Точки: {e}")
            raise Exception("Ошибка соединения с платёжной системой")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании платёжной ссылки: {e}")
            raise
    
    async def get_payment_status(self, operation_id: str) -> dict:
        """
        Проверка статуса платёжной операции
        
        Args:
            operation_id: UUID операции от Точки (operationId)
        
        Returns:
            {
                'status': 'CREATED|PAID|EXPIRED|CANCELLED',
                'amount': '1000.00',
                'paid_at': '2024-01-01T12:00:00',
                'receipt_url': 'https://...'
            }
        
        Статусы:
            - CREATED: новая операция, ожидает оплаты
            - PAID: оплачена
            - EXPIRED: истекла
            - CANCELLED: отменена
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/acquiring/{self.api_version}/payments/{operation_id}"
                headers = self._get_headers()
                
                logger.info("=" * 80)
                logger.info("ЗАПРОС К API ТОЧКИ (проверка статуса):")
                logger.info(f"URL: {url}")
                logger.info(f"Метод: GET")
                logger.info(f"Заголовки: {headers}")
                logger.info("=" * 80)
                
                response = await client.get(url, headers=headers)
                
                logger.info("=" * 80)
                logger.info("ОТВЕТ ОТ API ТОЧКИ (проверка статуса):")
                logger.info(f"Статус: {response.status_code}")
                logger.info(f"Заголовки ответа: {dict(response.headers)}")
                logger.info(f"Тело ответа: {response.text}")
                logger.info("=" * 80)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    logger.info(f"✓ Статус платёжной операции {operation_id}")
                    logger.info(f"Полный ответ: {data}")
                    
                    # Извлекаем данные из объекта "Data"
                    payment_data = data.get('Data', {})
                    
                    return {
                        'status': payment_data.get('status', 'unknown'),
                        'amount': str(payment_data.get('amount', 0)),
                        'paid_at': payment_data.get('paidAt'),
                        'receipt_url': payment_data.get('receiptUrl', payment_data.get('receiptURL'))
                    }
                else:
                    error_text = response.text
                    logger.error(f"✗ Ошибка получения статуса [{response.status_code}]: {error_text}")
                    raise Exception(f"Ошибка получения статуса платежа: {error_text}")
                    
        except httpx.TimeoutException:
            logger.error("Таймаут при проверке статуса платежа")
            raise Exception("Таймаут при проверке статуса. Попробуйте позже.")
        except Exception as e:
            logger.error(f"Ошибка при получении статуса платежа: {e}")
            raise
    
    async def cancel_payment_link(self, operation_id: str) -> bool:
        """
        Отмена платёжной операции
        
        Args:
            operation_id: UUID операции от Точки (operationId)
        
        Returns:
            True если отменена успешно, False в противном случае
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/acquiring/{self.api_version}/payments/{operation_id}/cancel"
                headers = self._get_headers()
                
                logger.info("=" * 80)
                logger.info("ЗАПРОС К API ТОЧКИ (отмена платежа):")
                logger.info(f"URL: {url}")
                logger.info(f"Метод: DELETE")
                logger.info(f"Заголовки: {headers}")
                logger.info("=" * 80)
                
                response = await client.delete(url, headers=headers)
                
                logger.info("=" * 80)
                logger.info("ОТВЕТ ОТ API ТОЧКИ (отмена платежа):")
                logger.info(f"Статус: {response.status_code}")
                logger.info(f"Заголовки ответа: {dict(response.headers)}")
                logger.info(f"Тело ответа: {response.text}")
                logger.info("=" * 80)
                
                success = response.status_code in [200, 204]
                
                if success:
                    logger.info(f"✓ Платёжная операция {operation_id} успешно отменена")
                else:
                    logger.warning(f"✗ Не удалось отменить платёжную операцию {operation_id}: {response.status_code}")
                
                return success
                
        except Exception as e:
            logger.error(f"Ошибка при отмене платёжной ссылки: {e}")
            return False
