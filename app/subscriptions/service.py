"""
Сервис бизнес-логики для работы с подписками
"""

from datetime import datetime, timedelta
from typing import Optional
import logging

from app.subscriptions.dao import SubscriptionDAO, PaymentDAO, SubscriptionPlanDAO
from app.users.dao import UsersDAO
from app.payments.tochka_service import TochkaPaymentService

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Сервис для управления подписками пользователей"""
    
    @staticmethod
    async def create_trial_subscription(user_id: int) -> dict:
        """
        Создание триальной подписки на 2 недели при регистрации
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Словарь с данными созданной подписки
        
        Raises:
            Exception: Если триальный период уже использован
        """
        user = await UsersDAO.find_one_or_none_by_id(user_id)
        
        if not user:
            raise Exception("Пользователь не найден")
        
        if user.trial_used:
            raise Exception("Триальный период уже использован")
        
        # Создаем подписку на 14 дней
        started_at = datetime.utcnow()
        expires_at = started_at + timedelta(days=14)
        
        logger.info(f"Создание триальной подписки для пользователя {user_id} до {expires_at}")
        
        subscription_data = {
            'user_id': user_id,
            'plan_id': None,  # У триала нет плана
            'payment_id': None,  # У триала нет платежа
            'started_at': started_at,
            'expires_at': expires_at,
            'is_trial': True,
            'auto_renew': False
        }
        
        subscription_uuid = await SubscriptionDAO.add(**subscription_data)
        
        # Обновляем пользователя
        await UsersDAO.update(
            user.uuid,
            subscription_status='active',
            subscription_until=expires_at.date(),
            trial_used=True,
            trial_started_at=started_at
        )
        
        logger.info(f"Триальная подписка успешно создана для пользователя {user_id}")
        
        return {
            'subscription_uuid': str(subscription_uuid),
            'started_at': started_at,
            'expires_at': expires_at,
            'is_trial': True
        }
    
    @staticmethod
    async def initiate_payment(
        user_id: int,
        plan_uuid: str,
        return_url: Optional[str] = None,
        payment_mode: Optional[list] = None
    ) -> dict:
        """
        Инициация платежа - создание платёжной ссылки
        
        Args:
            user_id: ID пользователя
            plan_uuid: UUID тарифного плана
            return_url: URL для возврата после оплаты (опционально)
            payment_mode: Способы оплаты ['card', 'sbp', 'tinkoff', 'dolyame'] (опционально)
        
        Returns:
            {
                'payment_uuid': 'xxx',
                'payment_url': 'https://...',
                'payment_link_id': 'xxx'
            }
        
        Raises:
            Exception: При ошибке создания платежа
        """
        user = await UsersDAO.find_one_or_none_by_id(user_id)
        plan = await SubscriptionPlanDAO.find_full_data(plan_uuid)
        
        if not user:
            raise Exception("Пользователь не найден")
        
        if not plan or not plan.is_active:
            raise Exception("Тарифный план недоступен")
        
        logger.info(f"Инициация платежа для пользователя {user_id}, план {plan.name}")
        
        # Создаем запись о платеже в БД
        payment_data = {
            'user_id': user_id,
            'plan_id': plan.id,
            'amount': float(plan.price),
            'status': 'pending'
        }
        
        payment_uuid = await PaymentDAO.add(**payment_data)
        payment = await PaymentDAO.find_full_data(payment_uuid)
        
        # URL для возврата по умолчанию (deep link в приложение)
        if not return_url:
            return_url = f"myapp://payment/callback?payment_uuid={payment_uuid}"
        
        # Создаем платёжную ссылку в Точке
        tochka = TochkaPaymentService()
        
        # Способы оплаты по умолчанию или переданные
        if not payment_mode:
            payment_mode = ["card", "sbp"]
        
        try:
            payment_info = await tochka.create_payment_link(
                amount=float(plan.price),
                description=f"Подписка NinjaTraining: {plan.name}",
                user_id=user.id,
                user_uuid=str(user.uuid),
                user_email=user.email,
                user_phone=user.phone_number,
                return_url=return_url,
                payment_uuid=str(payment_uuid),
                payment_mode=payment_mode
            )
            
            # Обновляем платеж данными от Точки
            await PaymentDAO.update(
                payment_uuid,
                payment_id=payment_info['payment_link_id'],
                operation_id=payment_info.get('operation_id'),
                payment_url=payment_info['payment_url'],
                status='processing'
            )
            
            logger.info(f"Платёжная ссылка создана для пользователя {user_id}: {payment_info['payment_link_id']}")
            
            return {
                'payment_uuid': str(payment_uuid),
                'payment_url': payment_info['payment_url'],
                'payment_link_id': payment_info['payment_link_id'],
                'operation_id': payment_info.get('operation_id')
            }
            
        except Exception as e:
            # В случае ошибки помечаем платеж как failed
            await PaymentDAO.update(
                payment_uuid,
                status='failed',
                error_message=str(e)
            )
            logger.error(f"Ошибка создания платёжной ссылки для пользователя {user_id}: {e}")
            raise Exception(f"Не удалось создать платёжную ссылку: {str(e)}")
    
    @staticmethod
    async def process_webhook(webhook_data: dict):
        """
        Обработка вебхука от Точки о статусе платежа
        
        Документация: https://developers.tochka.com/docs/tochka-api/opisanie-metodov/vebkhuki
        
        Args:
            webhook_data: Данные из вебхука
        """
        logger.info(f"Получен вебхук от Точки: {webhook_data}")
        
        try:
            # Извлекаем данные из вебхука
            event_type = webhook_data.get('eventType')
            payment_data = webhook_data.get('Data', {})
            
            payment_link_id = payment_data.get('paymentLinkId')
            status = payment_data.get('status')  # new, paid, expired, cancelled
            metadata = payment_data.get('metadata', {})
            payment_uuid = metadata.get('payment_uuid')
            
            logger.info(f"Вебхук: payment_link_id={payment_link_id}, status={status}, payment_uuid={payment_uuid}")
            
            if not payment_uuid:
                logger.warning("Вебхук не содержит payment_uuid в metadata")
                return
            
            # Находим платеж в БД
            payment = await PaymentDAO.find_full_data(payment_uuid)
            
            if not payment:
                logger.error(f"Платеж {payment_uuid} не найден в БД")
                return
            
            # Обрабатываем статус (Точка возвращает статусы в верхнем регистре)
            status_upper = status.upper() if status else ''
            
            if status_upper == 'PAID':
                logger.info(f"Платеж {payment_uuid} оплачен, активируем подписку")
                
                # Сохраняем URL чека
                receipt_url = payment_data.get('receiptUrl')
                await PaymentDAO.update(
                    payment_uuid,
                    status='succeeded',
                    paid_at=datetime.utcnow(),
                    receipt_url=receipt_url
                )
                
                # Активируем подписку
                await SubscriptionService.process_successful_payment(payment_uuid)
                
            elif status_upper == 'EXPIRED':
                logger.info(f"Срок действия платёжной ссылки {payment_uuid} истек")
                await PaymentDAO.update(
                    payment_uuid,
                    status='failed',
                    error_message='Истек срок действия платёжной ссылки'
                )
                
            elif status_upper == 'CANCELLED':
                logger.info(f"Платеж {payment_uuid} отменен")
                await PaymentDAO.update(
                    payment_uuid,
                    status='cancelled',
                    error_message='Платеж отменен пользователем'
                )
            
            logger.info(f"Вебхук успешно обработан для платежа {payment_uuid}")
            
        except Exception as e:
            logger.error(f"Ошибка обработки вебхука: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def process_successful_payment(payment_uuid: str):
        """
        Обработка успешного платежа - активация/продление подписки
        
        Args:
            payment_uuid: UUID платежа
        """
        payment = await PaymentDAO.find_full_data(payment_uuid)
        
        if not payment:
            raise Exception(f"Платеж {payment_uuid} не найден")
        
        if payment.status == 'succeeded':
            logger.info(f"Платеж {payment_uuid} уже обработан")
            return
        
        plan = await SubscriptionPlanDAO.find_one_or_none_by_id(payment.plan_id)
        user = await UsersDAO.find_one_or_none_by_id(payment.user_id)
        
        if not plan or not user:
            raise Exception("План или пользователь не найден")
        
        logger.info(f"Обработка успешного платежа {payment_uuid} для пользователя {user.id}")
        
        # Вычисляем даты подписки
        now = datetime.utcnow()
        current_end = user.subscription_until
        
        # Если подписка активна, продлеваем от даты окончания
        if current_end and current_end > now.date():
            started_at = datetime.combine(current_end, datetime.min.time()) + timedelta(days=1)
            logger.info(f"Продление существующей подписки с {current_end}")
        else:
            started_at = now
            logger.info("Активация новой подписки")
        
        # Рассчитываем дату окончания (30 дней * количество месяцев)
        expires_at = started_at + timedelta(days=30 * plan.duration_months)
        
        # Создаем запись подписки
        subscription_data = {
            'user_id': payment.user_id,
            'plan_id': payment.plan_id,
            'payment_id': payment.id,
            'started_at': started_at,
            'expires_at': expires_at,
            'is_trial': False,
            'auto_renew': False
        }
        
        await SubscriptionDAO.add(**subscription_data)
        
        # Обновляем пользователя
        await UsersDAO.update(
            user.uuid,
            subscription_status='active',
            subscription_until=expires_at.date()
        )
        
        logger.info(f"Подписка активирована для пользователя {user.id} до {expires_at}")
    
    @staticmethod
    async def check_and_update_expired_subscriptions():
        """
        Фоновая задача: проверка и деактивация истекших подписок
        
        Эту функцию можно вызывать по расписанию (например, через cron или Celery)
        """
        logger.info("Проверка истекших подписок...")
        
        # Находим всех пользователей с активной подпиской
        users = await UsersDAO.find_all(subscription_status='active')
        
        expired_count = 0
        now = datetime.utcnow().date()
        
        for user in users:
            if user.subscription_until and user.subscription_until < now:
                # Подписка истекла
                logger.info(f"Подписка пользователя {user.id} истекла {user.subscription_until}")
                
                await UsersDAO.update(
                    user.uuid,
                    subscription_status='expired'
                )
                
                expired_count += 1
        
        logger.info(f"Деактивировано подписок: {expired_count}")
        
        return expired_count
